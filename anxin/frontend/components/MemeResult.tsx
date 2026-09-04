"use client";

import { useLanguage, pickBilingual } from "@/lib/i18n";
import type { MemeExplanation } from "@/lib/types";
import TransparencyPanel from "./TransparencyPanel";

/**
 * IMG-05: deliberately distinct visual language from ResultsPanel (violet
 * accent, no green/red risk colours, no Truth Score, no verdict word) so
 * this can never be mistaken for a fact-check "verified safe" result --
 * paired with an explicit disclaimer at the top.
 */
export default function MemeResult({ meme, onNewCheck }: { meme: MemeExplanation; onNewCheck: () => void }) {
  const { language, t } = useLanguage();

  return (
    <div className="space-y-4">
      <section className="rounded-xl2 border-2 border-dashed border-purple-300 bg-purple-50 p-5 shadow-sm sm:p-6">
        <h2 className="text-lg font-semibold text-purple-900">{t.meme.heading}</h2>
        <p role="note" className="mt-1 text-sm font-medium text-purple-700">
          {t.meme.disclaimer}
        </p>

        {meme.is_visual_only_limitation && (
          <p role="alert" className="mt-3 rounded-lg bg-white p-3 text-sm text-purple-800">
            {t.meme.visualOnlyWarning}
          </p>
        )}

        <div className="mt-4 space-y-4">
          <Block title={t.meme.literal} en={meme.literal_meaning_en} zh={meme.literal_meaning_zh} language={language} />
          <Block title={t.meme.joke} en={meme.joke_or_reference_en} zh={meme.joke_or_reference_zh} language={language} />
          <Block title={t.meme.culture} en={meme.cultural_context_en} zh={meme.cultural_context_zh} language={language} />
          <Block title={t.meme.safety} en={meme.safety_notes_en} zh={meme.safety_notes_zh} language={language} />
        </div>
      </section>

      <TransparencyPanel calls={[meme.meta]} />

      <div className="text-center">
        <button
          type="button"
          onClick={onNewCheck}
          className="rounded-full border border-anxin-border bg-anxin-surface px-5 py-2.5 text-sm font-medium text-anxin-ink hover:border-anxin-brand hover:text-anxin-brand"
        >
          {t.results.newCheck}
        </button>
      </div>
    </div>
  );
}

function Block({ title, en, zh, language }: { title: string; en: string; zh: string; language: "en" | "zh" }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-purple-900">{title}</h3>
      <p className="mt-1 rounded-lg bg-white p-3 text-sm text-anxin-ink" lang={language}>
        {pickBilingual(language, en, zh)}
      </p>
    </div>
  );
}
