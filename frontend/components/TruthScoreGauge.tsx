"use client";

import { useEffect, useId, useState } from "react";
import type { Dictionary, ResultsStringKey } from "@/lib/i18n";
import type { RiskBand } from "@/lib/types";
import Icon, { type IconName } from "./Icon";

/**
 * UI-05 / UI-07: the headline number must land in five seconds, and no risk
 * meaning may rest on colour alone.
 *
 * Two signals are shown, deliberately kept apart. The arc is the Truth Score
 * (how well evidence supports the claim). The strip beneath it is the scam
 * risk band. A believable message can still be a scam, so blending them into
 * one colour would tell a reassuring lie -- the arc going green must never be
 * read as "safe" when the risk band says otherwise.
 */

/** Mirrors the risk colours in tailwind.config.ts. Duplicated as hex because
 * SVG stroke needs a literal value, not a utility class. */
const BAND_STROKE: Record<RiskBand, string> = {
  low: "#1a7a43",
  medium: "#a15c00",
  high: "#b3261e",
};

const BAND_CHROME: Record<RiskBand, { icon: IconName; labelKey: ResultsStringKey; box: string; fg: string }> = {
  low: { icon: "check", labelKey: "riskLow", box: "border-anxin-risk-low bg-anxin-risk-low-bg", fg: "text-anxin-risk-low" },
  medium: { icon: "warning", labelKey: "riskMedium", box: "border-anxin-risk-medium bg-anxin-risk-medium-bg", fg: "text-anxin-risk-medium" },
  high: { icon: "cross", labelKey: "riskHigh", box: "border-anxin-risk-high bg-anxin-risk-high-bg", fg: "text-anxin-risk-high" },
};

const SIZE = 208;
const STROKE = 16;
const RADIUS = SIZE * 0.35;
const CENTER = SIZE / 2;
const CIRCUMFERENCE = Math.PI * RADIUS;
const HAIRLINE_RADIUS = RADIUS - STROKE - 4;
const ARC = `M ${CENTER - RADIUS} ${CENTER} A ${RADIUS} ${RADIUS} 0 0 1 ${CENTER + RADIUS} ${CENTER}`;
// Crop the empty band above the arc so the dial sits tight under its label.
const TOP = CENTER - RADIUS - STROKE / 2 - 2;
const HEIGHT = CENTER + STROKE / 2 + 20 - TOP;

export default function TruthScoreGauge({
  score,
  band,
  t,
}: {
  score: number;
  band: RiskBand;
  t: Dictionary;
}) {
  const clamped = Math.max(0, Math.min(100, score));
  const chrome = BAND_CHROME[band];
  const trackId = useId();

  // Start empty, then sweep to the real value on mount. The arc is the single
  // orchestrated moment on this screen; everything else stays still.
  const [swept, setSwept] = useState(false);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setSwept(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <div className="flex flex-col items-center text-center">
      <p className="text-sm font-medium text-anxin-ink-muted">{t.results.truthScore}</p>

      <div className="relative mt-2" style={{ width: SIZE, height: HEIGHT }}>
        <svg
          width={SIZE}
          height={HEIGHT}
          viewBox={`0 ${TOP} ${SIZE} ${HEIGHT}`}
          role="meter"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={t.results.truthScore}
        >
          <path
            d={`M ${CENTER - HAIRLINE_RADIUS} ${CENTER} A ${HAIRLINE_RADIUS} ${HAIRLINE_RADIUS} 0 0 1 ${CENTER + HAIRLINE_RADIUS} ${CENTER}`}
            fill="none"
            stroke="#e2e2e0"
            strokeWidth="1"
          />

          <path d={ARC} fill="none" stroke="#e2e2e0" strokeWidth={STROKE} strokeLinecap="round" />

          <path
            id={trackId}
            d={ARC}
            fill="none"
            stroke={BAND_STROKE[band]}
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={swept ? CIRCUMFERENCE * (1 - clamped / 100) : CIRCUMFERENCE}
            className="transition-[stroke-dashoffset] duration-1000 ease-out motion-reduce:transition-none"
          />
        </svg>

        <span
          className="absolute inset-x-0 font-bold tabular-nums text-anxin-ink"
          style={{ top: CENTER - 46 - TOP, fontSize: 44, lineHeight: 1, textAlign: "center" }}
        >
          {clamped}
        </span>

        <span
          className="absolute text-xs font-medium text-anxin-ink-muted tabular-nums"
          style={{ left: CENTER - RADIUS - 4, top: CENTER + STROKE / 2 - TOP }}
        >
          0
        </span>
        <span
          className="absolute text-xs font-medium text-anxin-ink-muted tabular-nums"
          style={{ left: CENTER + RADIUS - 14, top: CENTER + STROKE / 2 - TOP }}
        >
          100
        </span>
      </div>

      <p className="mt-1 max-w-[16rem] text-xs leading-relaxed text-anxin-ink-muted">{t.results.truthScoreHint}</p>

      {/* The second signal, kept visually separate from the arc so the two are
          read as two things. Colour + glyph + words, never colour alone. */}
      <div className={`mt-3 w-full rounded-lg border-2 px-3 py-2.5 text-left ${chrome.box}`}>
        <p className="text-xs font-medium text-anxin-ink-muted">{t.results.riskLevel}</p>
        <p className={`mt-0.5 flex items-center gap-2 text-sm font-semibold ${chrome.fg}`}>
          <Icon name={chrome.icon} className="h-4 w-4" />
          <span>{t.results[chrome.labelKey]}</span>
        </p>
      </div>
    </div>
  );
}
