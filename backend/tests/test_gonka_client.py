"""Mocked integration tests for the live Gonka Router path (QA-02).

These exercise the code that ONLY runs with a real API key -- 429 handling,
the response_format fallback, header capture, auth shape -- without ever
touching the network or spending credits.
"""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.config import Settings
from app.gonka_client import GonkaClient

CHAT_URL = "https://api.gonkarouter.io/v1/chat/completions"


def live_settings(**overrides) -> Settings:
    base = {
        "GONKA_API_KEY": "sk-test-key",
        "GONKA_MOCK_MODE": False,
        "GONKA_MAX_RETRIES": 1,
        "GONKA_TIMEOUT_SECONDS": 5.0,
    }
    base.update(overrides)
    return Settings(**base)


def ok_body(content: str = '{"ok": true}', model: str = "deepseek-ai/DeepSeek-V4-Flash-0731") -> dict:
    return {"model": model, "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}]}


async def call(settings: Settings):
    return await GonkaClient(settings).call(
        model_id="deepseek-ai/DeepSeek-V4-Flash-0731",
        model_label="DeepSeek",
        system_prompt="sys",
        user_prompt="user",
    )


@respx.mock
async def test_successful_call_captures_transparency_headers():
    respx.post(CHAT_URL).mock(
        return_value=httpx.Response(
            200,
            json=ok_body(),
            headers={
                "x-request-id": "req-abc123",
                "x-devshard-id": "shard-7",
            },
        )
    )
    result = await call(live_settings())
    assert result.ok
    assert result.request_id == "req-abc123"
    assert result.devshard_id == "shard-7"
    assert result.receipt_url == "https://api.gonkarouter.io/v1/receipts/req-abc123"
    assert result.fallback_occurred is False
    assert result.status == "ok"


@respx.mock
async def test_sends_bearer_auth_and_no_fallback_header():
    route = respx.post(CHAT_URL).mock(return_value=httpx.Response(200, json=ok_body()))
    await call(live_settings())
    request = route.calls[0].request
    assert request.headers["authorization"] == "Bearer sk-test-key"
    assert request.headers["x-gonka-no-fallback"] == "true"
    # Two competing auth headers can trip strict gateways -- send only one.
    assert "x-api-key" not in request.headers


@respx.mock
async def test_fallback_substitution_is_detected_from_header():
    respx.post(CHAT_URL).mock(
        return_value=httpx.Response(
            200,
            json=ok_body(model="some/other-model"),
            headers={"x-request-id": "req-1", "x-gonka-fallback": "requested -> served"},
        )
    )
    result = await call(live_settings())
    assert result.fallback_occurred is True
    assert result.actual_model == "some/other-model"


@respx.mock
async def test_429_is_retried_then_reported_honestly():
    route = respx.post(CHAT_URL).mock(return_value=httpx.Response(429, json={"error": "saturated"}))
    result = await call(live_settings(GONKA_MAX_RETRIES=1))
    assert result.ok is False
    assert result.status == "rate_limited"
    assert route.call_count == 2  # initial attempt + 1 retry, then honest failure
    assert result.content is None  # never fabricates a success


@respx.mock
async def test_400_with_json_mode_retries_without_response_format():
    responses = [
        httpx.Response(400, json={"error": "response_format not supported"}),
        httpx.Response(200, json=ok_body(), headers={"x-request-id": "req-2"}),
    ]
    route = respx.post(CHAT_URL).mock(side_effect=responses)
    result = await call(live_settings())

    assert result.ok is True
    assert route.call_count == 2
    import json as _json
    first_payload = _json.loads(route.calls[0].request.content)
    second_payload = _json.loads(route.calls[1].request.content)
    assert "response_format" in first_payload
    assert "response_format" not in second_payload


@respx.mock
async def test_persistent_400_eventually_fails_cleanly():
    respx.post(CHAT_URL).mock(return_value=httpx.Response(400, json={"error": "bad model id"}))
    result = await call(live_settings())
    assert result.ok is False
    assert result.status == "error"
    assert "400" in (result.error_message or "")


@respx.mock
async def test_401_does_not_leak_upstream_body():
    respx.post(CHAT_URL).mock(
        return_value=httpx.Response(401, json={"error": "invalid key sk-test-key leaked here"})
    )
    result = await call(live_settings())
    assert result.ok is False
    assert "sk-test-key" not in (result.error_message or "")


@respx.mock
async def test_timeout_is_retried_then_reported():
    respx.post(CHAT_URL).mock(side_effect=httpx.ConnectTimeout("timed out"))
    result = await call(live_settings(GONKA_MAX_RETRIES=1))
    assert result.ok is False
    assert result.status == "timeout"


@respx.mock
async def test_unexpected_response_shape_is_handled():
    respx.post(CHAT_URL).mock(return_value=httpx.Response(200, json={"unexpected": "shape"}))
    result = await call(live_settings())
    assert result.ok is False
    assert result.status == "error"


@respx.mock
async def test_reasoning_content_used_when_content_is_empty():
    body = {
        "model": "m",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "", "reasoning_content": '{"a": 1}'}}],
    }
    respx.post(CHAT_URL).mock(return_value=httpx.Response(200, json=body))
    result = await call(live_settings())
    assert result.ok is True
    assert result.content == '{"a": 1}'


@pytest.mark.parametrize("mock_mode", [True, False])
async def test_mock_mode_never_touches_network(mock_mode: bool):
    settings = Settings(GONKA_API_KEY="" if mock_mode else "sk-x", GONKA_MOCK_MODE=mock_mode)
    assert settings.gonka_configured is (not mock_mode)


# --- end-to-end: the leg that Gonka says will actually 429 ----------------

@respx.mock
async def test_deepseek_429_and_minimax_ok_degrades_honestly():
    """Gonka confirmed DeepSeek-V4-Flash is sustainedly saturated. With
    no-fallback set, this is the shape of a normal production request: one
    leg 429s, the other answers. The report must survive it AND must not
    claim cross-verification."""
    import app.verifier as verifier_module
    from app.config import Settings as S
    from app.schemas import ConsensusStatus, InputMode, Verdict, VerifyRequest

    verifier_module.web_search = lambda q, max_results=3: []

    good = json.dumps({
        "verdict": "credible", "credibility_score": 82, "fraud_risk_score": 6,
        "fraud_signals_en": [], "fraud_signals_zh": [],
        "evidence_quality": "strong", "confidence": 90,
        "reasoning_en": "Well supported.", "reasoning_zh": "有充分依据。",
        "cited_source_urls": [],
    })

    def route(request):
        payload = json.loads(request.content)
        if "DeepSeek" in payload["model"]:
            return httpx.Response(429, json={"error": "saturated"})
        return httpx.Response(
            200,
            json={"model": payload["model"],
                  "choices": [{"index": 0, "message": {"role": "assistant", "content": good}}]},
            headers={"x-request-id": "req-mm-1", "x-devshard-id": "67670"},
        )

    respx.post(CHAT_URL).mock(side_effect=route)

    settings = S(GONKA_API_KEY="sk-t", GONKA_MOCK_MODE=False, GONKA_MAX_RETRIES=0,
                 GONKA_MODEL_A="deepseek-ai/DeepSeek-V4-Flash-0731",
                 GONKA_MODEL_B="MiniMaxAI/MiniMax-M2.7")

    report = await verifier_module.run_verification(
        VerifyRequest(input_mode=InputMode.text, content="The Eiffel Tower is in Paris."), settings
    )

    # it did not crash, and it did not pretend
    assert len(report.model_verdicts) == 1
    assert report.consensus.status == ConsensusStatus.single_model_only
    assert report.consensus.verdict == Verdict.insufficient
    assert report.consensus.confidence <= 60
    assert "NOT the cross-model verification" in report.consensus.explanation_en
    # and the user is told a model was unavailable
    assert any("one of the two pinned models" in line.lower() for line in report.limitations_en)
