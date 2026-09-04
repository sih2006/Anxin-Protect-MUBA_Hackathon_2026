"use client";

import { useLanguage, pickBilingual } from "@/lib/i18n";
import type { Dictionary, ResultsStringKey } from "@/lib/i18n";
import type { EvidenceQuality, VerificationReport, Verdict } from "@/lib/types";
import RiskBadge from "./RiskBadge";
import TruthScoreGauge from "./TruthScoreGauge";
import TransparencyPanel from "./TransparencyPanel";
import ModelComparison from "./ModelComparison";

const VERDICT_LABEL_KEY: Record<Verdict, ResultsStringKey> = {
  credible: "verdictCredible",
  questionable: "verdictQuestionable",
  high_risk: "verdictHighRisk",
  insufficient: "verdictInsufficient",
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
            <span className="rounded-full bg-anxin-risk-medium-bg px-3 py-1 text-xs font-semibold text-anxin-risk-medium">
              {t.results.disagreementBadge}
            </span>
          )}
          {singleModel && (
            <span className="rounded-full bg-anxin-risk-medium-bg px-3 py-1 text-xs font-semibold text-anxin-risk-medium">
              {t.results.singleModelBadge}
            </span>
          )}
        </div>

        <p className="mt-3 text-xs uppercase tracking-wide text-anxin-ink-muted">{t.results.excerptLabel}</p>
        <blockquote className="mt-1 rounded-lg bg-anxin-bg p-3 text-sm text-anxin-ink" lang={language}>
          &ldquo;{report.original_input_excerpt}&rdquo;
        </blockquote>

        {/* Verdict hierarchy: most important conclusion first and largest (UI-05). */}
        <p className="mt-5 text-2xl font-bold text-anxin-ink">{verdictLabel}</p>

        {/* Three numbers, deliberately shown as three: a credible-looking
            message can still be a scam, and neither score is the same thing
            as how much we trust our own answer. */}
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TruthScoreGauge score={consensus.credibility_score} t={t} />
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

        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-anxin-ink-muted">{t.results.riskLevel}:</span>
            <RiskBadge band={consensus.risk_band} t={t} />
          </div>
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
        <section className="rounded-xl2 border border-anxin-risk-high bg-anxin-risk-high-bg p-5 shadow-sm">
          <h3 className="text-base font-semibold text-anxin-risk-high">{t.results.warningSignsHeading}</h3>
          <ul className="mt-2 space-y-2">
            {signals.map((signal, i) => (
              <li key={i} className="flex gap-2 text-sm text-anxin-ink" lang={language}>
                <span aria-hidden="true">⚠</span>
                <span>{signal}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm">
        <h3 className="text-base font-semibold text-anxin-ink">{t.results.nextActionsHeading}</h3>
        <ul className="mt-2 space-y-2">
          {report.next_actions.map((action, i) => (
            <li key={i} className="flex gap-2 text-sm text-anxin-ink" lang={language}>
              <span aria-hidden="true">•</span>
              <span>{pickBilingual(language, action.en, action.zh)}</span>
            </li>
          ))}
        </ul>
      </section>

      <ModelComparison verdicts={report.model_verdicts} scoreDelta={consensus.score_delta} />

      <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm">
        <h3 className="text-base font-semibold text-anxin-ink">{t.results.evidenceHeading}</h3>
        {report.evidence.length === 0 ? (
          <p className="mt-2 text-sm text-anxin-ink-muted">{t.results.noEvidence}</p>
        ) : (
          <ul className="mt-2 space-y-3">
            {report.evidence.map((ev, i) => (
              <li key={i} className="rounded-lg border border-anxin-border p-3">
                <a
                  href={ev.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-anxin-brand underline underline-offset-2 hover:text-anxin-brand-dark"
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
