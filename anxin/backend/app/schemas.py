"""Versioned verification report schema (VER-06, ARC-03).

The frontend TypeScript types in frontend/lib/types.ts are kept hand-in-sync
with this file. If you change a field here, update that file in the same
commit -- see DOC-02.
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "2.0"


class _BaseSchema(BaseModel):
    # Several fields below are legitimately named model_* (e.g. model_label,
    # model_verdicts) -- disable Pydantic's protected-namespace warning for
    # those rather than fighting our own, more descriptive naming.
    model_config = ConfigDict(protected_namespaces=())


class Language(str, Enum):
    en = "en"
    zh = "zh"


class InputMode(str, Enum):
    text = "text"
    url = "url"
    screenshot = "screenshot"


class AnalysisMode(str, Enum):
    fact_check = "fact_check"
    meme = "meme"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class VerifyRequest(_BaseSchema):
    input_mode: InputMode
    analysis_mode: AnalysisMode = AnalysisMode.fact_check
    content: str = Field(..., min_length=1, description="Raw text, a URL, or OCR-extracted+user-edited text.")
    ui_language: Language = Language.en

    @field_validator("content")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content must not be empty")
        return v


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

class ExtractedClaim(_BaseSchema):
    text: str
    claim_type: Literal["factual", "opinion", "unverifiable"] = "factual"


class ClaimExtractionResult(_BaseSchema):
    claims: list[ExtractedClaim]
    raw_input_excerpt: str


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceSource(_BaseSchema):
    url: str
    title: str
    snippet: str
    retrieved_at: datetime
    origin: Literal["submitted_url", "web_search"] = "web_search"


# ---------------------------------------------------------------------------
# Gonka transparency metadata (GON-04)
# ---------------------------------------------------------------------------

class GonkaCallMetadata(_BaseSchema):
    requested_model: str
    actual_model: str | None = None
    model_label: str
    request_id: str | None = None
    devshard_id: str | None = None
    fallback_occurred: bool = False
    fallback_header_raw: str | None = None
    latency_ms: int | None = None
    receipt_url: str | None = None
    status: Literal["ok", "timeout", "rate_limited", "error", "mocked"] = "ok"
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Per-model verdict (VER-06 -- validated strictly)
# ---------------------------------------------------------------------------

class Verdict(str, Enum):
    """The four states defined in the team context doc (section 5).

    credible      -- evidence is strong and the models broadly agree
    questionable  -- evidence is mixed, or the models moderately disagree
    high_risk     -- strong scam signals, or very low credibility
    insufficient  -- evidence is weak/missing, or the models strongly disagree
    """

    credible = "credible"
    questionable = "questionable"
    high_risk = "high_risk"
    insufficient = "insufficient"


class EvidenceQuality(str, Enum):
    """Independent gate representing source strength and coverage.

    Deliberately separate from the scores: content can be well-evidenced and
    still be a scam, or plausible with no retrievable sources at all.
    """

    strong = "strong"
    mixed = "mixed"
    weak = "weak"
    none = "none"


class RiskBand(str, Enum):
    """Display bucket derived from the numeric fraud_risk_score.

    The NUMBER is canonical; this band exists only so the UI can render an
    accessible badge (icon + words + colour, never colour alone).
    """

    low = "low"
    medium = "medium"
    high = "high"


# Band boundaries, in fraud_risk_score points.
RISK_BAND_MEDIUM_MIN = 34
RISK_BAND_HIGH_MIN = 67


def risk_band_for(fraud_risk_score: int) -> RiskBand:
    if fraud_risk_score >= RISK_BAND_HIGH_MIN:
        return RiskBand.high
    if fraud_risk_score >= RISK_BAND_MEDIUM_MIN:
        return RiskBand.medium
    return RiskBand.low


class ModelVerdict(_BaseSchema):
    """One verifier's independent answer, before consensus.

    credibility_score and fraud_risk_score are separate on purpose (context
    doc section 8): a weakly-supported claim is not automatically a scam, and
    a factually plausible message can still carry manipulative payment
    instructions.
    """

    verdict: Verdict
    credibility_score: int = Field(..., ge=0, le=100, description="How strongly evidence supports the claims.")
    fraud_risk_score: int = Field(..., ge=0, le=100, description="How strongly this resembles a scam or manipulation.")
    fraud_signals_en: list[str] = Field(default_factory=list, description="Concrete warning signs, plain English.")
    fraud_signals_zh: list[str] = Field(default_factory=list, description="Same warning signs, Simplified Chinese.")
    evidence_quality: EvidenceQuality
    confidence: int = Field(..., ge=0, le=100)
    reasoning_en: str
    reasoning_zh: str
    cited_source_urls: list[str] = Field(default_factory=list)
    meta: GonkaCallMetadata


# ---------------------------------------------------------------------------
# Consensus (VER-07, VER-08)
# ---------------------------------------------------------------------------

class ConsensusStatus(str, Enum):
    agree = "agree"
    partial_disagreement = "partial_disagreement"
    strong_disagreement = "strong_disagreement"
    single_model_only = "single_model_only"


class ConsensusResult(_BaseSchema):
    status: ConsensusStatus
    verdict: Verdict
    credibility_score: int = Field(..., ge=0, le=100, description="Consensus Truth/credibility score, 0-100.")
    fraud_risk_score: int = Field(..., ge=0, le=100, description="Consensus scam risk, 0-100. Escalates, never averages down.")
    risk_band: RiskBand = Field(..., description="Display bucket derived from fraud_risk_score.")
    evidence_quality: EvidenceQuality = Field(..., description="Better of the two models' assessments.")
    confidence: int = Field(..., ge=0, le=100, description="Model agreement + evidence strength. Capped when evidence is weak.")
    score_delta: int = Field(..., ge=0, le=100, description="Absolute difference between the two credibility scores.")
    fraud_signals_en: list[str] = Field(default_factory=list)
    fraud_signals_zh: list[str] = Field(default_factory=list)
    explanation_en: str
    explanation_zh: str


# ---------------------------------------------------------------------------
# Full report
# ---------------------------------------------------------------------------

class NextAction(_BaseSchema):
    en: str
    zh: str


class VerificationReport(_BaseSchema):
    schema_version: str = SCHEMA_VERSION
    report_id: str
    created_at: datetime
    input_mode: InputMode
    analysis_mode: AnalysisMode
    original_input_excerpt: str
    claims: list[ExtractedClaim]
    evidence: list[EvidenceSource]
    model_verdicts: list[ModelVerdict]
    consensus: ConsensusResult
    limitations_en: list[str]
    limitations_zh: list[str]
    next_actions: list[NextAction]

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)


class MemeExplanation(_BaseSchema):
    schema_version: str = SCHEMA_VERSION
    report_id: str
    created_at: datetime
    literal_meaning_en: str
    literal_meaning_zh: str
    joke_or_reference_en: str
    joke_or_reference_zh: str
    cultural_context_en: str
    cultural_context_zh: str
    safety_notes_en: str
    safety_notes_zh: str
    is_visual_only_limitation: bool
    meta: GonkaCallMetadata


class OcrResult(_BaseSchema):
    extracted_text: str
    detected_languages: list[str]
    warning: str | None = None


class HealthResponse(_BaseSchema):
    status: Literal["ok"]
    gonka_mock_mode: bool
    schema_version: str = SCHEMA_VERSION


class ErrorResponse(_BaseSchema):
    error: str
    detail: str | None = None
