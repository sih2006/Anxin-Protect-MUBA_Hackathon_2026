"""End-to-end verification pipeline orchestration.

Flow (mirrors Epic 3 of the backlog):
  1. validate input (VER-01, in routers/verify.py)
  2. extract atomic claims through Gonka                       (VER-02)
  3. retrieve evidence -- submitted URL and/or web search       (VER-03/04)
  4. prompt both pinned models concurrently, identical evidence  (GON-05, VER-05)
  5. validate each raw model response against ModelVerdict       (VER-06)
  6. build consensus / disagreement result                       (VER-07/08)
  7. attach EN+ZH explanations, sources, limitations, next steps  (VER-09/10)
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import uuid
from datetime import UTC, datetime

from app.config import Settings
from app.consensus import build_consensus, failed_call_summary
from app.evidence import UnsafeUrlError, fetch_url, to_snippet, web_search
from app.gonka_client import GonkaCallResult, GonkaClient
from app.json_utils import JsonExtractionError, extract_json_object
from app.prompts import (
    CLAIM_EXTRACTION_SYSTEM,
    VERIFY_SYSTEM,
    build_claim_extraction_user_prompt,
    build_verify_user_prompt,
)
from app.redaction import redact, redaction_note
from app.schemas import (
    ClaimExtractionResult,
    ConsensusStatus,
    EvidenceQuality,
    EvidenceSource,
    ExtractedClaim,
    InputMode,
    ModelVerdict,
    NextAction,
    RiskBand,
    Verdict,
    VerificationReport,
    VerifyRequest,
)

logger = logging.getLogger("anxin.verifier")

SCAM_KEYWORDS = [
    "urgent", "verify your account", "gift card", "wire transfer", "act now",
    "limited time", "you have won", "claim your prize", "bank details",
    "one-time password", "otp", "click here immediately", "suspended account",
    "紧急", "中奖", "验证您的账户", "礼品卡", "汇款", "点击这里", "账户已被冻结", "限时",
]


class VerificationError(Exception):
    """Raised when neither pinned model returned a usable result."""

    def __init__(self, message: str, failed_calls: list[GonkaCallResult]):
        super().__init__(message)
        self.failed_calls = failed_calls


def _looks_scammy(text: str) -> bool:
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in SCAM_KEYWORDS)


async def extract_claims(client: GonkaClient, settings: Settings, content: str) -> ClaimExtractionResult:
    def mock_gen() -> str:
        sentences = [s.strip() for s in content.replace("\n", " ").split(".") if s.strip()]
        claims = [{"text": s[:200], "claim_type": "factual"} for s in sentences[:3]] or [
            {"text": content[:200], "claim_type": "factual"}
        ]
        return json.dumps({"claims": claims})

    result = await client.call(
        model_id=settings.gonka_model_a,
        model_label=settings.gonka_model_a_label,
        system_prompt=CLAIM_EXTRACTION_SYSTEM,
        user_prompt=build_claim_extraction_user_prompt(content),
        mock_generator=mock_gen,
    )
    if result.ok and result.content:
        try:
            data = extract_json_object(result.content)
            return ClaimExtractionResult(claims=[ExtractedClaim(**c) for c in data.get("claims", [])][:5] or
                                          [ExtractedClaim(text=content[:200], claim_type="factual")],
                                          raw_input_excerpt=content[:300])
        except (JsonExtractionError, TypeError, ValueError):
            logger.warning("claim extraction returned malformed JSON; falling back to raw input as one claim")
    return ClaimExtractionResult(claims=[ExtractedClaim(text=content[:200], claim_type="factual")],
                                  raw_input_excerpt=content[:300])


def gather_evidence(input_mode: InputMode, content: str, claims: ClaimExtractionResult) -> list[EvidenceSource]:
    sources: list[EvidenceSource] = []
    now = datetime.now(UTC)

    if input_mode == InputMode.url:
        try:
            page = fetch_url(content)
            sources.append(EvidenceSource(
                url=page.url, title=page.title, snippet=to_snippet(page.text),
                retrieved_at=now, origin="submitted_url",
            ))
        except UnsafeUrlError as exc:
            logger.info("blocked unsafe URL: %s", exc)
        except Exception as exc:  # noqa: BLE001 -- degrade to "no evidence", never crash the request
            logger.warning("failed to fetch submitted URL: %s", exc.__class__.__name__)

    query = claims.claims[0].text if claims.claims else content
    try:
        for page in web_search(query[:200]):
            sources.append(EvidenceSource(
                url=page.url, title=page.title, snippet=to_snippet(page.text),
                retrieved_at=now, origin="web_search",
            ))
    except Exception as exc:  # noqa: BLE001
        logger.warning("web_search failed: %s", exc.__class__.__name__)

    return sources


def _evidence_block(sources: list[EvidenceSource]) -> str:
    if not sources:
        return ""
    lines = []
    for i, s in enumerate(sources, start=1):
        lines.append(f"[{i}] {s.title}\nURL: {s.url}\nRetrieved: {s.retrieved_at.isoformat()}\nExcerpt: {s.snippet}")
    return "\n\n".join(lines)


def _mock_verdict_json(content: str, model_label: str, jitter_seed: str, has_evidence: bool) -> str:
    """Deterministic-ish mock output so local/dev/demo-rehearsal runs still look
    real without a live Gonka key. A seeded PRNG lets the two mock models differ
    slightly (exercising the disagreement UI) while staying reproducible."""
    # nosec B311 -- deliberately NOT cryptographic. This seeds reproducible
    # mock demo data; it never generates tokens, ids, or anything a security
    # decision depends on.
    rng = random.Random(f"{content}:{jitter_seed}")  # noqa: S311  # nosec B311
    scammy = _looks_scammy(content)

    credibility = rng.randint(10, 30) if scammy else rng.randint(55, 92)
    credibility = max(0, min(100, credibility + rng.randint(-8, 8)))
    fraud_risk = rng.randint(70, 95) if scammy else rng.randint(3, 30)

    if not has_evidence:
        evidence_quality = "none"
    elif scammy:
        evidence_quality = rng.choice(["weak", "mixed"])
    else:
        evidence_quality = rng.choice(["mixed", "strong"])

    if scammy:
        verdict = "high_risk"
        signals_en = [
            "Creates artificial urgency so you act before thinking",
            "Asks for money, codes, or account details",
            "Impersonates a bank or official body",
        ]
        signals_zh = ["制造紧迫感，让您来不及思考", "索要钱款、验证码或账户信息", "冒充银行或官方机构"]
    elif evidence_quality in ("weak", "none"):
        verdict = "insufficient"
        signals_en = ["No independent sources could be found to check this"]
        signals_zh = ["未能找到可核实此内容的独立来源"]
    elif credibility >= 65:
        verdict, signals_en, signals_zh = "credible", [], []
    else:
        verdict = "questionable"
        signals_en = ["Claim is only partly supported by the sources found"]
        signals_zh = ["该说法仅得到部分来源的支持"]

    confidence = rng.randint(70, 92) if scammy else rng.randint(55, 85)
    return json.dumps({
        "verdict": verdict,
        "credibility_score": credibility,
        "fraud_risk_score": fraud_risk,
        "fraud_signals_en": signals_en,
        "fraud_signals_zh": signals_zh,
        "evidence_quality": evidence_quality,
        "confidence": confidence,
        "reasoning_en": (
            f"[MOCK -- no live Gonka Router key configured] Based on the retrieved evidence, this content "
            f"appears {verdict.replace('_', ' ')}. Scam-pattern heuristics "
            f"{'were' if scammy else 'were not'} triggered by phrases in the text."
        ),
        "reasoning_zh": (
            f"【模拟结果 —— 未配置真实 Gonka Router 密钥】根据检索到的证据，该内容"
            f"{'风险较高' if scammy else ('可信' if verdict == 'credible' else '存疑')}。"
            f"文本中{'触发了' if scammy else '未触发'}诈骗模式特征。"
        ),
        "cited_source_urls": [],
    })


# --- tolerant normalizers for real model output -----------------------------
# Prompts ask for exact enum values, but real models improvise: "TRUE",
# "high risk", a 0-1 score, a stringified number. Normalizing here means one
# sloppy label does not cost us an entire second opinion -- while anything
# genuinely unrecognizable still falls through to a rejected verdict.

_VERDICT_ALIASES = {
    # canonical (context doc section 5)
    "credible": Verdict.credible,
    "questionable": Verdict.questionable,
    "high_risk": Verdict.high_risk,
    "insufficient": Verdict.insufficient,
    # what models actually say instead
    "true": Verdict.credible, "likely_true": Verdict.credible, "accurate": Verdict.credible,
    "mostly_true": Verdict.credible, "supported": Verdict.credible, "verified": Verdict.credible,
    "misleading": Verdict.questionable, "partly_true": Verdict.questionable,
    "mixed": Verdict.questionable, "disputed": Verdict.questionable, "unclear": Verdict.questionable,
    "scam": Verdict.high_risk, "fraud": Verdict.high_risk, "phishing": Verdict.high_risk,
    "false": Verdict.high_risk, "likely_false": Verdict.high_risk, "fake": Verdict.high_risk,
    "mostly_false": Verdict.high_risk, "refuted": Verdict.high_risk, "dangerous": Verdict.high_risk,
    "insufficient_evidence": Verdict.insufficient, "unverifiable": Verdict.insufficient,
    "unverified": Verdict.insufficient, "unknown": Verdict.insufficient,
    "uncertain": Verdict.insufficient, "no_evidence": Verdict.insufficient,
}


def _normalize_verdict(raw: object) -> Verdict:
    key = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key in _VERDICT_ALIASES:
        return _VERDICT_ALIASES[key]
    raise ValueError(f"unrecognized verdict label: {raw!r}")


def _normalize_score(raw: object) -> int:
    if raw is None:
        raise ValueError("missing score")
    if isinstance(raw, str):
        raw = raw.strip().rstrip("%")
    value = float(raw)  # type: ignore[arg-type]
    # A model answering on a 0-1 scale means 0.8 -> 80, not 0.
    if 0 < value <= 1:
        value *= 100
    return max(0, min(100, round(value)))


def _normalize_evidence_quality(raw: object, *, evidence_count: int) -> EvidenceQuality:
    """Trust the model's own read of evidence strength when it gives one, but
    never let it claim strong evidence when we retrieved nothing at all --
    that false confidence is exactly what the evidence gate exists to stop."""
    key = str(raw or "").strip().lower()
    parsed: EvidenceQuality | None = None
    for quality in (EvidenceQuality.strong, EvidenceQuality.mixed, EvidenceQuality.weak, EvidenceQuality.none):
        if quality.value in key:
            parsed = quality
            break

    if evidence_count == 0:
        return EvidenceQuality.none
    return parsed if parsed is not None else EvidenceQuality.weak


def _normalize_signals(raw: object, limit: int = 3) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()][:limit]


async def _verify_with_model(
    client: GonkaClient,
    settings: Settings,
    *,
    model_id: str,
    model_label: str,
    claim_text: str,
    evidence_block: str,
    evidence_count: int,
    ui_language: str,
) -> tuple[ModelVerdict | None, GonkaCallResult]:
    result = await client.call(
        model_id=model_id,
        model_label=model_label,
        system_prompt=VERIFY_SYSTEM,
        user_prompt=build_verify_user_prompt(claim_text, evidence_block, ui_language),
        mock_generator=lambda: _mock_verdict_json(
            claim_text, model_label, model_label, has_evidence=evidence_count > 0
        ),
    )
    if not result.ok or not result.content:
        return None, result

    try:
        data = extract_json_object(result.content)
        reasoning_en = str(data.get("reasoning_en") or data.get("reasoning_zh") or "").strip()
        reasoning_zh = str(data.get("reasoning_zh") or data.get("reasoning_en") or "").strip()
        if not reasoning_en:
            raise ValueError("model returned no reasoning text")
        signals_en = _normalize_signals(data.get("fraud_signals_en") or data.get("fraud_signals"))
        signals_zh = _normalize_signals(data.get("fraud_signals_zh")) or signals_en
        verdict = ModelVerdict(
            verdict=_normalize_verdict(data.get("verdict")),
            credibility_score=_normalize_score(data.get("credibility_score")),
            fraud_risk_score=_normalize_score(data.get("fraud_risk_score")),
            fraud_signals_en=signals_en,
            fraud_signals_zh=signals_zh,
            evidence_quality=_normalize_evidence_quality(
                data.get("evidence_quality"), evidence_count=evidence_count
            ),
            confidence=_normalize_score(data.get("confidence")),
            reasoning_en=reasoning_en,
            reasoning_zh=reasoning_zh,
            cited_source_urls=[str(u) for u in (data.get("cited_source_urls") or []) if u],
            meta=result.to_metadata(),
        )
        return verdict, result
    except (JsonExtractionError, KeyError, TypeError, ValueError) as exc:
        logger.warning("model %s returned schema-invalid output: %s", model_label, exc.__class__.__name__)
        failed = GonkaCallResult(
            ok=False, content=None, requested_model=result.requested_model, actual_model=result.actual_model,
            model_label=model_label, request_id=result.request_id, devshard_id=result.devshard_id,
            fallback_occurred=result.fallback_occurred, fallback_header_raw=result.fallback_header_raw,
            latency_ms=result.latency_ms, receipt_url=result.receipt_url, status="error",
            error_message="Model response failed schema validation.",
        )
        return None, failed


def _next_actions(verdict: Verdict, risk_band: RiskBand) -> list[NextAction]:
    """Safe next steps (context doc section 5).

    Note what is deliberately absent: we never tell someone to ring a number
    or open a link found inside the message they are checking -- a scam's own
    "support line" reaches the scammer. Every route out points to an
    independently-located official channel.
    """
    actions: list[NextAction] = []

    if risk_band in (RiskBand.high, RiskBand.medium):
        actions.append(NextAction(
            en="Pause. Do not click links, share codes, or send money or gift cards because of this message.",
            zh="请先暂停。不要因这条消息点击链接、分享验证码，或转账、购买礼品卡。",
        ))
        actions.append(NextAction(
            en="If it claims to be your bank or a government body, look up their official number yourself "
               "and contact them that way -- never using the contact details in the message.",
            zh="如果它声称来自银行或政府机构，请自行查找其官方号码并主动联系，"
               "切勿使用消息中提供的联系方式。",
        ))

    if verdict == Verdict.insufficient:
        actions.append(NextAction(
            en="Check an official source (a government site, the organisation's verified account, or a "
               "reputable news outlet) before believing or forwarding this.",
            zh="在相信或转发之前，请查阅官方来源（政府网站、机构认证账号或权威新闻媒体）。",
        ))

    if verdict == Verdict.questionable:
        actions.append(NextAction(
            en="Consider telling the sender it may be inaccurate before it spreads further.",
            zh="建议告知转发者该内容可能不准确，以免进一步传播。",
        ))

    if not actions:
        actions.append(NextAction(
            en="This appears consistent with the evidence found, but always double-check high-stakes claims "
               "yourself.",
            zh="该内容与检索到的证据基本一致，但涉及重大决策时仍建议自行再次核实。",
        ))
    return actions


async def run_verification(req: VerifyRequest, settings: Settings) -> VerificationReport:
    client = GonkaClient(settings)
    report_id = f"anx-{uuid.uuid4().hex[:12]}"

    # Mask the user's own identifiers BEFORE anything reaches a model
    # (context doc §9). Typed placeholders keep the scam structure intact --
    # see app/redaction.py. A URL is redacted for inference but the original
    # is still needed to actually fetch the page.
    redaction = redact(req.content)
    safe_content = redaction.text

    claims = await extract_claims(client, settings, safe_content)
    evidence = gather_evidence(req.input_mode, req.content, claims)
    evidence_block = _evidence_block(evidence)
    claim_text = claims.claims[0].text if claims.claims else safe_content

    (verdict_a, call_a), (verdict_b, call_b) = await asyncio.gather(
        _verify_with_model(
            client, settings, model_id=settings.gonka_model_a, model_label=settings.gonka_model_a_label,
            claim_text=claim_text, evidence_block=evidence_block, evidence_count=len(evidence),
            ui_language=req.ui_language.value,
        ),
        _verify_with_model(
            client, settings, model_id=settings.gonka_model_b, model_label=settings.gonka_model_b_label,
            claim_text=claim_text, evidence_block=evidence_block, evidence_count=len(evidence),
            ui_language=req.ui_language.value,
        ),
    )

    verdicts = [v for v in (verdict_a, verdict_b) if v is not None]
    if not verdicts:
        raise VerificationError(
            f"Both verifier models failed: {failed_call_summary([call_a, call_b])}",
            failed_calls=[call_a, call_b],
        )

    consensus = build_consensus(verdicts)

    limitations_en = [
        "Truth Score reflects available evidence at the time of the check, not absolute proof.",
        "Gonka Request IDs and receipts prove which decentralized model instance answered and when -- "
        "they do not themselves prove the claim is true or false.",
    ]
    limitations_zh = [
        "真实性评分反映的是核查当下可获得的证据，并非绝对证明。",
        "Gonka 请求 ID 与回执用于证明是哪个去中心化模型实例、何时作答，并不能直接证明该说法本身的真假。",
    ]
    if consensus.status == ConsensusStatus.single_model_only:
        limitations_en.append("Only one of the two pinned models returned a usable result for this check.")
        limitations_zh.append("本次核查中，两个指定模型仅有一个返回了可用结果。")
    if not evidence:
        limitations_en.append("No external evidence sources could be retrieved for this input.")
        limitations_zh.append("未能为该输入检索到外部证据来源。")

    note = redaction_note(redaction)
    if note:
        limitations_en.append(note[0])
        limitations_zh.append(note[1])

    return VerificationReport(
        report_id=report_id,
        created_at=VerificationReport.now(),
        input_mode=req.input_mode,
        analysis_mode=req.analysis_mode,
        # The redacted form, deliberately: it is what was actually analysed,
        # and it means a screenshot of a report can never leak real digits.
        original_input_excerpt=safe_content[:400],
        claims=claims.claims,
        evidence=evidence,
        model_verdicts=verdicts,
        consensus=consensus,
        limitations_en=limitations_en,
        limitations_zh=limitations_zh,
        next_actions=_next_actions(consensus.verdict, consensus.risk_band),
    )
