"use client";

import { useRef, useState } from "react";
import { useLanguage } from "@/lib/i18n";
import type { AnalysisMode, InputMode } from "@/lib/types";
import { runOcr } from "@/lib/api";
import Icon, { type IconName } from "./Icon";

const MAX_CHARS = 4000;
const ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

/** Weak focus rings fail the people this tool is for. One shared, obviously
 * visible focus treatment on every interactive surface. */
const FOCUS = "focus:outline-none focus-visible:ring-2 focus-visible:ring-anxin-brand focus-visible:ring-offset-2 focus-visible:ring-offset-anxin-surface";
const FIELD = `w-full rounded-xl border-2 border-anxin-border bg-anxin-surface p-4 text-lg leading-relaxed text-anxin-ink placeholder:text-anxin-ink-muted ${FOCUS} focus-visible:border-anxin-brand`;

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

  // The icon repeats what the word says. That redundancy is the point: a
  // recognisable shape is faster to find than read, and survives a language
  // the reader is less fluent in.
  const tabs: { key: Tab; label: string; icon: IconName }[] = [
    { key: "text", label: t.input.modeText, icon: "text" },
    { key: "url", label: t.input.modeUrl, icon: "link" },
    { key: "screenshot", label: t.input.modeScreenshot, icon: "image" },
  ];

  return (
    <section className="rounded-xl2 border border-anxin-border bg-anxin-surface p-5 shadow-sm sm:p-8" aria-labelledby="input-heading">
      <h2 id="input-heading" className="text-2xl font-semibold tracking-tight text-anxin-ink">
        {t.input.heading}
      </h2>

      {/* Segmented control rather than three loose pills: one enclosure, one
          filled segment. Fewer competing shapes to parse. Targets are sized
          for fingers and unsteady hands, not cursors. */}
      <div
        role="tablist"
        aria-label={t.input.heading}
        className="mt-5 grid grid-cols-3 rounded-xl border-2 border-anxin-border bg-anxin-bg p-1"
      >
        {tabs.map((tabItem) => (
          <button
            key={tabItem.key}
            type="button"
            role="tab"
            id={`tab-${tabItem.key}`}
            aria-selected={tab === tabItem.key}
            aria-controls="input-panel"
            className={`flex items-center justify-center gap-1.5 rounded-lg px-1.5 py-3 text-sm font-semibold transition sm:gap-2 sm:px-3 sm:text-base ${FOCUS} ${
              tab === tabItem.key
                ? "bg-anxin-brand text-white shadow-sm"
                : "text-anxin-ink-muted hover:bg-anxin-surface hover:text-anxin-ink"
            }`}
            onClick={() => {
              setTab(tabItem.key);
              setFormError(null);
            }}
          >
            <Icon name={tabItem.icon} className="h-4 w-4 sm:h-5 sm:w-5" />
            {tabItem.label}
          </button>
        ))}
      </div>

      {/* Two large selectable cards instead of native radios: a 16px radio
          is a hard target at 70. The real <input> stays for the keyboard and
          screen readers; the card is its label. */}
      <fieldset className="mt-5">
        <legend className="text-base font-medium text-anxin-ink-muted">{t.input.analysisModeLabel}</legend>
        <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {(["fact_check", "meme"] as AnalysisMode[]).map((mode) => {
            const checked = analysisMode === mode;
            return (
              <label
                key={mode}
                className={`flex cursor-pointer items-center gap-3 rounded-xl border-2 px-4 py-3.5 text-base font-medium transition ${
                  checked
                    ? "border-anxin-brand bg-anxin-brand-soft text-anxin-brand-dark"
                    : "border-anxin-border bg-anxin-surface text-anxin-ink hover:border-anxin-ink-muted"
                }`}
              >
                <input
                  type="radio"
                  name="analysisMode"
                  checked={checked}
                  onChange={() => setAnalysisMode(mode)}
                  className={`h-5 w-5 shrink-0 accent-anxin-brand ${FOCUS}`}
                />
                {mode === "fact_check" ? t.input.analysisFactCheck : t.input.analysisMeme}
              </label>
            );
          })}
        </div>
      </fieldset>

      <form onSubmit={handleSubmit} className="mt-6" id="input-panel" role="tabpanel" aria-labelledby={`tab-${tab}`}>
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
              rows={7}
              maxLength={MAX_CHARS + 200}
              className={`${FIELD} resize-y`}
            />
            <p className="mt-2 text-right text-sm tabular-nums text-anxin-ink-muted">
              {t.input.charCount(text.length, MAX_CHARS)}
            </p>
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
              className={FIELD}
            />
          </div>
        )}

        {tab === "screenshot" && (
          <div>
            <label htmlFor="file-input" className="block text-sm font-medium text-anxin-ink">
              {t.input.uploadLabel}
            </label>
            <p className="mt-1 max-w-prose text-xs leading-relaxed text-anxin-ink-muted">{t.input.uploadHint}</p>
            <input
              id="file-input"
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_IMAGE_TYPES.join(",")}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void handleFile(file);
              }}
              className={`mt-3 block w-full rounded-lg text-sm text-anxin-ink ${FOCUS} file:mr-3 file:rounded-md file:border-0 file:bg-anxin-brand file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-anxin-brand-dark`}
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
              <div className="mt-4 rounded-lg border border-anxin-border bg-anxin-bg p-4">
                <p className="text-sm font-medium text-anxin-ink">{t.ocr.reviewHeading}</p>
                <p className="mt-1 max-w-prose text-xs leading-relaxed text-anxin-ink-muted">{t.ocr.reviewHint}</p>
                {ocrState.warning && (
                  <p role="alert" className="mt-2 text-xs font-medium text-anxin-risk-medium">
                    {ocrState.warning}
                  </p>
                )}
                <textarea
                  aria-label={t.ocr.reviewHeading}
                  value={ocrState.text}
                  onChange={(e) => setOcrState({ phase: "review", text: e.target.value, warning: ocrState.warning })}
                  rows={5}
                  maxLength={MAX_CHARS + 200}
                  className={`mt-3 ${FIELD} resize-y bg-anxin-surface`}
                />
              </div>
            )}
          </div>
        )}

        {tab === "text" && (
          <div className="mt-5">
            <p className="text-sm font-medium text-anxin-ink-muted">{t.input.tryExample}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => { setText(t.input.exampleScamText); setFormError(null); }}
                className={`rounded-full border-2 border-anxin-border bg-anxin-bg px-4 py-2 text-sm font-medium text-anxin-ink transition hover:border-anxin-brand hover:text-anxin-brand ${FOCUS}`}
              >
                {t.input.exampleScamLabel}
              </button>
              <button
                type="button"
                onClick={() => { setText(t.input.exampleClaimText); setFormError(null); }}
                className={`rounded-full border-2 border-anxin-border bg-anxin-bg px-4 py-2 text-sm font-medium text-anxin-ink transition hover:border-anxin-brand hover:text-anxin-brand ${FOCUS}`}
              >
                {t.input.exampleClaimLabel}
              </button>
            </div>
          </div>
        )}

        {formError && (
          <p role="alert" className="mt-4 flex items-start gap-2.5 rounded-xl border-2 border-anxin-risk-high bg-anxin-risk-high-bg px-4 py-3 text-base font-medium text-anxin-risk-high">
            <Icon name="cross" className="mt-0.5 h-5 w-5" />
            <span>{formError}</span>
          </p>
        )}

        {/* One primary action, full width at every size. The person only has
            to find one thing. */}
        <button
          type="submit"
          disabled={disabled || (tab === "screenshot" && ocrState.phase !== "review")}
          className={`mt-6 w-full rounded-xl bg-anxin-brand px-6 py-4 text-lg font-semibold text-white shadow-sm transition hover:bg-anxin-brand-dark disabled:cursor-not-allowed disabled:opacity-50 ${FOCUS}`}
        >
          {disabled ? t.input.submitting : tab === "screenshot" ? t.ocr.confirmAndCheck : t.input.submit}
        </button>
      </form>
    </section>
  );
}
