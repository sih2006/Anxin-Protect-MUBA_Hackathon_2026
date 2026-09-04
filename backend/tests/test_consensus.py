"""Consensus rules from the team context doc (section 8).

Boundaries tested at exactly 20/21/40/41 because section 12 names those
numbers -- if a judge or teammate reads the doc and then the tests, the two
must agree.
"""
from __future__ import annotations

import pytest

from app.consensus import (
    AGREEMENT_MAX_DELTA,
    PARTIAL_DISAGREEMENT_MAX_DELTA,
    SINGLE_MODEL_CONFIDENCE_CAP,
    WEAK_EVIDENCE_CONFIDENCE_CAP,
    build_consensus,
)
from app.schemas import ConsensusStatus, EvidenceQuality, RiskBand, Verdict
from tests.conftest import make_verdict

# --- the documented band boundaries ---------------------------------------

def test_bands_match_the_documented_numbers():
    assert AGREEMENT_MAX_DELTA == 20
    assert PARTIAL_DISAGREEMENT_MAX_DELTA == 40


@pytest.mark.parametrize("delta", [0, 10, 20])
def test_delta_up_to_20_is_agreement(delta):
    a = make_verdict(score=50, label="A")
    b = make_verdict(score=50 + delta, label="B")
    assert build_consensus([a, b]).status == ConsensusStatus.agree


@pytest.mark.parametrize("delta", [21, 30, 40])
def test_delta_21_to_40_is_partial_disagreement(delta):
    a = make_verdict(score=50, label="A")
    b = make_verdict(score=50 + delta, label="B")
    assert build_consensus([a, b]).status == ConsensusStatus.partial_disagreement


@pytest.mark.parametrize("delta", [41, 60, 100])
def test_delta_above_40_is_strong_disagreement(delta):
    a = make_verdict(score=0, label="A")
    b = make_verdict(score=min(100, delta), label="B")
    result = build_consensus([a, b])
    assert result.status == ConsensusStatus.strong_disagreement
    assert result.verdict == Verdict.insufficient


def test_partial_disagreement_reduces_confidence():
    a = make_verdict(score=50, confidence=80, label="A")
    b = make_verdict(score=80, confidence=80, label="B")
    assert build_consensus([a, b]).confidence < 80


def test_strong_disagreement_never_looks_confident():
    a = make_verdict(score=5, confidence=90, label="A")
    b = make_verdict(score=95, confidence=90, label="B")
    result = build_consensus([a, b])
    assert result.verdict == Verdict.insufficient
    assert result.confidence < 50


# --- evidence gate ---------------------------------------------------------

@pytest.mark.parametrize("quality", [EvidenceQuality.weak, EvidenceQuality.none])
def test_both_models_weak_evidence_forces_insufficient_and_caps_confidence(quality):
    """The rule that stops a confident-looking score resting on nothing."""
    a = make_verdict(score=90, confidence=95, evidence=quality, label="A")
    b = make_verdict(score=90, confidence=95, evidence=quality, label="B")
    result = build_consensus([a, b])
    assert result.verdict == Verdict.insufficient
    assert result.confidence <= WEAK_EVIDENCE_CONFIDENCE_CAP
    assert "weak or missing evidence" in result.explanation_en


def test_one_model_with_good_evidence_does_not_trigger_the_gate():
    a = make_verdict(score=80, confidence=85, evidence=EvidenceQuality.strong, label="A")
    b = make_verdict(score=80, confidence=85, evidence=EvidenceQuality.none, label="B")
    result = build_consensus([a, b])
    assert result.evidence_quality == EvidenceQuality.strong
    assert result.verdict != Verdict.insufficient


def test_agreement_alone_cannot_beat_the_evidence_gate():
    a = make_verdict(score=88, confidence=99, evidence=EvidenceQuality.none, label="A")
    b = make_verdict(score=88, confidence=99, evidence=EvidenceQuality.none, label="B")
    result = build_consensus([a, b])
    assert result.status == ConsensusStatus.agree  # they DID agree
    assert result.verdict == Verdict.insufficient  # ...on nothing
    assert result.confidence <= WEAK_EVIDENCE_CONFIDENCE_CAP


# --- fraud risk: separate from credibility, and escalates ------------------

def test_fraud_risk_escalates_never_averages_down():
    """A scam one model missed must still be flagged."""
    a = make_verdict(score=70, fraud_risk=90, label="A")
    b = make_verdict(score=75, fraud_risk=10, label="B")
    result = build_consensus([a, b])
    assert result.fraud_risk_score == 90
    assert result.risk_band == RiskBand.high


def test_plausible_claim_can_still_be_high_risk():
    """Credibility and fraud risk are different questions (context doc 8)."""
    a = make_verdict(score=85, fraud_risk=88, evidence=EvidenceQuality.strong, label="A")
    b = make_verdict(score=85, fraud_risk=85, evidence=EvidenceQuality.strong, label="B")
    result = build_consensus([a, b])
    assert result.credibility_score == 85
    assert result.verdict == Verdict.high_risk


def test_very_low_credibility_is_high_risk():
    a = make_verdict(score=10, fraud_risk=5, evidence=EvidenceQuality.strong, label="A")
    b = make_verdict(score=15, fraud_risk=5, evidence=EvidenceQuality.strong, label="B")
    assert build_consensus([a, b]).verdict == Verdict.high_risk


def test_well_evidenced_agreement_is_credible():
    a = make_verdict(score=88, fraud_risk=3, evidence=EvidenceQuality.strong, label="A")
    b = make_verdict(score=85, fraud_risk=4, evidence=EvidenceQuality.strong, label="B")
    assert build_consensus([a, b]).verdict == Verdict.credible


def test_mixed_evidence_is_questionable_not_credible():
    a = make_verdict(score=80, evidence=EvidenceQuality.mixed, label="A")
    b = make_verdict(score=80, evidence=EvidenceQuality.mixed, label="B")
    assert build_consensus([a, b]).verdict == Verdict.questionable


# --- fraud signals ---------------------------------------------------------

def test_signals_are_merged_deduplicated_and_capped_at_three():
    a = make_verdict(score=20, fraud_risk=80, label="A",
                     signals_en=["Urgency", "Asks for gift cards", "urgency"])
    b = make_verdict(score=25, fraud_risk=80, label="B",
                     signals_en=["Impersonates a bank", "Threatens account closure"])
    signals = build_consensus([a, b]).fraud_signals_en
    assert len(signals) == 3
    assert len({s.lower() for s in signals}) == 3  # no duplicates


def test_no_signals_when_models_report_none():
    a = make_verdict(score=85, evidence=EvidenceQuality.strong, label="A")
    b = make_verdict(score=85, evidence=EvidenceQuality.strong, label="B")
    assert build_consensus([a, b]).fraud_signals_en == []


# --- single model ----------------------------------------------------------

def test_single_model_caps_confidence():
    result = build_consensus([make_verdict(score=90, confidence=95)])
    assert result.status == ConsensusStatus.single_model_only
    assert result.confidence <= SINGLE_MODEL_CONFIDENCE_CAP


def test_single_model_with_no_evidence_is_capped_twice():
    result = build_consensus([make_verdict(score=90, confidence=99, evidence=EvidenceQuality.none)])
    assert result.confidence <= WEAK_EVIDENCE_CONFIDENCE_CAP
    assert result.verdict == Verdict.insufficient


def test_empty_verdicts_raises():
    with pytest.raises(ValueError):
        build_consensus([])


# --- how the evidence gate and the fraud rule interact ---------------------
# These encode a real judgement call: a phishing SMS has no retrievable
# evidence by nature, so an evidence-first ordering would report the most
# dangerous messages we ever see as merely "Insufficient evidence".

def test_scam_with_no_evidence_is_still_high_risk_not_insufficient():
    a = make_verdict(score=15, fraud_risk=90, confidence=88, evidence=EvidenceQuality.none, label="A")
    b = make_verdict(score=20, fraud_risk=85, confidence=85, evidence=EvidenceQuality.none, label="B")
    result = build_consensus([a, b])
    assert result.verdict == Verdict.high_risk
    assert result.risk_band == RiskBand.high
    # and the warning is not muffled by the evidence cap
    assert result.confidence > WEAK_EVIDENCE_CONFIDENCE_CAP


def test_ordinary_claim_with_no_evidence_is_still_insufficient():
    """The gate must keep working for everything that isn't a scam."""
    a = make_verdict(score=80, fraud_risk=5, confidence=90, evidence=EvidenceQuality.none, label="A")
    b = make_verdict(score=80, fraud_risk=5, confidence=90, evidence=EvidenceQuality.none, label="B")
    result = build_consensus([a, b])
    assert result.verdict == Verdict.insufficient
    assert result.confidence <= WEAK_EVIDENCE_CONFIDENCE_CAP


def test_strong_disagreement_is_not_turned_into_high_risk_by_averaging():
    """0 and 41 average to 20, which looks like 'very low credibility' -- but
    the models disagree by 41 points, so that average is not a number we are
    entitled to act on."""
    a = make_verdict(score=0, fraud_risk=5, label="A")
    b = make_verdict(score=41, fraud_risk=5, label="B")
    assert build_consensus([a, b]).verdict == Verdict.insufficient


def test_but_a_fraud_signal_still_wins_over_disagreement():
    """If one model spots a scam, disagreement about credibility must not
    bury the warning."""
    a = make_verdict(score=0, fraud_risk=92, label="A")
    b = make_verdict(score=60, fraud_risk=20, label="B")
    assert build_consensus([a, b]).verdict == Verdict.high_risk


# --- the DeepSeek-saturation scenario -------------------------------------
# Gonka confirmed (2 Sep 2026) that DeepSeek-V4-Flash is sustainedly
# saturated and that their default failover re-routes overflow to MiniMax.
# With X-Gonka-No-Fallback set we opt into real 429s on that leg instead, so
# a single-model result is an ORDINARY outcome we will hit on stage -- not an
# edge case. Their mentor's warning was explicit: do not proceed on the one
# model that answered while still presenting it as cross-verified.

def test_single_model_does_not_report_credible():
    """One model saying "credible" is not a cross-verified credible verdict."""
    result = build_consensus([
        make_verdict(score=90, confidence=95, fraud_risk=4, evidence=EvidenceQuality.strong)
    ])
    assert result.status == ConsensusStatus.single_model_only
    assert result.verdict == Verdict.insufficient, "a lone model must not yield a credible verdict"
    assert result.confidence <= SINGLE_MODEL_CONFIDENCE_CAP


def test_single_model_does_not_report_questionable_either():
    result = build_consensus([
        make_verdict(score=50, confidence=80, fraud_risk=20, evidence=EvidenceQuality.mixed)
    ])
    assert result.verdict == Verdict.insufficient


def test_but_a_lone_model_can_still_raise_a_scam_warning():
    """The one exception, for the same reason the evidence gate has one: a
    scam pattern one model saw is still a scam, and muting the warning to
    protect methodological purity would harm the person we exist to protect."""
    result = build_consensus([
        make_verdict(score=12, confidence=88, fraud_risk=93, evidence=EvidenceQuality.none,
                     signals_en=["Asks for gift card codes"])
    ])
    assert result.verdict == Verdict.high_risk
    assert result.risk_band == RiskBand.high
    assert result.fraud_signals_en == ["Asks for gift card codes"]


def test_single_model_explanation_says_it_was_not_cross_verified():
    """The words matter as much as the verdict -- this text is what a judge
    reads if the DeepSeek leg 429s during the live demo."""
    result = build_consensus([make_verdict(score=80, label="MiniMax")])
    assert "NOT the cross-model verification" in result.explanation_en
    assert "MiniMax" in result.explanation_en
    assert "交叉验证" in result.explanation_zh or "跨模型" in result.explanation_zh
