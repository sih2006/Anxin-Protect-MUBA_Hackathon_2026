"use client";

import { useLanguage } from "@/lib/i18n";
import { ApiError } from "@/lib/types";
import Icon from "./Icon";

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
    <section role="alert" className="rounded-xl2 border-2 border-anxin-risk-high bg-anxin-risk-high-bg p-6 text-center shadow-sm">
      <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-anxin-risk-high/10 text-anxin-risk-high">
        <Icon name="warning" className="h-7 w-7" strokeWidth={2} />
      </span>
      <p className="mt-3 text-lg font-semibold text-anxin-risk-high">{t.errors.heading}</p>
      <p className="mt-2 text-base text-anxin-ink">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-5 rounded-xl bg-anxin-brand px-6 py-3 text-base font-semibold text-white transition hover:bg-anxin-brand-dark focus:outline-none focus-visible:ring-2 focus-visible:ring-anxin-brand focus-visible:ring-offset-2"
      >
        {t.errors.retry}
      </button>
    </section>
  );
}
