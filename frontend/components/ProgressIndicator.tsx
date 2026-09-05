"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/lib/i18n";

/** UI-04: users see the current stage, elapsed time, and can cancel while
 * decentralized inference runs. The stages below are cosmetic (the backend
 * does one request), but they set honest expectations that two independent
 * models are being consulted through Gonka rather than a single fast call. */
const STAGE_KEYS = ["stageClaim", "stageEvidence", "stageModelA", "stageModelB", "stageConsensus"] as const;
const STAGE_INTERVAL_MS = 1800;

export default function ProgressIndicator({ onCancel }: { onCancel: () => void }) {
  const { t } = useLanguage();
  const [stageIndex, setStageIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const stageTimer = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, STAGE_KEYS.length - 1));
    }, STAGE_INTERVAL_MS);
    const clock = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => {
      clearInterval(stageTimer);
      clearInterval(clock);
    };
  }, []);

  const stageKey = STAGE_KEYS[stageIndex] ?? STAGE_KEYS[0];

  return (
    <section
      className="rounded-xl2 border border-anxin-border bg-anxin-surface p-6 text-center shadow-sm"
      role="status"
      aria-live="polite"
    >
      <div
        className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-anxin-brand-soft border-t-anxin-brand motion-reduce:animate-none"
        aria-hidden="true"
      />

      {/* Which of the five stages we are on, as shape not just words. */}
      <ol className="mt-5 flex items-center justify-center gap-2" aria-hidden="true">
        {STAGE_KEYS.map((key, i) => (
          <li
            key={key}
            className={`h-2 rounded-full transition-all duration-500 ${
              i < stageIndex
                ? "w-2 bg-anxin-brand"
                : i === stageIndex
                  ? "w-8 bg-anxin-brand"
                  : "w-2 bg-anxin-border"
            }`}
          />
        ))}
      </ol>

      <p className="mt-4 text-base font-medium text-anxin-ink">{t.progress[stageKey]}</p>
      <p className="mt-1 text-sm tabular-nums text-anxin-ink-muted">{t.progress.elapsed(elapsed)}</p>
      {elapsed > 8 && (
        <p className="mx-auto mt-2 max-w-prose text-xs leading-relaxed text-anxin-ink-muted">
          {t.progress.stillWorking}
        </p>
      )}
      <button
        type="button"
        onClick={onCancel}
        className="mt-5 rounded-full border-2 border-anxin-border px-5 py-2.5 text-sm font-semibold text-anxin-ink transition hover:border-anxin-brand hover:text-anxin-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-anxin-brand focus-visible:ring-offset-2"
      >
        {t.input.cancel}
      </button>
    </section>
  );
}
