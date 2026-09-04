"use client";

import { useRef, useState } from "react";
import { useLanguage } from "@/lib/i18n";
import { verifyContent, explainMeme } from "@/lib/api";
import type { MemeExplanation, VerificationReport } from "@/lib/types";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import InputPanel, { SubmitPayload } from "@/components/InputPanel";
import ProgressIndicator from "@/components/ProgressIndicator";
import ResultsPanel from "@/components/ResultsPanel";
import MemeResult from "@/components/MemeResult";
import ErrorState from "@/components/ErrorState";

type ViewState =
  | { kind: "input" }
  | { kind: "loading" }
  | { kind: "result"; report: VerificationReport }
  | { kind: "meme"; meme: MemeExplanation }
  | { kind: "error"; error: unknown };

export default function Home() {
  const { language, t } = useLanguage();
  const [view, setView] = useState<ViewState>({ kind: "input" });
  const lastPayload = useRef<SubmitPayload | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function runSubmit(payload: SubmitPayload) {
    lastPayload.current = payload;
    setView({ kind: "loading" });
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      if (payload.analysisMode === "meme") {
        const meme = await explainMeme(payload.content, controller.signal);
        setView({ kind: "meme", meme });
      } else {
        const report = await verifyContent(
          {
            input_mode: payload.inputMode,
            analysis_mode: payload.analysisMode,
            content: payload.content,
            ui_language: language,
          },
          controller.signal,
        );
        setView({ kind: "result", report });
      }
    } catch (error) {
      if (controller.signal.aborted) {
        setView({ kind: "input" });
        return;
      }
      setView({ kind: "error", error });
    }
  }

  function handleCancel() {
    abortRef.current?.abort();
    setView({ kind: "input" });
  }

  function handleRetry() {
    if (lastPayload.current) void runSubmit(lastPayload.current);
  }

  function handleNewCheck() {
    setView({ kind: "input" });
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6">
        {view.kind === "input" && <InputPanel onSubmit={runSubmit} disabled={false} />}
        {view.kind === "loading" && (
          <>
            <InputPanel onSubmit={() => {}} disabled />
            <div className="mt-4">
              <ProgressIndicator onCancel={handleCancel} />
            </div>
          </>
        )}
        {view.kind === "result" && <ResultsPanel report={view.report} onNewCheck={handleNewCheck} />}
        {view.kind === "meme" && <MemeResult meme={view.meme} onNewCheck={handleNewCheck} />}
        {view.kind === "error" && (
          <div className="space-y-4">
            <ErrorState error={view.error} onRetry={handleRetry} />
            <div className="text-center">
              <button
                type="button"
                onClick={handleNewCheck}
                className="text-sm font-medium text-anxin-brand underline underline-offset-2"
              >
                {t.results.newCheck}
              </button>
            </div>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
