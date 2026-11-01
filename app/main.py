"""
Live-mode server (self-hosted): REST + WebSocket hub, Twitch chat, Quark AI, OBS overlay.

This needs a long-running process, so it is NOT what runs on Vercel (see ``app/web.py`` for that).
Run it with ``python run.py`` on your own machine or on a host that keeps a process alive
(Railway, Fly.io, Render, a VPS ...).

Security model
--------------
* Control endpoints (change mission/parameters, open/resolve voting, OAuth login) require the admin
  token (``X-Admin-Token``). With no ``ADMIN_TOKEN`` configured they accept direct loopback clients only.
* Audience endpoints (vote, ask Quark, chat) are open but validated and rate limited.
* Chat from the website is never treated as moderator input; only the Twitch channel owner can run
  privileged chat commands (``!mission``, ``!run``, ``!round``).
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, Set
from urllib.parse import quote, urlparse
import asyncio
import hmac
import json
import logging
import pathlib
import re
import secrets
import time

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from app.ai.quark import QuarkCompanion, clean_question
from app.config import settings
from app.game.missions import MISSION_DEFINITIONS
from app.game.scoring import BADGE_METADATA, ScoreManager
from app.game.state import GameStateManager
from app.game.validation import normalize_username
from app.ratelimit import RateLimiter
from app.twitch.client import TwitchService
from app.twitch.parser import PRIVILEGED_ACTIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sciencequest.server")

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "public"

MAX_WS_CONNECTIONS = 300
MAX_WS_MESSAGE_CHARS = 2048
OAUTH_STATE_TTL = 600

game_state = GameStateManager()
score_manager = ScoreManager()
quark = QuarkCompanion(api_key=settings.openai_api_key, model=settings.openai_model)
twitch_service: TwitchService = None
limiter = RateLimiter()
_oauth_states: Dict[str, float] = {}
_param_cooldown_until = 0.0
_background: Set[asyncio.Task] = set()  # keep references so tasks are not garbage collected mid-flight


def spawn(coro) -> None:
    task = asyncio.create_task(coro)
    _background.add(task)
    task.add_done_callback(_background.discard)


# ----------------------------------------------------------------------------- access control
def _is_loopback(request: Request) -> bool:
    # Behind a reverse proxy every request *looks* local, so any forwarding header disables the shortcut.
    if request.headers.get("x-forwarded-for") or request.headers.get("forwarded"):
        return False
    return bool(request.client) and request.client.host in ("127.0.0.1", "::1")


def is_admin(request: Request) -> bool:
    token = settings.admin_token
    if token:
        supplied = request.headers.get("x-admin-token", "")
        return hmac.compare_digest(supplied.encode(), token.encode())
    return _is_loopback(request)


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(status_code=401, detail="Admin token required")


def _client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _limit(request: Request, bucket: str, per_minute: int) -> None:
    if not limiter.allow(_client_id(request), bucket, per_minute):
        raise HTTPException(status_code=429, detail="Too many requests, please slow down.")


# ----------------------------------------------------------------------------- websocket hub
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> bool:
        if len(self.active_connections) >= MAX_WS_CONNECTIONS:
            await websocket.close(code=1013)
            return False
        origin = websocket.headers.get("origin")
        if origin:
            host = urlparse(origin).netloc
            allowed = {websocket.headers.get("host", "")}
            allowed.update(o.strip() for o in settings.allowed_origins.split(",") if o.strip())
            if host not in allowed:
                await websocket.close(code=1008)
                return False
        await websocket.accept()
        self.active_connections.add(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)


ws_manager = ConnectionManager()


# ----------------------------------------------------------------------------- event bridge
def handle_twitch_chat(username: str, text: str, is_simulated: bool):
    spawn(ws_manager.broadcast({
        "event": "chat_message",
        "username": str(username)[:25],
        "text": str(text)[:500],
        "is_simulated": is_simulated,
    }))


def handle_twitch_command(action: Dict[str, Any]):
    """Apply a parsed chat command. Privileged commands need the channel owner."""
    global _param_cooldown_until
    action_type = action.get("type")
    username = action.get("username", "Viewer")

    if action_type in PRIVILEGED_ACTIONS and not action.get("is_mod_or_streamer"):
        return

    if action_type == "vote":
        if game_state.record_vote(username, action.get("option", "")):
            spawn(ws_manager.broadcast({"event": "vote_update", "voting_status": game_state.get_voting_status()}))
    elif action_type == "set_param":
        # Viewers may nudge the experiment, but not faster than once per second for the whole channel.
        now = time.monotonic()
        if not action.get("is_mod_or_streamer") and now < _param_cooldown_until:
            return
        if game_state.update_parameter(action.get("param"), action.get("value")):
            _param_cooldown_until = now + 1.0
            spawn(broadcast_full_state())
    elif action_type == "set_mission":
        if game_state.set_active_mission(action.get("mission_id")):
            spawn(broadcast_full_state())
    elif action_type == "ask_quark":
        spawn(process_quark_question(action.get("question", ""), username))
    elif action_type == "run_experiment":
        if game_state.voting_open:
            spawn(resolve_current_round())
        else:
            game_state.recalculate_current_physics()
            spawn(broadcast_full_state())
    elif action_type == "start_round":
        game_state.start_voting_round(duration_seconds=45)
        spawn(broadcast_full_state())


async def broadcast_full_state():
    await ws_manager.broadcast({"event": "state_update", "state": game_state.get_full_client_state()})


async def process_quark_question(question: str, username: str):
    m_def = game_state.get_mission_def()
    answer = await quark.answer_user_question(
        question=clean_question(question),
        mission_id=game_state.active_mission_id,
        mission_title=m_def["title"],
        current_params=game_state.mission_params[game_state.active_mission_id],
        physics_result=game_state.active_physics_result,
    )
    await ws_manager.broadcast({
        "event": "quark_speech",
        "question": clean_question(question),
        "username": str(username)[:25],
        "answer": answer,
        "level": quark.current_explanation_level,
    })


async def resolve_current_round():
    res = game_state.close_and_resolve_voting()
    m_def = game_state.get_mission_def()
    if not res["already_resolved"]:  # calling resolve twice must not award points twice
        score_manager.record_prediction_round(
            mission_id=game_state.active_mission_id,
            correct_voters=res["correct_voters"],
            incorrect_voters=res["incorrect_voters"],
            badge_awarded_id=m_def.get("badge_id"),
        )
    explanation = await quark.explain_active_experiment(
        mission_id=game_state.active_mission_id,
        mission_title=m_def["title"],
        current_params=game_state.mission_params[game_state.active_mission_id],
        physics_result=game_state.active_physics_result,
    )
    await ws_manager.broadcast({
        "event": "round_resolved",
        "round_result": res,
        "quark_explanation": explanation,
        "leaderboard": score_manager.get_leaderboard(5),
    })
    await broadcast_full_state()


# ----------------------------------------------------------------------------- lifespan / app
@asynccontextmanager
async def lifespan(app: FastAPI):
    global twitch_service
    logger.info("Initializing ScienceQuest live services...")
    if not settings.admin_token:
        logger.warning("ADMIN_TOKEN is not set: control endpoints accept direct loopback clients only.")
    twitch_service = TwitchService(
        channel=settings.twitch_channel,
        bot_nick=settings.twitch_bot_nickname,
        oauth_token=settings.twitch_oauth_token,
        simulation_mode=settings.simulation_mode,
        on_command_callback=handle_twitch_command,
        on_chat_callback=handle_twitch_chat,
    )
    await twitch_service.start()
    yield
    if twitch_service:
        await twitch_service.stop()


app = FastAPI(title="ScienceQuest Live", version="1.1.0", lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' ws: wss:; "
       "object-src 'none'; base-uri 'none'; frame-ancestors 'self'")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Content-Security-Policy", CSP)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR / "static")), name="static")


@app.get("/")
async def get_index():
    return FileResponse(PUBLIC_DIR / "index.html")


@app.get("/overlay")
async def get_overlay():
    return FileResponse(PUBLIC_DIR / "overlay.html")


@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    return FileResponse(PUBLIC_DIR / "favicon.svg")


@app.get("/api/mode")
async def get_mode():
    return {"mode": "live"}


# ----------------------------------------------------------------------------- Twitch OAuth
_STATE_SAFE = re.compile(r"[^a-z_]")


@app.get("/auth/twitch/login", dependencies=[Depends(require_admin)])
async def twitch_login():
    """Send the streamer to Twitch. Admin only; a one-time ``state`` value defends against login CSRF."""
    if not settings.twitch_client_id:
        return JSONResponse(status_code=400, content={
            "error": "TWITCH_CLIENT_ID is not configured in .env.",
            "message": "Register your application in the Twitch Developer Console and set TWITCH_CLIENT_ID "
                       "and TWITCH_CLIENT_SECRET.",
            "configured_redirect_uri": settings.twitch_redirect_uri,
        })
    now = time.time()
    for key in [k for k, t in _oauth_states.items() if now - t > OAUTH_STATE_TTL]:
        _oauth_states.pop(key, None)
    state = secrets.token_urlsafe(24)
    _oauth_states[state] = now
    auth_url = (
        "https://id.twitch.tv/oauth2/authorize"
        f"?client_id={quote(settings.twitch_client_id, safe='')}"
        f"&redirect_uri={quote(settings.twitch_redirect_uri, safe='')}"
        "&response_type=code"
        "&scope=chat:read+chat:edit"  # least privilege: whispers are not used
        f"&state={state}"
        "&force_verify=true"
    )
    return RedirectResponse(auth_url)


@app.get("/auth/twitch/callback")
async def twitch_callback(code: str = Query(None, max_length=256), state: str = Query(None, max_length=128),
                          error: str = Query(None, max_length=64), error_description: str = Query(None, max_length=256)):
    if error:
        logger.error("Twitch OAuth error: %s", _STATE_SAFE.sub("", error.lower()))
        return RedirectResponse(f"/?twitch_error={_STATE_SAFE.sub('', error.lower())[:40]}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing from callback.")
    issued = _oauth_states.pop(state, None) if state else None
    if issued is None or time.time() - issued > OAUTH_STATE_TTL:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")
    if not settings.twitch_client_secret:
        return JSONResponse(status_code=400, content={"error": "TWITCH_CLIENT_SECRET is not configured in .env."})

    payload = {
        "client_id": settings.twitch_client_id,
        "client_secret": settings.twitch_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.twitch_redirect_uri,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://id.twitch.tv/oauth2/token", data=payload)
        if resp.status_code != 200:
            logger.error("Twitch token exchange failed with status %s", resp.status_code)
            return RedirectResponse("/?twitch_error=token_exchange_failed")
        access_token = resp.json().get("access_token")
        settings.twitch_oauth_token = access_token
        settings.simulation_mode = False
        if twitch_service:
            twitch_service.oauth_token = access_token
            twitch_service.simulation_mode = False
            await twitch_service.stop()
            await twitch_service.start()
        logger.info("Authenticated with Twitch via OAuth.")
        return RedirectResponse("/?twitch=authenticated")
    except Exception as exc:
        logger.error("Exception during Twitch token exchange: %s", type(exc).__name__)
        return RedirectResponse("/?twitch_error=exchange_exception")


# ----------------------------------------------------------------------------- REST API
@app.get("/api/state")
async def get_state():
    return game_state.get_full_client_state()


@app.post("/api/mission/{mission_id}", dependencies=[Depends(require_admin)])
async def change_mission(mission_id: str):
    if not game_state.set_active_mission(mission_id):
        raise HTTPException(status_code=400, detail="Invalid mission ID")
    await broadcast_full_state()
    m_def = game_state.get_mission_def()
    intro = await quark.explain_active_experiment(
        mission_id=m_def["id"], mission_title=m_def["title"],
        current_params=game_state.mission_params[m_def["id"]],
        physics_result=game_state.active_physics_result,
    )
    await ws_manager.broadcast({
        "event": "quark_speech", "username": "Quark", "question": f"Starting {m_def['title']}!",
        "answer": intro, "level": quark.current_explanation_level,
    })
    return game_state.get_full_client_state()


class ParameterUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    param: str = Field(max_length=32)
    value: Any


@app.post("/api/parameter", dependencies=[Depends(require_admin)])
async def update_param(data: ParameterUpdate):
    if not game_state.update_parameter(data.param, data.value):
        raise HTTPException(status_code=400, detail="Invalid parameter name or value")
    await broadcast_full_state()
    return {
        "status": "success",
        "current_params": game_state.mission_params[game_state.active_mission_id],
        "physics_result": game_state.active_physics_result,
    }


class VotingStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    duration_seconds: int = Field(default=45, ge=5, le=300)


@app.post("/api/voting/start", dependencies=[Depends(require_admin)])
async def start_voting(data: VotingStartRequest):
    status = game_state.start_voting_round(duration_seconds=data.duration_seconds)
    await ws_manager.broadcast({"event": "voting_started", "voting_status": status})
    return status


class VoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(max_length=25)
    option: str = Field(max_length=4)


@app.post("/api/voting/vote")
async def cast_vote(data: VoteRequest, request: Request):
    _limit(request, "vote", 30)
    if not game_state.record_vote(data.username, data.option):
        raise HTTPException(status_code=400, detail="Voting closed, invalid option or invalid username")
    status = game_state.get_voting_status()
    await ws_manager.broadcast({"event": "vote_update", "voting_status": status})
    return status


@app.post("/api/voting/resolve", dependencies=[Depends(require_admin)])
async def resolve_voting():
    await resolve_current_round()
    return game_state.last_round_result


class AskQuarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(max_length=500)
    username: str = Field(default="Player", max_length=25)
    level: str = Field(default="SCIENTIST", max_length=16)


@app.post("/api/quark/ask")
async def ask_quark_endpoint(data: AskQuarkRequest, request: Request):
    _limit(request, "quark", 10)
    level = data.level.strip().upper()
    if level not in ("EXPLORER", "SCIENTIST", "RESEARCHER"):
        raise HTTPException(status_code=400, detail="Invalid level")
    question = clean_question(data.question)
    m_def = game_state.get_mission_def()
    ans = await quark.answer_user_question(
        question=question, mission_id=game_state.active_mission_id, mission_title=m_def["title"],
        current_params=game_state.mission_params[game_state.active_mission_id],
        physics_result=game_state.active_physics_result, level=level,
    )
    username = normalize_username(data.username) or "player"
    await ws_manager.broadcast({"event": "quark_speech", "question": question, "username": username,
                                "answer": ans, "level": level})
    return {"question": question, "answer": ans, "level": level}


class QuarkLevelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: str = Field(max_length=16)


@app.post("/api/quark/level", dependencies=[Depends(require_admin)])
async def set_quark_level(data: QuarkLevelRequest):
    if not quark.set_explanation_level(data.level):
        raise HTTPException(status_code=400, detail="Invalid level. Choose EXPLORER, SCIENTIST, or RESEARCHER.")
    return {"current_level": quark.current_explanation_level}


@app.get("/api/leaderboard")
async def get_leaderboard():
    return {"leaderboard": score_manager.get_leaderboard(10), "badges": BADGE_METADATA}


@app.get("/api/status")
async def get_service_status(request: Request):
    status = {
        "simulation_mode": settings.simulation_mode,
        "twitch_connected": twitch_service.is_running if twitch_service else False,
        "twitch_live": twitch_service.is_live_configured() if twitch_service else False,
        "ai_enabled": bool(settings.openai_api_key),
        "active_mission": game_state.active_mission_id,
        "explanation_level": quark.current_explanation_level,
    }
    if is_admin(request):  # configuration details are for the streamer only
        status.update({
            "twitch_channel": settings.twitch_channel or "(None - Running in Simulation Mode)",
            "twitch_oauth_configured": bool(settings.twitch_client_id and settings.twitch_client_secret),
            "twitch_redirect_uri": settings.twitch_redirect_uri,
            "twitch_client_id_set": bool(settings.twitch_client_id),
            "ai_model": settings.openai_model,
        })
    return status


class SendChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(max_length=25)
    text: str = Field(max_length=500)


@app.post("/api/chat/send")
async def send_chat(data: SendChatRequest, request: Request):
    """Web chat box. It is audience input: it never carries moderator rights."""
    _limit(request, "chat", 30)
    if normalize_username(data.username) is None:
        raise HTTPException(status_code=400, detail="Invalid username")
    handle_twitch_chat(data.username, data.text, is_simulated=True)
    action = twitch_service.parser.parse_message(data.username, data.text, is_mod_or_streamer=False)
    if action:
        handle_twitch_command(action)
    return {"status": "sent"}


# ----------------------------------------------------------------------------- WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if not await ws_manager.connect(websocket):
        return
    votes_window = []
    try:
        await websocket.send_text(json.dumps({
            "event": "init_state",
            "state": game_state.get_full_client_state(),
            "leaderboard": score_manager.get_leaderboard(5),
        }))
        while True:
            data_text = await websocket.receive_text()
            if len(data_text) > MAX_WS_MESSAGE_CHARS:
                continue
            try:
                data = json.loads(data_text)
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            msg_type = data.get("type")
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
            elif msg_type == "vote":
                now = time.monotonic()
                votes_window = [t for t in votes_window if now - t < 10.0]
                if len(votes_window) >= 10:
                    continue
                votes_window.append(now)
                if game_state.record_vote(data.get("username"), data.get("option")):
                    await ws_manager.broadcast({"event": "vote_update", "voting_status": game_state.get_voting_status()})
            # Parameter changes are deliberately not accepted over the socket: use the admin REST API.
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)
