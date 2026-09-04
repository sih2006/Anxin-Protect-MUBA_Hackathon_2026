"use client";

import { useState } from "react";
import { useLanguage } from "@/lib/i18n";
import type { GonkaCallMetadata } from "@/lib/types";

/**
 * UI-06 / GON-06: expandable panel showing Request IDs, shards, models, and
 * a DIRECT link to the public https://api.gonkarouter.io/v1/receipts/{id}
 * endpoint for every model call -- not a link into our own backend, so
 * anyone can verify it independently of Anxin entirely.
 */
export default function TransparencyPanel({ calls }: { calls: GonkaCallMetadata[] }) {
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const anyMocked = calls.some((c) => c.status === "mocked");

  return (
    <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between text-left"
      >
        <span className="text-base font-semibold text-anxin-ink">{t.transparency.heading}</span>
        <span aria-hidden="true" className="text-anxin-ink-muted">
          {open ? "▲" : "▼"}
        </span>
        <span className="sr-only">{open ? t.transparency.toggleHide : t.transparency.toggleShow}</span>
      </button>

      {open && (
        <div className="mt-4 space-y-4">
          {anyMocked && (
            <p role="status" className="rounded-lg bg-anxin-risk-medium-bg p-3 text-sm text-anxin-risk-medium">
              {t.transparency.mockNotice}
            </p>
          )}
          {calls.map((call, idx) => (
            <div key={idx} className="rounded-lg border border-anxin-border p-4 text-sm">
              <p className="font-semibold text-anxin-ink">{call.model_label}</p>

              {call.status === "error" || call.status === "timeout" || call.status === "rate_limited" ? (
                <p className="mt-1 text-anxin-risk-high">
                  {t.transparency.modelFailed}
                  {call.error_message ? `: ${call.error_message}` : ""}
                </p>
              ) : (
                <dl className="mt-2 grid grid-cols-1 gap-x-4 gap-y-1 sm:grid-cols-2">
                  <Row label={t.transparency.requestedModel} value={call.requested_model} />
                  <Row label={t.transparency.actualModel} value={call.actual_model ?? "--"} />
                  <Row label={t.transparency.requestId} value={call.request_id ?? "--"} mono />
                  {call.devshard_id && <Row label={t.transparency.devshardId} value={call.devshard_id} mono />}
                  {call.latency_ms != null && (
                    <Row label={t.transparency.latency} value={`${call.latency_ms} ms`} />
                  )}
                </dl>
              )}

              {call.fallback_occurred && (
                <p role="alert" className="mt-2 text-xs font-medium text-anxin-risk-medium">
                  {t.transparency.fallbackWarning}
                </p>
              )}

              {call.receipt_url && (
                <div className="mt-3">
                  <a
                    href={call.receipt_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm font-medium text-anxin-brand underline underline-offset-2 hover:text-anxin-brand-dark"
                  >
                    {t.transparency.receiptLink}
                    <span aria-hidden="true">↗</span>
                  </a>
                  <p className="mt-1 text-xs text-anxin-ink-muted">{t.transparency.receiptHint}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <>
      <dt className="text-anxin-ink-muted">{label}</dt>
      <dd className={`truncate text-anxin-ink ${mono ? "font-mono text-xs" : ""}`} title={value}>
        {value}
      </dd>
    </>
  );
}
