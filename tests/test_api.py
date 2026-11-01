"""Integration tests for the self-hosted LIVE server (app/main.py). Needs: pip install -r requirements-dev.txt"""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app, game_state, limiter  # noqa: E402

TOKEN = "test-admin-token"
ADMIN = {"X-Admin-Token": TOKEN}


@pytest.fixture(autouse=True)
def _configure():
    old = settings.admin_token
    settings.admin_token = TOKEN
    limiter.hits.clear()
    game_state.set_active_mission("mission_1")
    yield
    settings.admin_token = old


@pytest.fixture()
def client():
    with TestClient(app) as c:   # runs the lifespan so the Twitch simulator/parser exist
        yield c


def test_pages_and_static(client):
    assert "ScienceQuest Live" in client.get("/").text
    assert "Audience Prediction Poll" in client.get("/overlay").text
    assert client.get("/static/js/app.js").status_code == 200
    assert client.get("/api/mode").json() == {"mode": "live"}


def test_security_headers(client):
    r = client.get("/")
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"


def test_get_state_is_public_and_hides_answer(client):
    data = client.get("/api/state").json()
    assert len(data["all_missions"]) == 5
    assert data["voting_status"]["correct_option"] is None


@pytest.mark.parametrize("method,path,body", [
    ("post", "/api/parameter", {"param": "energy_ev", "value": 4.0}),
    ("post", "/api/mission/mission_2", None),
    ("post", "/api/voting/start", {"duration_seconds": 30}),
    ("post", "/api/voting/resolve", None),
    ("post", "/api/quark/level", {"level": "EXPLORER"}),
    ("get", "/auth/twitch/login", None),
])
def test_control_endpoints_require_admin(client, method, path, body):
    r = getattr(client, method)(path, **({"json": body} if body else {}))
    assert r.status_code == 401
    r = getattr(client, method)(path, headers={"X-Admin-Token": "wrong"}, **({"json": body} if body else {}))
    assert r.status_code == 401


def test_admin_can_change_parameter_and_bad_values_are_400(client):
    ok = client.post("/api/parameter", json={"param": "energy_ev", "value": 4.0}, headers=ADMIN)
    assert ok.status_code == 200 and ok.json()["current_params"]["energy_ev"] == 4.0
    for value in ("abc", 1e9, None):
        assert client.post("/api/parameter", json={"param": "energy_ev", "value": value}, headers=ADMIN).status_code == 400
    assert client.get("/api/state").status_code == 200      # state was not poisoned


def test_mission_switch_is_post_only(client):
    """The home-page cards used to send GET to this POST-only route (405), so missions never switched."""
    assert client.get("/api/mission/mission_2").status_code == 405
    assert client.post("/api/mission/mission_2", headers=ADMIN).status_code == 200


def test_voting_flow_and_idempotent_scoring(client):
    client.post("/api/voting/start", json={"duration_seconds": 30}, headers=ADMIN)
    correct = game_state.get_mission_def()["default_question"]["correct_option"]
    assert client.post("/api/voting/vote", json={"username": "TestViewer", "option": correct}).status_code == 200
    assert client.post("/api/voting/vote", json={"username": "<b>x</b>", "option": correct}).status_code in (400, 422)
    first = client.post("/api/voting/resolve", headers=ADMIN).json()
    assert first["correct_option"] == correct
    points = client.get("/api/leaderboard").json()["leaderboard"][0]["points"]
    client.post("/api/voting/resolve", headers=ADMIN)       # resolving again must not award again
    assert client.get("/api/leaderboard").json()["leaderboard"][0]["points"] == points


def test_chat_cannot_issue_privileged_commands(client):
    client.post("/api/chat/send", json={"username": "troll", "text": "!mission 3"})
    assert game_state.active_mission_id == "mission_1"
    client.post("/api/chat/send", json={"username": "troll", "text": "!energy nan"})
    assert game_state.mission_params["mission_1"]["energy_ev"] == 3.5


def test_status_hides_config_from_public(client):
    pub = client.get("/api/status").json()
    assert "twitch_redirect_uri" not in pub and "ai_model" not in pub
    assert "twitch_redirect_uri" in client.get("/api/status", headers=ADMIN).json()


def test_oauth_requires_state(client):
    settings.twitch_client_id = "mock_client_id_123"
    loc = client.get("/auth/twitch/login", headers=ADMIN, follow_redirects=False).headers["location"]
    assert "state=" in loc and "whispers" not in loc
    r = client.get("/auth/twitch/callback?code=abc&state=forged")
    assert r.status_code == 400
    assert client.get("/auth/twitch/callback").status_code == 400
    settings.twitch_client_id = ""


def test_ws_rejects_foreign_origin(client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", headers={"origin": "https://evil.example"}):
            pass
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["event"] == "init_state"
