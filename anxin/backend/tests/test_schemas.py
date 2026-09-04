from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import EvidenceQuality, ModelVerdict, VerifyRequest
from tests.conftest import make_verdict


def test_truth_score_out_of_range_rejected():
    with pytest.raises(ValidationError):
        make_verdict(score=101)
    with pytest.raises(ValidationError):
        make_verdict(score=-1)


def test_verify_request_rejects_empty_content():
    with pytest.raises(ValidationError):
        VerifyRequest(input_mode="text", content="   ")


def test_verify_request_strips_content():
    req = VerifyRequest(input_mode="text", content="  hello world  ")
    assert req.content == "hello world"


def test_model_verdict_rejects_unknown_verdict_label():
    with pytest.raises(ValidationError):
        ModelVerdict(
            verdict="definitely_true",  # not a valid enum member
            credibility_score=50,
            fraud_risk_score=10,
            evidence_quality=EvidenceQuality.strong,
            confidence=50,
            reasoning_en="x",
            reasoning_zh="x",
            meta={"requested_model": "m", "model_label": "M", "status": "ok"},
        )


def test_fraud_risk_score_out_of_range_rejected():
    with pytest.raises(ValidationError):
        make_verdict(score=50, fraud_risk=101)


def test_risk_band_derives_from_the_numeric_score():
    """The number is canonical; the band is only for display."""
    from app.schemas import RiskBand, risk_band_for

    assert risk_band_for(0) == RiskBand.low
    assert risk_band_for(33) == RiskBand.low
    assert risk_band_for(34) == RiskBand.medium
    assert risk_band_for(66) == RiskBand.medium
    assert risk_band_for(67) == RiskBand.high
    assert risk_band_for(100) == RiskBand.high
