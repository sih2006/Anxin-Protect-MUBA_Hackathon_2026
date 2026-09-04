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
        className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-anxin-border border-t-anxin-brand"
        aria-hidden="true"
      />
      <p className="mt-4 text-base font-medium text-anxin-ink">{t.progress[stageKey]}</p>
      <p className="mt-1 text-sm text-anxin-ink-muted">{t.progress.elapsed(elapsed)}</p>
      {elapsed > 8 && <p className="mt-2 text-xs text-anxin-ink-muted">{t.progress.stillWorking}</p>}
      <button
        type="button"
        onClick={onCancel}
        className="mt-4 rounded-full border border-anxin-border px-4 py-2 text-sm font-medium text-anxin-ink hover:border-anxin-brand hover:text-anxin-brand"
      >
        {t.input.cancel}
      </button>
    </section>
  );
}
