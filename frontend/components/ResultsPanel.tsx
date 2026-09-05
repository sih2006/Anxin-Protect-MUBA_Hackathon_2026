"use client";

import { useLanguage, pickBilingual } from "@/lib/i18n";
import type { Dictionary, ResultsStringKey } from "@/lib/i18n";
import type { EvidenceQuality, ExtractedClaim, VerificationReport, Verdict } from "@/lib/types";
import TruthScoreGauge from "./TruthScoreGauge";
import TransparencyPanel from "./TransparencyPanel";
import ModelComparison, { VERDICT_CHROME } from "./ModelComparison";
import Icon from "./Icon";

const VERDICT_LABEL_KEY: Record<Verdict, ResultsStringKey> = {
  credible: "verdictCredible",
  questionable: "verdictQuestionable",
  high_risk: "verdictHighRisk",
  insufficient: "verdictInsufficient",
};

/** The backend separates a checkable assertion from an opinion before it
 * verifies anything (`ExtractedClaim.claim_type`). Surfacing that is what
 * stops "not enough evidence" from reading as a failure: an opinion was
 * never fact-checkable, and saying so is the honest answer, not a shrug. */
const CLAIM_TYPE: Record<ExtractedClaim["claim_type"], { labelKey: ResultsStringKey; chip: string }> = {
  factual: { labelKey: "claimFactual", chip: "border-anxin-brand bg-anxin-brand-soft text-anxin-brand-dark" },
  opinion: { labelKey: "claimOpinion", chip: "border-anxin-border bg-anxin-bg text-anxin-ink-muted" },
  unverifiable: { labelKey: "claimUnverifiable", chip: "border-anxin-risk-unknown bg-anxin-risk-unknown-bg text-anxin-risk-unknown" },
};

const EVIDENCE_LABEL_KEY: Record<EvidenceQuality, ResultsStringKey> = {
  strong: "evidenceStrong",
  mixed: "evidenceMixed",
  weak: "evidenceWeak",
  none: "evidenceNone",
};

export default function ResultsPanel({ report, onNewCheck }: { report: VerificationReport; onNewCheck: () => void }) {
  const { language, t } = useLanguage();
  const { consensus } = report;
  const verdictLabel = t.results[VERDICT_LABEL_KEY[consensus.verdict]];
  const verdictChrome = VERDICT_CHROME[consensus.verdict];
  const showDisagreement = consensus.status === "partial_disagreement" || consensus.status === "strong_disagreement";
  const singleModel = consensus.status === "single_model_only";
  const signals = language === "zh" ? consensus.fraud_signals_zh : consensus.fraud_signals_en;

  return (
    <div className="space-y-4">
      <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm sm:p-6" aria-labelledby="results-heading">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="results-heading" className="text-lg font-semibold text-anxin-ink">
            {t.results.heading}
          </h2>
          {showDisagreement && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-anxin-risk-medium-bg px-3 py-1 text-xs font-semibold text-anxin-risk-medium">
              <Icon name="warning" className="h-3.5 w-3.5" />
              {t.results.disagreementBadge}
            </span>
          )}
          {singleModel && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-anxin-risk-medium-bg px-3 py-1 text-xs font-semibold text-anxin-risk-medium">
              <Icon name="warning" className="h-3.5 w-3.5" />
              {t.results.singleModelBadge}
            </span>
          )}
        </div>

        <p className="mt-3 text-xs uppercase tracking-wide text-anxin-ink-muted">{t.results.excerptLabel}</p>
        <blockquote className="mt-1 rounded-lg bg-anxin-bg p-3 text-sm text-anxin-ink" lang={language}>
          &ldquo;{report.original_input_excerpt}&rdquo;
        </blockquote>

        {/* Verdict hierarchy: most important conclusion first and largest
            (UI-05). Carried on a tinted band with a matching icon, so the
            headline answer is legible from across a room and still survives
            greyscale -- the words say it, the icon shapes it, colour is third. */}
        <div
          className={`mt-5 flex items-center gap-3 rounded-xl border-2 px-4 py-3.5 ${verdictChrome.box} ${verdictChrome.fg}`}
        >
          <Icon name={verdictChrome.icon} className="h-8 w-8" strokeWidth={2} />
          <p className="text-2xl font-bold leading-tight">{verdictLabel}</p>
        </div>

        {/* Three numbers, deliberately shown as three: a credible-looking
            message can still be a scam, and neither score is the same thing
            as how much we trust our own answer. */}
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TruthScoreGauge score={consensus.credibility_score} band={consensus.risk_band} t={t} />
          <div>
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-medium text-anxin-ink-muted">{t.results.fraudRiskScore}</span>
              <span className="text-3xl font-bold tabular-nums text-anxin-ink">{consensus.fraud_risk_score}</span>
            </div>
            <div
              className="mt-2 h-3 w-full overflow-hidden rounded-full bg-anxin-border"
              role="meter"
              aria-valuenow={consensus.fraud_risk_score}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={t.results.fraudRiskScore}
            >
              <div
                className={`h-full rounded-full transition-all ${
                  consensus.risk_band === "high"
                    ? "bg-anxin-risk-high"
                    : consensus.risk_band === "medium"
                      ? "bg-anxin-risk-medium"
                      : "bg-anxin-risk-low"
                }`}
                style={{ width: `${consensus.fraud_risk_score}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-anxin-ink-muted">{t.results.fraudRiskHint}</p>
          </div>
        </div>

        {/* The risk band itself now lives inside TruthScoreGauge, directly
            under the arc, so it is read against the number it qualifies. */}
        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3">
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-medium text-anxin-ink-muted">{t.results.confidence}:</span>
            <span className="text-lg font-semibold tabular-nums text-anxin-ink">{consensus.confidence}</span>
            <span className="text-xs text-anxin-ink-muted">({t.results.confidenceHint})</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-medium text-anxin-ink-muted">{t.results.evidenceQualityLabel}:</span>
            <span className="text-sm font-semibold text-anxin-ink">
              {t.results[EVIDENCE_LABEL_KEY[consensus.evidence_quality]]}
            </span>
          </div>
        </div>

        <p className="mt-4 rounded-lg bg-anxin-bg p-3 text-sm text-anxin-ink" lang={language}>
          {pickBilingual(language, consensus.explanation_en, consensus.explanation_zh)}
        </p>
      </section>

      {signals.length > 0 && (
        <section className="rounded-xl2 border-2 border-anxin-risk-high bg-anxin-risk-high-bg p-5 shadow-sm">
          <h3 className="flex items-center gap-2 text-base font-semibold text-anxin-risk-high">
            <Icon name="warning" className="h-5 w-5" strokeWidth={2} />
            {t.results.warningSignsHeading}
          </h3>
          <ul className="mt-3 space-y-2.5">
            {signals.map((signal, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-anxin-ink" lang={language}>
                <Icon name="warning" className="mt-0.5 h-4 w-4 text-anxin-risk-high" />
                <span>{signal}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* The one card that tells the reader what to DO. Given the brand edge
          so it reads as guidance rather than another block of findings. */}
      <section className="rounded-xl2 border-2 border-anxin-brand bg-anxin-brand-soft p-5 shadow-sm">
        <h3 className="flex items-center gap-2 text-base font-semibold text-anxin-brand-dark">
          <Icon name="shield" className="h-5 w-5" strokeWidth={2} />
          {t.results.nextActionsHeading}
        </h3>
        <ul className="mt-3 space-y-2.5">
          {report.next_actions.map((action, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm text-anxin-ink" lang={language}>
              <Icon name="check" className="mt-0.5 h-4 w-4 text-anxin-brand" />
              <span>{pickBilingual(language, action.en, action.zh)}</span>
            </li>
          ))}
        </ul>
      </section>

      <ModelComparison verdicts={report.model_verdicts} scoreDelta={consensus.score_delta} />

      {/* The claim the backend actually verified. Without this the report
          answers a question the reader never saw us ask. */}
      {report.claims.length > 0 && (
        <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm">
          <h3 className="flex items-center gap-2 text-base font-semibold text-anxin-ink">
            <Icon name="text" className="h-5 w-5 text-anxin-ink-muted" />
            {t.results.claimsHeading}
          </h3>
          <p className="mt-1 text-xs leading-relaxed text-anxin-ink-muted">{t.results.claimsHint}</p>
          <ul className="mt-3 space-y-2.5">
            {report.claims.map((claim, i) => {
              const type = CLAIM_TYPE[claim.claim_type];
              return (
                <li key={i} className="rounded-lg border border-anxin-border bg-anxin-bg p-3">
                  <p className="text-sm leading-relaxed text-anxin-ink" lang={language}>
                    {claim.text}
                  </p>
                  <span
                    className={`mt-2 inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${type.chip}`}
                  >
                    {t.results[type.labelKey]}
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="flex items-center gap-2 text-base font-semibold text-anxin-ink">
            <Icon name="link" className="h-5 w-5 text-anxin-ink-muted" />
            {t.results.evidenceHeading}
          </h3>
          {report.evidence.length > 0 && (
            <span className="text-xs font-medium tabular-nums text-anxin-ink-muted">
              {t.results.evidenceSourceCount(report.evidence.length)}
            </span>
          )}
        </div>
        {report.evidence.length === 0 ? (
          <p className="mt-2 text-sm text-anxin-ink-muted">{t.results.noEvidence}</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {report.evidence.map((ev, i) => (
              <li key={i} className="rounded-lg border border-anxin-border p-3">
                <a
                  href={ev.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-anxin-brand underline underline-offset-2 hover:text-anxin-brand-dark focus:outline-none focus-visible:ring-2 focus-visible:ring-anxin-brand focus-visible:ring-offset-2"
                >
                  {ev.title}
                </a>
                <p className="mt-1 text-xs text-anxin-ink-muted">{ev.snippet}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm">
        <h3 className="text-base font-semibold text-anxin-ink">{t.results.limitationsHeading}</h3>
        <ul className="mt-2 space-y-1">
          {(language === "zh" ? report.limitations_zh : report.limitations_en).map((line, i) => (
            <li key={i} className="text-sm text-anxin-ink-muted">
              {line}
            </li>
          ))}
        </ul>
      </section>

      <TransparencyPanel calls={report.model_verdicts.map((v) => v.meta)} />

      <div className="text-center">
        <button
          type="button"
          onClick={onNewCheck}
          className="rounded-full border border-anxin-border bg-anxin-surface px-5 py-2.5 text-sm font-medium text-anxin-ink hover:border-anxin-brand hover:text-anxin-brand"
        >
          {t.results.newCheck}
        </button>
      </div>
    </div>
  );
}
