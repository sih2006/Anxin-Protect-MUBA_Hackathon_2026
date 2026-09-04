"use client";

import { useLanguage } from "@/lib/i18n";

export default function LanguageSwitch() {
  const { language, setLanguage, t } = useLanguage();
  const other = language === "en" ? "zh" : "en";

  return (
    <button
      type="button"
      onClick={() => setLanguage(other)}
      className="rounded-full border border-anxin-border bg-anxin-surface px-4 py-2 text-sm font-medium text-anxin-ink shadow-sm transition hover:border-anxin-brand hover:text-anxin-brand"
      aria-label={`${t.nav.languageLabel}: ${t.nav.switchToZh}`}
    >
      {t.nav.switchToZh}
    </button>
  );
}
