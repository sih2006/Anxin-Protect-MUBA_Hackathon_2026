import type { RiskBand } from "@/lib/types";
import type { Dictionary, ResultsStringKey } from "@/lib/i18n";

/**
 * UI-07 / Design standard: warnings never depend on colour alone. Every risk
 * level pairs a distinct icon glyph AND a text label with its background
 * colour, so the meaning survives colour-blindness, greyscale printing, or a
 * screen reader (icons are aria-hidden; the text label carries the meaning).
 */
const RISK_CONFIG: Record<RiskBand, { icon: string; bg: string; fg: string; labelKey: ResultsStringKey }> = {
  low: { icon: "✓", bg: "bg-anxin-risk-low-bg", fg: "text-anxin-risk-low", labelKey: "riskLow" },
  medium: { icon: "⚠", bg: "bg-anxin-risk-medium-bg", fg: "text-anxin-risk-medium", labelKey: "riskMedium" },
  high: { icon: "✕", bg: "bg-anxin-risk-high-bg", fg: "text-anxin-risk-high", labelKey: "riskHigh" },
};

export default function RiskBadge({ band, t }: { band: RiskBand; t: Dictionary }) {
  const cfg = RISK_CONFIG[band];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium ${cfg.bg} ${cfg.fg}`}
    >
      <span aria-hidden="true">{cfg.icon}</span>
      <span>{t.results[cfg.labelKey]}</span>
    </span>
  );
}
