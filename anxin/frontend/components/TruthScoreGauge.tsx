import type { Dictionary } from "@/lib/i18n";

/** UI-05: the headline number + label must be understandable within five
 * seconds -- large numeral, short label, simple horizontal bar (no chart
 * library, no ambiguous colour-only meaning: the bar fill colour is always
 * accompanied by the numeric score and the verdict text rendered beside it). */
export default function TruthScoreGauge({ score, t }: { score: number; t: Dictionary }) {
  const barColor = score >= 65 ? "bg-anxin-risk-low" : score <= 35 ? "bg-anxin-risk-high" : "bg-anxin-risk-medium";

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-anxin-ink-muted">{t.results.truthScore}</span>
        <span className="text-3xl font-bold tabular-nums text-anxin-ink">{score}</span>
      </div>
      <div
        className="mt-2 h-3 w-full overflow-hidden rounded-full bg-anxin-border"
        role="meter"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={t.results.truthScore}
      >
        <div className={`h-full rounded-full ${barColor} transition-all`} style={{ width: `${score}%` }} />
      </div>
      <p className="mt-1 text-xs text-anxin-ink-muted">{t.results.truthScoreHint}</p>
    </div>
  );
}
