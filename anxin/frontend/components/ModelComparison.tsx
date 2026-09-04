"use client";

import { useLanguage, pickBilingual } from "@/lib/i18n";
import type { Dictionary, ResultsStringKey } from "@/lib/i18n";
import type { Language, ModelVerdict, Verdict } from "@/lib/types";
import Icon, { type IconName } from "./Icon";

const VERDICT_LABEL_KEY: Record<Verdict, ResultsStringKey> = {
  credible: "verdictCredible",
  questionable: "verdictQuestionable",
  high_risk: "verdictHighRisk",
  insufficient: "verdictInsufficient",
};

/** UI-07: a verdict never arrives as colour alone -- glyph and words carry it. */
export const VERDICT_CHROME: Record<Verdict, { icon: IconName; box: string; fg: string }> = {
  credible: { icon: "check", box: "border-anxin-risk-low bg-anxin-risk-low-bg", fg: "text-anxin-risk-low" },
  questionable: { icon: "question", box: "border-anxin-risk-medium bg-anxin-risk-medium-bg", fg: "text-anxin-risk-medium" },
  high_risk: { icon: "cross", box: "border-anxin-risk-high bg-anxin-risk-high-bg", fg: "text-anxin-risk-high" },
  insufficient: { icon: "dash", box: "border-anxin-risk-unknown bg-anxin-risk-unknown-bg", fg: "text-anxin-risk-unknown" },
};

function VerdictPill({ verdict, t }: { verdict: Verdict; t: Dictionary }) {
  const chrome = VERDICT_CHROME[verdict];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${chrome.box} ${chrome.fg}`}>
      <Icon name={chrome.icon} className="h-3.5 w-3.5" />
      {t.results[VERDICT_LABEL_KEY[verdict]]}
    </span>
  );
}

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <dt className="text-sm text-anxin-ink-muted">{label}</dt>
      <dd className="text-lg font-bold tabular-nums text-anxin-ink">{value}</dd>
    </div>
  );
}

function Reasoning({ verdict, language }: { verdict: ModelVerdict; language: Language }) {
  return (
    <p className="text-xs leading-relaxed text-anxin-ink" lang={language}>
      {pickBilingual(language, verdict.reasoning_en, verdict.reasoning_zh)}
    </p>
  );
}

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

  // Deliberately two different shapes, not one shape in two colours. A single
  // opinion must not be able to masquerade as a comparison at a glance.
  if (!crossVerified) {
    return (
      <section className="overflow-hidden rounded-xl2 border-2 border-anxin-risk-medium bg-anxin-risk-medium-bg shadow-sm">
        <div className="flex items-start gap-3 p-5">
          <Icon name="warning" className="mt-0.5 h-6 w-6 text-anxin-risk-medium" strokeWidth={2} />
          <div>
            <h3 className="text-base font-semibold text-anxin-risk-medium">{t.results.singleModelHeading}</h3>
            <p className="mt-1 max-w-prose text-xs leading-relaxed text-anxin-ink-muted">
              {t.results.singleModelHint}
            </p>
          </div>
        </div>

        {verdicts.map((v, i) => (
          <div key={i} className="border-t-2 border-anxin-risk-medium bg-anxin-surface p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-anxin-brand-dark">{v.meta.model_label}</p>
              <VerdictPill verdict={v.verdict} t={t} />
            </div>

            <dl className="mt-4 grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2">
              <ScoreRow label={t.results.truthScore} value={v.credibility_score} />
              <ScoreRow label={t.results.fraudRiskScore} value={v.fraud_risk_score} />
            </dl>

            <div className="mt-4 border-t border-anxin-border pt-3">
              <Reasoning verdict={v} language={language} />
            </div>
          </div>
        ))}
      </section>
    );
  }

  return (
    <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm">
      <h3 className="text-base font-semibold text-anxin-ink">{t.results.modelComparisonHeading}</h3>
      <p className="mt-1 max-w-prose text-xs leading-relaxed text-anxin-ink-muted">
        {t.results.modelComparisonHint}
      </p>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {verdicts.map((v, i) => (
          <div key={i} className="flex flex-col rounded-lg border border-anxin-border bg-anxin-bg">
            <div className="flex flex-wrap items-center justify-between gap-2 p-4 pb-3">
              <p className="text-sm font-semibold text-anxin-brand-dark">{v.meta.model_label}</p>
              <VerdictPill verdict={v.verdict} t={t} />
            </div>

            <div className="border-t border-anxin-border" />

            <dl className="space-y-1.5 p-4 pt-3">
              <ScoreRow label={t.results.truthScore} value={v.credibility_score} />
              <ScoreRow label={t.results.fraudRiskScore} value={v.fraud_risk_score} />
            </dl>

            <div className="mt-auto border-t border-anxin-border p-4 pt-3">
              <Reasoning verdict={v} language={language} />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-3 text-center text-xs font-medium tabular-nums text-anxin-ink-muted">
        {t.results.modelGap(scoreDelta)}
      </p>
    </section>
  );
}
