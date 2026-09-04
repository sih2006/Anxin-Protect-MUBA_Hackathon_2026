from __future__ import annotations

import pytest

from app.config import Settings
from app.gonka_client import GonkaCallResult
from app.schemas import EvidenceQuality, GonkaCallMetadata, ModelVerdict, Verdict


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(GONKA_MOCK_MODE=True, GONKA_API_KEY="")


def make_verdict(
    *,
    score: int,
    confidence: int = 80,
    fraud_risk: int = 5,
    evidence: EvidenceQuality = EvidenceQuality.strong,
    verdict: Verdict = Verdict.credible,
    label: str = "TestModel",
    signals_en: list[str] | None = None,
    signals_zh: list[str] | None = None,
) -> ModelVerdict:
    return ModelVerdict(
        verdict=verdict,
        credibility_score=score,
        fraud_risk_score=fraud_risk,
        fraud_signals_en=signals_en or [],
        fraud_signals_zh=signals_zh or [],
        evidence_quality=evidence,
        confidence=confidence,
        reasoning_en="test reasoning",
        reasoning_zh="测试推理",
        cited_source_urls=[],
        meta=GonkaCallMetadata(
            requested_model="test/model",
            actual_model="test/model",
            model_label=label,
            request_id="req-test-123",
            devshard_id="shard-0",
            fallback_occurred=False,
            status="ok",
        ),
    )


def make_call_result(*, ok: bool = True, status: str = "ok", model_label: str = "TestModel") -> GonkaCallResult:
    return GonkaCallResult(
        ok=ok,
        content="{}" if ok else None,
        requested_model="test/model",
        actual_model="test/model" if ok else None,
        model_label=model_label,
        request_id="req-test-123" if ok else None,
        devshard_id="shard-0" if ok else None,
        fallback_occurred=False,
        fallback_header_raw=None,
        latency_ms=42,
        receipt_url=None,
        status=status,
        error_message=None if ok else "boom",
    )
