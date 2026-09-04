"""Documented consensus and disagreement rules (context doc section 8).

Every constant here is the single source of truth for "how much do two
independently-prompted models have to disagree before we tell the user we
are uncertain instead of confident". They are deliberately NOT buried in
prompt text, so they can be unit tested (tests/test_consensus.py) and quoted
verbatim in Q&A.

Three numbers that are NOT the same thing, and must never be conflated in
the UI (context doc section 8):

* credibility_score -- how strongly the available evidence supports the
                       factual claims (0 = clearly false, 100 = clearly true).
* fraud_risk_score  -- how strongly the content resembles a scam or
                       manipulation attempt. A claim can be weakly supported
                       without being a scam, or factually plausible while
                       still using manipulative payment instructions.
* confidence        -- how much the system trusts its own answer, from model
                       agreement AND evidence strength. Low confidence is
                       never hidden behind a precise-looking score.
"""
from __future__ import annotations

from app.gonka_client import GonkaCallResult
from app.schemas import (
    ConsensusResult,
    ConsensusStatus,
    EvidenceQuality,
    ModelVerdict,
    Verdict,
    risk_band_for,
)

# --- disagreement bands, in credibility-score points ----------------------
# Context doc section 8: 0-20 broadly agree, 21-40 reduce confidence,
# above 40 do not average into a confident score.
AGREEMENT_MAX_DELTA = 20
PARTIAL_DISAGREEMENT_MAX_DELTA = 40

# --- confidence penalties --------------------------------------------------
PARTIAL_DISAGREEMENT_PENALTY = 20
STRONG_DISAGREEMENT_PENALTY = 45
SINGLE_MODEL_CONFIDENCE_CAP = 60

# --- evidence gate ---------------------------------------------------------
# "Both models report weak/no evidence: cap confidence and show Insufficient
# evidence." A confident-looking score resting on nothing is the single most
# misleading thing this product could display.
WEAK_EVIDENCE_CONFIDENCE_CAP = 40

# --- verdict derivation thresholds ----------------------------------------
HIGH_RISK_FRAUD_SCORE = 67   # strong scam signals
HIGH_RISK_CREDIBILITY = 25   # ...or very low credibility
CREDIBLE_MIN_SCORE = 65

_EVIDENCE_RANK = {
    EvidenceQuality.none: 0,
    EvidenceQuality.weak: 1,
    EvidenceQuality.mixed: 2,
    EvidenceQuality.strong: 3,
}
_WEAK_EVIDENCE = (EvidenceQuality.weak, EvidenceQuality.none)


def _better_evidence(a: EvidenceQuality, b: EvidenceQuality) -> EvidenceQuality:
    return a if _EVIDENCE_RANK[a] >= _EVIDENCE_RANK[b] else b


def _derive_verdict(
    *,
    credibility: int,
    fraud_risk: int,
    evidence: EvidenceQuality,
    status: ConsensusStatus,
) -> Verdict:
    """Map the numbers onto the four documented states (context doc section 5).

    ORDER MATTERS, and this is the subtle part.

    Scam risk is evaluated FIRST -- before the evidence gate and before the
    disagreement bands. A phishing SMS ("your account is suspended, verify
    now") has no retrievable web evidence by its nature, so an evidence-first
    ordering would report the most dangerous messages we ever see as merely
    "Insufficient evidence". That under-warns precisely the person this
    product exists to protect.

    The two context-doc rules that meet here are section 8's evidence gate
    ("both models weak/no evidence -> Insufficient") and its fraud rule
    ("strong combination of payment request, impersonation, urgency ->
    raise fraud-risk presentation"). They are reconciled by scope: the
    evidence gate governs whether we can judge the CLAIM's truth, while
    fraud risk is read off the message's own manipulation pattern and needs
    no external sources at all.
    """
    # 1. Danger first, but ONLY on the fraud signal. A manipulation pattern is
    #    read off the message itself, so it survives both missing evidence and
    #    model disagreement about the factual claims.
    if fraud_risk >= HIGH_RISK_FRAUD_SCORE:
        return Verdict.high_risk
    # 2. Contradiction or an evidence vacuum -> we honestly do not know.
    #    Note this sits ABOVE the low-credibility branch: when the models
    #    disagree by more than 40 points the averaged credibility is not a
    #    number we are entitled to act on, so it must not be the basis of a
    #    "very low credibility" high-risk call either.
    if status == ConsensusStatus.strong_disagreement:
        return Verdict.insufficient
    if evidence in _WEAK_EVIDENCE:
        return Verdict.insufficient
    # 3. Very low credibility that BOTH models broadly agree on.
    if credibility <= HIGH_RISK_CREDIBILITY:
        return Verdict.high_risk
    # 4. Shaky but not dangerous.
    if status == ConsensusStatus.partial_disagreement or evidence == EvidenceQuality.mixed:
        return Verdict.questionable
    if credibility >= CREDIBLE_MIN_SCORE:
        return Verdict.credible
    return Verdict.questionable


def _merge_signals(a: list[str], b: list[str], limit: int = 3) -> list[str]:
    """Union of both models' warning signs, de-duplicated case-insensitively,
    capped at `limit` -- the context doc asks for three concise reasons, and a
    wall of bullet points is not readable by the audience this is built for."""
    seen: set[str] = set()
    merged: list[str] = []
    for signal in [*a, *b]:
        key = signal.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(signal.strip())
        if len(merged) >= limit:
            break
    return merged


def build_consensus(verdicts: list[ModelVerdict]) -> ConsensusResult:
    """``verdicts`` contains only the models that returned a VALID result.

    Callers filter out failed/timed-out calls first (see verifier.py) and
    handle the zero-successful-verdicts case explicitly rather than calling
    this at all.
    """
    if len(verdicts) == 0:
        raise ValueError("build_consensus requires at least one successful model verdict")

    if len(verdicts) == 1:
        v = verdicts[0]
        status = ConsensusStatus.single_model_only
        confidence = min(v.confidence, SINGLE_MODEL_CONFIDENCE_CAP)
        evidence = v.evidence_quality
        if evidence in _WEAK_EVIDENCE:
            confidence = min(confidence, WEAK_EVIDENCE_CONFIDENCE_CAP)
        verdict = _derive_verdict(
            credibility=v.credibility_score,
            fraud_risk=v.fraud_risk_score,
            evidence=evidence,
            status=status,
        )
        # Cross-verification did not happen, so we must not report a verdict
        # that reads as though it did. Gonka confirmed (2 Sep 2026) that
        # DeepSeek-V4-Flash is sustainedly saturated, so with no-fallback set
        # a 429 on that leg is an ORDINARY occurrence, not an edge case --
        # this path will run in production and on stage.
        #
        # high_risk is exempt for the same reason it is exempt from the
        # evidence gate: a scam pattern one model saw is still a scam, and
        # muting that warning to preserve methodological purity would harm
        # the person we are protecting. Everything else degrades.
        if verdict != Verdict.high_risk:
            verdict = Verdict.insufficient

        return ConsensusResult(
            status=status,
            verdict=verdict,
            credibility_score=v.credibility_score,
            fraud_risk_score=v.fraud_risk_score,
            risk_band=risk_band_for(v.fraud_risk_score),
            evidence_quality=evidence,
            confidence=confidence,
            score_delta=0,
            fraud_signals_en=_merge_signals(v.fraud_signals_en, []),
            fraud_signals_zh=_merge_signals(v.fraud_signals_zh, []),
            explanation_en=(
                f"Only {v.meta.model_label} returned a usable result, so this is a single opinion, "
                "NOT the cross-model verification Anxin normally performs. The other model was "
                "unavailable — usually because the Gonka network was saturated for that model and "
                "we refuse to silently substitute a different one. Confidence is capped and the "
                "verdict is downgraded accordingly."
            ),
            explanation_zh=(
                f"仅有 {v.meta.model_label} 返回了可用结果，因此这是单一模型意见，"
                "并非安心通常执行的跨模型验证。另一个模型不可用 —— 通常是因为 Gonka 网络中该模型已饱和，"
                "而我们拒绝在用户不知情的情况下替换成其他模型。置信度已被限制，结论也相应下调。"
            ),
        )

    a, b = verdicts[0], verdicts[1]
    delta = abs(a.credibility_score - b.credibility_score)
    avg_credibility = round((a.credibility_score + b.credibility_score) / 2)
    # Fraud risk ESCALATES rather than averaging: a scam one model missed
    # must still be flagged. Averaging risk down is how people get hurt.
    fraud_risk = max(a.fraud_risk_score, b.fraud_risk_score)
    evidence = _better_evidence(a.evidence_quality, b.evidence_quality)
    both_evidence_weak = a.evidence_quality in _WEAK_EVIDENCE and b.evidence_quality in _WEAK_EVIDENCE

    if delta <= AGREEMENT_MAX_DELTA:
        status = ConsensusStatus.agree
        confidence = round((a.confidence + b.confidence) / 2)
        explanation_en = (
            f"{a.meta.model_label} and {b.meta.model_label} independently reached similar credibility "
            f"scores (difference of {delta} points), so this result reflects genuine cross-model agreement."
        )
        explanation_zh = (
            f"{a.meta.model_label} 与 {b.meta.model_label} 独立得出的可信度评分接近"
            f"（相差 {delta} 分），该结果反映了跨模型的真实一致性。"
        )
    elif delta <= PARTIAL_DISAGREEMENT_MAX_DELTA:
        status = ConsensusStatus.partial_disagreement
        confidence = max(0, round((a.confidence + b.confidence) / 2) - PARTIAL_DISAGREEMENT_PENALTY)
        explanation_en = (
            f"{a.meta.model_label} and {b.meta.model_label} disagree moderately "
            f"({a.meta.model_label}: {a.credibility_score}, {b.meta.model_label}: {b.credibility_score}). "
            "Treat this as a lean, not a certainty, and review the evidence yourself."
        )
        explanation_zh = (
            f"{a.meta.model_label} 与 {b.meta.model_label} 存在中等程度的分歧"
            f"（{a.meta.model_label}：{a.credibility_score}，{b.meta.model_label}：{b.credibility_score}）。"
            "请将此结果视为倾向性判断而非确定结论，并自行查看证据。"
        )
    else:
        status = ConsensusStatus.strong_disagreement
        confidence = max(0, round((a.confidence + b.confidence) / 2) - STRONG_DISAGREEMENT_PENALTY)
        explanation_en = (
            f"{a.meta.model_label} and {b.meta.model_label} strongly disagree "
            f"({a.meta.model_label}: {a.credibility_score}, {b.meta.model_label}: {b.credibility_score}). "
            "Rather than average two contradictory opinions into a falsely precise number, Anxin reports "
            "this as Insufficient evidence. Please review the sources listed below yourself."
        )
        explanation_zh = (
            f"{a.meta.model_label} 与 {b.meta.model_label} 的结论存在严重分歧"
            f"（{a.meta.model_label}：{a.credibility_score}，{b.meta.model_label}：{b.credibility_score}）。"
            "系统不会把两个相互矛盾的意见平均成一个虚假精确的数字，而是将此内容标记为“证据不足”。"
            "请自行查看下方证据来源。"
        )

    verdict = _derive_verdict(
        credibility=avg_credibility,
        fraud_risk=fraud_risk,
        evidence=evidence,
        status=status,
    )

    # Evidence gate: if NEITHER model found usable evidence, no amount of
    # agreement earns a confident score. Exempt high_risk, for the same
    # reason the verdict ordering exempts it -- a scam pattern is read off
    # the message itself, so "no sources" is not a reason to sound unsure
    # about a warning we can see plainly.
    if both_evidence_weak and verdict != Verdict.high_risk:
        confidence = min(confidence, WEAK_EVIDENCE_CONFIDENCE_CAP)
        explanation_en += (
            " Both models reported weak or missing evidence, so confidence is capped and the result is "
            "reported as Insufficient evidence regardless of how closely they agreed."
        )
        explanation_zh += "两个模型均报告证据薄弱或缺失，因此置信度已被限制，无论二者结论多么接近，结果均标记为“证据不足”。"

    return ConsensusResult(
        status=status,
        verdict=verdict,
        credibility_score=avg_credibility,
        fraud_risk_score=fraud_risk,
        risk_band=risk_band_for(fraud_risk),
        evidence_quality=evidence,
        confidence=confidence,
        score_delta=delta,
        fraud_signals_en=_merge_signals(a.fraud_signals_en, b.fraud_signals_en),
        fraud_signals_zh=_merge_signals(a.fraud_signals_zh, b.fraud_signals_zh),
        explanation_en=explanation_en,
        explanation_zh=explanation_zh,
    )


def failed_call_summary(results: list[GonkaCallResult]) -> str:
    parts = []
    for r in results:
        if not r.ok:
            parts.append(f"{r.model_label}: {r.status}" + (f" ({r.error_message})" if r.error_message else ""))
    return "; ".join(parts)
