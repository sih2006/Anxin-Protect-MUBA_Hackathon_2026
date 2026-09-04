"""Tolerance for the enum/score improvisation real models produce
(app/verifier.py normalizers). One sloppy label must not cost a verifier."""
from __future__ import annotations

import pytest

from app.schemas import EvidenceQuality, Verdict
from app.verifier import (
    _normalize_evidence_quality,
    _normalize_score,
    _normalize_signals,
    _normalize_verdict,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("credible", Verdict.credible),
        ("TRUE", Verdict.credible),
        ("Mostly True", Verdict.credible),
        ("questionable", Verdict.questionable),
        ("misleading", Verdict.questionable),
        ("partly true", Verdict.questionable),
        ("high_risk", Verdict.high_risk),
        ("high-risk", Verdict.high_risk),
        ("SCAM", Verdict.high_risk),
        ("likely_false", Verdict.high_risk),
        ("insufficient", Verdict.insufficient),
        ("unverifiable", Verdict.insufficient),
        ("insufficient evidence", Verdict.insufficient),
    ],
)
def test_verdict_aliases(raw, expected):
    assert _normalize_verdict(raw) == expected


@pytest.mark.parametrize("raw", ["definitely maybe", "", None, 42])
def test_unrecognized_verdict_still_rejected(raw):
    with pytest.raises(ValueError):
        _normalize_verdict(raw)


@pytest.mark.parametrize(
    "raw,expected",
    [
        (85, 85),
        ("85", 85),
        ("85%", 85),
        (85.4, 85),
        (0.8, 80),      # 0-1 scale
        (1, 100),       # 0-1 scale upper bound
        (150, 100),     # clamped
        (-20, 0),       # clamped
        (0, 0),
    ],
)
def test_score_normalization(raw, expected):
    assert _normalize_score(raw) == expected


def test_missing_score_raises():
    with pytest.raises(ValueError):
        _normalize_score(None)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("strong", EvidenceQuality.strong),
        ("MIXED", EvidenceQuality.mixed),
        ("weak", EvidenceQuality.weak),
        ("none", EvidenceQuality.none),
    ],
)
def test_evidence_quality_normalization(raw, expected):
    assert _normalize_evidence_quality(raw, evidence_count=3) == expected


def test_no_retrieved_evidence_always_means_none():
    """A model must not be able to claim strong evidence when we found none --
    that is the false confidence the evidence gate exists to prevent."""
    assert _normalize_evidence_quality("strong", evidence_count=0) == EvidenceQuality.none


def test_unrecognized_evidence_quality_defaults_to_weak_not_strong():
    """Fail toward caution, never toward confidence."""
    assert _normalize_evidence_quality("banana", evidence_count=2) == EvidenceQuality.weak
    assert _normalize_evidence_quality(None, evidence_count=2) == EvidenceQuality.weak


def test_signals_are_cleaned_and_capped():
    assert _normalize_signals(["  a  ", "", "b", "c", "d"]) == ["a", "b", "c"]
    assert _normalize_signals("not a list") == []
    assert _normalize_signals(None) == []
