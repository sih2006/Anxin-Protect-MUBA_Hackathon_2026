"use client";

import { useRef, useState } from "react";
import { useLanguage } from "@/lib/i18n";
import type { AnalysisMode, InputMode } from "@/lib/types";
import { runOcr } from "@/lib/api";

const MAX_CHARS = 4000;
const ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

export interface SubmitPayload {
  inputMode: InputMode;
  analysisMode: AnalysisMode;
  content: string;
}

interface Props {
  onSubmit: (payload: SubmitPayload) => void;
  disabled: boolean;
}

type Tab = Extract<InputMode, "text" | "url" | "screenshot">;

export default function InputPanel({ onSubmit, disabled }: Props) {
  const { t } = useLanguage();
  const [tab, setTab] = useState<Tab>("text");
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("fact_check");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [ocrState, setOcrState] = useState<
    | { phase: "idle" }
    | { phase: "extracting" }
    | { phase: "review"; text: string; warning: string | null }
    | { phase: "failed"; message: string }
  >({ phase: "idle" });
  const [formError, setFormError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const content = tab === "text" ? text : tab === "url" ? url : ocrState.phase === "review" ? ocrState.text : "";

  async function handleFile(file: File) {
    setFormError(null);
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      setOcrState({ phase: "failed", message: t.input.invalidImage });
      return;
    }
    setOcrState({ phase: "extracting" });
    try {
      const result = await runOcr(file);
      setOcrState({ phase: "review", text: result.extracted_text, warning: result.warning });
    } catch {
      setOcrState({ phase: "failed", message: t.ocr.processingFailed });
    }
  }

  function validate(): string | null {
    const value = content.trim();
    if (!value) return t.input.emptyError;
    if (value.length > MAX_CHARS) return t.input.tooLong;
    if (tab === "url") {
      try {
        const parsed = new URL(value);
        if (!["http:", "https:"].includes(parsed.protocol)) return t.input.invalidUrl;
      } catch {
        return t.input.invalidUrl;
      }
    }
    return null;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const err = validate();
    if (err) {
      setFormError(err);
      return;
    }
    setFormError(null);
    onSubmit({ inputMode: tab, analysisMode, content: content.trim() });
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "text", label: t.input.modeText },
    { key: "url", label: t.input.modeUrl },
    { key: "screenshot", label: t.input.modeScreenshot },
  ];

  return (
    <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm sm:p-6" aria-labelledby="input-heading">
      <h2 id="input-heading" className="text-lg font-semibold text-anxin-ink">
        {t.input.heading}
      </h2>

      <div role="tablist" aria-label={t.input.heading} className="mt-4 flex gap-2">
        {tabs.map((tabItem) => (
          <button
            key={tabItem.key}
            type="button"
            role="tab"
            aria-selected={tab === tabItem.key}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              tab === tabItem.key
                ? "bg-anxin-brand text-white"
                : "border border-anxin-border bg-anxin-surface text-anxin-ink hover:border-anxin-brand"
            }`}
            onClick={() => {
              setTab(tabItem.key);
              setFormError(null);
            }}
          >
            {tabItem.label}
          </button>
        ))}
      </div>

      <div className="mt-3 flex gap-4" role="radiogroup" aria-label="analysis mode">
        {(["fact_check", "meme"] as AnalysisMode[]).map((mode) => (
          <label key={mode} className="flex items-center gap-2 text-sm text-anxin-ink">
            <input
              type="radio"
              name="analysisMode"
              checked={analysisMode === mode}
              onChange={() => setAnalysisMode(mode)}
              className="h-4 w-4 accent-anxin-brand"
            />
            {mode === "fact_check" ? t.input.analysisFactCheck : t.input.analysisMeme}
          </label>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-4">
        {tab === "text" && (
          <div>
            <label htmlFor="text-input" className="sr-only">
              {t.input.heading}
            </label>
            <textarea
              id="text-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t.input.textPlaceholder}
              rows={5}
              maxLength={MAX_CHARS + 200}
              className="w-full resize-y rounded-lg border border-anxin-border bg-anxin-bg p-3 text-anxin-ink placeholder:text-anxin-ink-muted focus:border-anxin-brand"
            />
            <p className="mt-1 text-right text-xs text-anxin-ink-muted">{t.input.charCount(text.length, MAX_CHARS)}</p>
          </div>
        )}

        {tab === "url" && (
          <div>
            <label htmlFor="url-input" className="sr-only">
              {t.input.modeUrl}
            </label>
            <input
              id="url-input"
              type="url"
              inputMode="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={t.input.urlPlaceholder}
              className="w-full rounded-lg border border-anxin-border bg-anxin-bg p-3 text-anxin-ink placeholder:text-anxin-ink-muted focus:border-anxin-brand"
            />
          </div>
        )}

        {tab === "screenshot" && (
          <div>
            <label htmlFor="file-input" className="block text-sm font-medium text-anxin-ink">
              {t.input.uploadLabel}
            </label>
            <p className="mt-1 text-xs text-anxin-ink-muted">{t.input.uploadHint}</p>
            <input
              id="file-input"
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_IMAGE_TYPES.join(",")}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void handleFile(file);
              }}
              className="mt-2 block w-full text-sm text-anxin-ink file:mr-3 file:rounded-full file:border-0 file:bg-anxin-brand file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-anxin-brand-dark"
            />

            {ocrState.phase === "extracting" && (
              <p role="status" className="mt-3 text-sm text-anxin-ink-muted">
                {t.ocr.extracting}
              </p>
            )}

            {ocrState.phase === "failed" && (
              <p role="alert" className="mt-3 text-sm text-anxin-risk-high">
                {ocrState.message}
              </p>
            )}

            {ocrState.phase === "review" && (
              <div className="mt-3 rounded-lg border border-anxin-border bg-anxin-bg p-3">
                <p className="text-sm font-medium text-anxin-ink">{t.ocr.reviewHeading}</p>
                <p className="mt-1 text-xs text-anxin-ink-muted">{t.ocr.reviewHint}</p>
                {ocrState.warning && (
                  <p role="alert" className="mt-1 text-xs text-anxin-risk-medium">
                    {ocrState.warning}
                  </p>
                )}
                <textarea
                  aria-label={t.ocr.reviewHeading}
                  value={ocrState.text}
                  onChange={(e) => setOcrState({ phase: "review", text: e.target.value, warning: ocrState.warning })}
                  rows={5}
                  maxLength={MAX_CHARS + 200}
                  className="mt-2 w-full resize-y rounded-lg border border-anxin-border bg-anxin-surface p-3 text-anxin-ink focus:border-anxin-brand"
                />
              </div>
            )}
          </div>
        )}

        {tab === "text" && (
          <div className="mt-3">
            <p className="text-xs font-medium text-anxin-ink-muted">{t.input.tryExample}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => { setText(t.input.exampleScamText); setFormError(null); }}
                className="rounded-full border border-anxin-border bg-anxin-bg px-3 py-1.5 text-xs font-medium text-anxin-ink transition hover:border-anxin-brand hover:text-anxin-brand"
              >
                {t.input.exampleScamLabel}
              </button>
              <button
                type="button"
                onClick={() => { setText(t.input.exampleClaimText); setFormError(null); }}
                className="rounded-full border border-anxin-border bg-anxin-bg px-3 py-1.5 text-xs font-medium text-anxin-ink transition hover:border-anxin-brand hover:text-anxin-brand"
              >
                {t.input.exampleClaimLabel}
              </button>
            </div>
          </div>
        )}

        {formError && (
          <p role="alert" className="mt-3 text-sm font-medium text-anxin-risk-high">
            {formError}
          </p>
        )}

        <button
          type="submit"
          disabled={disabled || (tab === "screenshot" && ocrState.phase !== "review")}
          className="mt-4 w-full rounded-lg bg-anxin-brand px-4 py-3 text-base font-semibold text-white transition hover:bg-anxin-brand-dark disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
        >
          {disabled ? t.input.submitting : tab === "screenshot" ? t.ocr.confirmAndCheck : t.input.submit}
        </button>
      </form>
    </section>
  );
}
