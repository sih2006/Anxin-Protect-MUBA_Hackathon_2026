"""QA-04-adjacent backend smoke test: the FastAPI app itself, end to end,
in mock mode -- exercises routers + exception handling, still with zero
live network dependency (see the autouse evidence stub below)."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GONKA_MOCK_MODE", "true")
os.environ.setdefault("GONKA_API_KEY", "")

import app.verifier as verifier_module  # noqa: E402
from app import main as main_module  # noqa: E402


@pytest.fixture(autouse=True)
def no_real_network_evidence(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(verifier_module, "web_search", lambda query, max_results=3: [])


@pytest.fixture
def client() -> TestClient:
    # raise_server_exceptions=False so we exercise the real HTTP response the
    # unhandled_exception_handler produces, instead of pytest re-raising it.
    return TestClient(main_module.app, raise_server_exceptions=False)


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["gonka_mock_mode"] is True


def test_verify_happy_path(client: TestClient):
    resp = client.post("/api/verify", json={"input_mode": "text", "content": "The sky is blue during a clear day."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "2.0"
    assert len(body["model_verdicts"]) == 2
    assert "credibility_score" in body["consensus"]
    assert "fraud_risk_score" in body["consensus"]


def test_verify_rejects_empty_content(client: TestClient):
    resp = client.post("/api/verify", json={"input_mode": "text", "content": ""})
    assert resp.status_code == 422


def test_verify_rejects_oversized_content(client: TestClient):
    resp = client.post("/api/verify", json={"input_mode": "text", "content": "a" * 100_000})
    assert resp.status_code == 422


def test_verify_rejects_invalid_url(client: TestClient):
    resp = client.post("/api/verify", json={"input_mode": "url", "content": "not-a-url"})
    assert resp.status_code == 422


def test_unhandled_error_never_leaks_stack_trace(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def boom(*args, **kwargs):
        raise RuntimeError("some internal secret detail")

    monkeypatch.setattr("app.routers.verify.run_verification", boom)
    resp = client.post("/api/verify", json={"input_mode": "text", "content": "hello"})
    assert resp.status_code == 500
    assert "some internal secret detail" not in resp.text
    assert "Traceback" not in resp.text


def test_both_localhost_spellings_are_allowed_by_default():
    """A browser treats http://localhost:3000 and http://127.0.0.1:3000 as
    different origins. Allowing only one means the app breaks depending on
    which URL the user typed -- with an opaque 'could not reach server'."""
    from app.config import Settings

    origins = Settings(GONKA_API_KEY="", GONKA_MOCK_MODE=True).cors_origins
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins


def test_cors_preflight_succeeds_for_the_frontend_origin(client: TestClient):
    resp = client.options(
        "/api/verify",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200, "CORS preflight must succeed or the browser never sends the POST"
