"use client";

import { useLanguage } from "@/lib/i18n";
import { ApiError } from "@/lib/types";

/** UI-09: every known failure path (rate-limited, timeout, network, generic)
 * gets an understandable, actionable message and a retry -- never a raw
 * stack trace or bare HTTP status code. */
export default function ErrorState({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { t } = useLanguage();

  let message = t.errors.generic;
  if (error instanceof ApiError) {
    if (error.status === 429 || error.status === 503) message = t.errors.rateLimited;
    else if (error.message === "timeout") message = t.errors.timeout;
    else if (error.message === "network_error") message = t.errors.network;
    else if (error.detail) message = error.detail;
  }

  return (
    <section role="alert" className="rounded-xl2 border border-anxin-risk-high bg-anxin-risk-high-bg p-6 text-center shadow-sm">
      <p className="text-base font-semibold text-anxin-risk-high">{t.errors.heading}</p>
      <p className="mt-2 text-sm text-anxin-ink">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 rounded-full bg-anxin-brand px-5 py-2.5 text-sm font-medium text-white hover:bg-anxin-brand-dark"
      >
        {t.errors.retry}
      </button>
    </section>
  );
}
