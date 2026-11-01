"""HTTP tests for the stateless Vercel API (app/web.py). Needs: pip install -r requirements-dev.txt"""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from app.web import app, limiter  # noqa: E402

client = TestClient(app)


def setup_function(_fn):
    limiter.hits.clear()


def test_health_and_mode():
    assert client.get("/api/health").json() == {"status": "ok", "mode": "solo"}
    assert client.get("/api/mode").json() == {"mode": "solo"}


def test_missions_catalog_hides_answers():
    r = client.get("/api/solo/missions")
    assert r.status_code == 200
    assert len(r.json()["missions"]) == 5
    assert "correct_option" not in r.text


def test_compute_returns_validated_state():
    r = client.post("/api/solo/compute", json={"mission_id": "mission_1", "params": {"energy_ev": 4.2}})
    assert r.status_code == 200
    assert r.json()["current_params"]["energy_ev"] == 4.2
    assert r.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("body", [
    {"mission_id": "mission_1", "params": {"energy_ev": "abc"}},
    {"mission_id": "mission_1", "params": {"energy_ev": 1e9}},
    {"mission_id": "mission_1", "params": {"nope": 1}},
    {"mission_id": "mission_99", "params": {}},
    {"mission_id": "mission_1", "params": {}, "extra": 1},
    {"params": {}},
])
def test_compute_rejects_bad_input(body):
    assert client.post("/api/solo/compute", json=body).status_code == 422


def test_compute_rejects_nan_literal():
    r = client.post("/api/solo/compute", content='{"mission_id":"mission_1","params":{"energy_ev":NaN}}',
                    headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_answer_endpoint():
    ok = client.post("/api/solo/answer", json={"mission_id": "mission_1", "option": "B"}).json()
    assert ok["correct"] is True
    assert client.post("/api/solo/answer", json={"mission_id": "mission_1", "option": "Z"}).status_code == 422


def test_quark_offline_answer():
    r = client.post("/api/solo/quark", json={"mission_id": "mission_1", "params": {}, "level": "EXPLORER"})
    assert r.status_code == 200 and len(r.json()["answer"]) > 20
    r = client.post("/api/solo/quark", json={"mission_id": "mission_1", "params": {},
                                             "question": "<img src=x onerror=alert(1)> why?"})
    assert r.status_code == 200
    assert client.post("/api/solo/quark", json={"mission_id": "mission_1", "level": "GOD"}).status_code == 422


def test_oversized_body_rejected():
    big = {"mission_id": "mission_1", "params": {}, "pad": "x" * 20000}
    assert client.post("/api/solo/compute", json=big).status_code == 413


def test_rate_limit_kicks_in():
    codes = [client.post("/api/solo/quark", json={"mission_id": "mission_1", "params": {}}).status_code for _ in range(25)]
    assert 429 in codes and codes[0] == 200


def test_no_docs_or_openapi_exposed():
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404
