"""
Stateless HTTP API for the public website (deployed on Vercel).

All game logic lives in ``app.solo`` (pure functions). This file is only the HTTP adapter:
request models, error mapping, a body-size cap, rate limiting and response headers.

Static files are NOT served from here: Vercel serves ``public/**`` from its CDN.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app import solo
from app.ai.fallback_knowledge import get_curated_explanation
from app.ai.quark import QuarkCompanion, clean_question
from app.config import settings
from app.game.missions import MISSION_DEFINITIONS
from app.game.validation import ParamError, sanitize_params
from app.ratelimit import RateLimiter

MAX_BODY_BYTES = 8 * 1024
LEVELS = ("EXPLORER", "SCIENTIST", "RESEARCHER")

app = FastAPI(title="ScienceQuest", docs_url=None, redoc_url=None, openapi_url=None)
quark = QuarkCompanion(api_key=settings.openai_api_key, model=settings.openai_model)


# ----------------------------------------------------------------------------- rate limiting
limiter = RateLimiter()


def _client_id(request: Request) -> str:
    # Vercel's edge sets x-forwarded-for; the first entry is the real client.
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def _limit(request: Request, bucket: str, per_minute: int) -> None:
    if not limiter.allow(_client_id(request), bucket, per_minute):
        raise HTTPException(status_code=429, detail="Too many requests, please slow down.")


# ----------------------------------------------------------------------------- middleware
@app.middleware("http")
async def guard(request: Request, call_next):
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            too_big = int(declared) > MAX_BODY_BYTES
        except ValueError:
            too_big = True
        if too_big:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(ParamError)
async def param_error_handler(_request: Request, exc: ParamError):
    return JSONResponse({"detail": str(exc)}, status_code=422)


# ----------------------------------------------------------------------------- models
class ComputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mission_id: str = Field(max_length=32)
    params: Dict[str, Any] = Field(default_factory=dict)


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mission_id: str = Field(max_length=32)
    option: str = Field(max_length=4)


class QuarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mission_id: str = Field(max_length=32)
    params: Dict[str, Any] = Field(default_factory=dict)
    question: Optional[str] = Field(default=None, max_length=500)
    level: str = Field(default="SCIENTIST", max_length=16)


# ----------------------------------------------------------------------------- routes
@app.get("/api/health")
async def health():
    return {"status": "ok", "mode": "solo"}


@app.get("/api/mode")
async def mode():
    return {"mode": "solo"}


@app.get("/api/solo/missions")
async def missions(request: Request):
    _limit(request, "read", 60)
    return solo.catalog()


@app.post("/api/solo/compute")
async def compute(body: ComputeRequest, request: Request):
    _limit(request, "compute", 240)
    return solo.build_state(body.mission_id, body.params)


@app.post("/api/solo/answer")
async def answer(body: AnswerRequest, request: Request):
    _limit(request, "answer", 60)
    return solo.check_answer(body.mission_id, body.option)


@app.post("/api/solo/quark")
async def ask_quark(body: QuarkRequest, request: Request):
    _limit(request, "quark", 20)
    level = body.level.strip().upper()
    if level not in LEVELS:
        raise HTTPException(status_code=422, detail="Invalid level")
    if body.mission_id not in MISSION_DEFINITIONS:
        raise HTTPException(status_code=422, detail="Unknown mission")
    state = solo.build_state(body.mission_id, sanitize_params(body.mission_id, body.params))
    mission = MISSION_DEFINITIONS[body.mission_id]
    question = clean_question(body.question) if body.question else ""

    if question:
        text = await quark.answer_user_question(
            question=question, mission_id=body.mission_id, mission_title=mission["title"],
            current_params=state["current_params"], physics_result=state["physics_result"], level=level)
    else:
        text = await quark.explain_active_experiment(
            mission_id=body.mission_id, mission_title=mission["title"],
            current_params=state["current_params"], physics_result=state["physics_result"], level=level)
    if not text:
        text = get_curated_explanation(body.mission_id, level)
    return {"answer": text, "level": level}
