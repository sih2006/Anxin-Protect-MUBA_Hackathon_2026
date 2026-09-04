"""QA-02: deterministic integration tests with Gonka calls mocked out --
no live credits or network availability required in CI."""
from __future__ import annotations

import pytest

import app.verifier as verifier_module
from app.config import Settings
from app.evidence import FetchedPage
from app.schemas import InputMode, VerifyRequest
from app.verifier import run_verification


@pytest.fixture
def settings() -> Settings:
    # gonka_mock_mode=True (the default) means GonkaClient never touches the
    # network -- see GonkaClient._mock_response.
    return Settings(GONKA_API_KEY="", GONKA_MOCK_MODE=True)


@pytest.fixture(autouse=True)
def no_real_network_evidence(monkeypatch: pytest.MonkeyPatch):
    """QA-02: CI must not depend on live network availability. Evidence
    retrieval (DuckDuckGo web search) is independent of GONKA_MOCK_MODE, so
    it is stubbed here with a fixed, realistic fake result."""
    monkeypatch.setattr(
        verifier_module,
        "web_search",
        lambda query, max_results=3: [
            FetchedPage(url="https://example.com/fact-check", title="Example fact-check article",
                        text="A neutral third-party summary of the claim, for test purposes."),
        ],
    )


@pytest.mark.asyncio
async def test_run_verification_normal_claim_end_to_end(settings: Settings):
    req = VerifyRequest(input_mode=InputMode.text, content="The Eiffel Tower is in Paris, France.")
    report = await run_verification(req, settings)
    assert len(report.model_verdicts) == 2
    assert 0 <= report.consensus.credibility_score <= 100
    assert report.consensus.explanation_en
    assert report.consensus.explanation_zh
    assert report.next_actions


@pytest.mark.asyncio
async def test_run_verification_scam_pattern_flags_high_risk(settings: Settings):
    req = VerifyRequest(
        input_mode=InputMode.text,
        content="URGENT: verify your account now or it will be suspended. Send gift card codes immediately.",
    )
    report = await run_verification(req, settings)
    assert report.consensus.risk_band.value in ("high", "medium")
    assert any("click links" in a.en.lower() or "gift card" in a.en.lower() for a in report.next_actions)


@pytest.mark.asyncio
async def test_run_verification_populates_gonka_transparency_metadata(settings: Settings):
    req = VerifyRequest(input_mode=InputMode.text, content="Water boils at 100 degrees Celsius at sea level.")
    report = await run_verification(req, settings)
    for verdict in report.model_verdicts:
        assert verdict.meta.request_id is not None
        assert verdict.meta.status == "mocked"


@pytest.mark.asyncio
async def test_run_verification_rejects_absurdly_long_input_is_caller_responsibility(settings: Settings):
    # Length validation lives in the router layer (VER-01); the pipeline
    # itself should still not crash on a large-but-schema-valid input.
    req = VerifyRequest(input_mode=InputMode.text, content="a" * 3900)
    report = await run_verification(req, settings)
    assert report.report_id.startswith("anx-")
