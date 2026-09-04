"use client";

import { useLanguage, pickBilingual } from "@/lib/i18n";
import type { ResultsStringKey } from "@/lib/i18n";
import type { ModelVerdict, Verdict } from "@/lib/types";

const VERDICT_LABEL_KEY: Record<Verdict, ResultsStringKey> = {
  credible: "verdictCredible",
  questionable: "verdictQuestionable",
  high_risk: "verdictHighRisk",
  insufficient: "verdictInsufficient",
};

/**
 * Side-by-side view of what each verifier concluded on its own.
 *
 * This is the challenge brief's mandatory requirement made visible. The
 * consensus sentence above says the models agreed; this shows the actual
 * separate numbers behind that claim, so "two models cross-verified it" is
 * something a reader can check rather than something we assert. It is also
 * where disagreement stops being a footnote: when the two columns differ,
 * you can see exactly where and by how much.
 */
export default function ModelComparison({
  verdicts,
  scoreDelta,
}: {
  verdicts: ModelVerdict[];
  scoreDelta: number;
}) {
  const { language, t } = useLanguage();
  if (verdicts.length === 0) return null;

  // Gonka confirmed DeepSeek is sustainedly saturated, so with no-fallback
  // enabled a single-model result is routine rather than exceptional. Saying
  // "this is the cross-verification" over one card would be a plain untruth,
  // and it is exactly the failure mode their mentor flagged.
  const crossVerified = verdicts.length === 2;

  return (
    <section
      className={`rounded-xl2 p-5 shadow-sm ${
        crossVerified
          ? "border border-anxin-border bg-anxin-surface"
          : "border-2 border-anxin-risk-medium bg-anxin-risk-medium-bg"
      }`}
    >
      <h3
        className={`text-base font-semibold ${
          crossVerified ? "text-anxin-ink" : "text-anxin-risk-medium"
        }`}
      >
        {crossVerified ? t.results.modelComparisonHeading : t.results.singleModelHeading}
      </h3>
      <p className="mt-1 text-xs text-anxin-ink-muted">
        {crossVerified ? t.results.modelComparisonHint : t.results.singleModelHint}
      </p>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {verdicts.map((v, i) => (
          <div key={i} className="rounded-lg border border-anxin-border bg-anxin-bg p-4">
            <p className="text-sm font-semibold text-anxin-brand-dark">{v.meta.model_label}</p>

            <dl className="mt-3 space-y-1.5 text-sm">
              <div className="flex items-baseline justify-between gap-2">
                <dt className="text-anxin-ink-muted">{t.results.truthScore}</dt>
                <dd className="text-lg font-bold tabular-nums text-anxin-ink">{v.credibility_score}</dd>
              </div>
              <div className="flex items-baseline justify-between gap-2">
                <dt className="text-anxin-ink-muted">{t.results.fraudRiskScore}</dt>
                <dd className="text-lg font-bold tabular-nums text-anxin-ink">{v.fraud_risk_score}</dd>
              </div>
              <div className="flex items-baseline justify-between gap-2">
                <dt className="text-anxin-ink-muted">{t.results.modelVerdictLabel}</dt>
                <dd className="text-right text-sm font-medium text-anxin-ink">
                  {t.results[VERDICT_LABEL_KEY[v.verdict]]}
                </dd>
              </div>
            </dl>

            <p className="mt-3 border-t border-anxin-border pt-3 text-xs leading-relaxed text-anxin-ink" lang={language}>
              {pickBilingual(language, v.reasoning_en, v.reasoning_zh)}
            </p>
          </div>
        ))}
      </div>

      {crossVerified && (
        <p className="mt-3 text-center text-xs font-medium text-anxin-ink-muted tabular-nums">
          {t.results.modelGap(scoreDelta)}
        </p>
      )}
    </section>
  );
}
