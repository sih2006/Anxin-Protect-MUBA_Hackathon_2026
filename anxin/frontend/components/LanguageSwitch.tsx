"use client";

import { useLanguage } from "@/lib/i18n";

export default function LanguageSwitch() {
  const { language, setLanguage, t } = useLanguage();
  const other = language === "en" ? "zh" : "en";

  return (
    <button
      type="button"
      onClick={() => setLanguage(other)}
      className="shrink-0 rounded-full bg-white/15 px-4 py-2 text-sm font-semibold text-white ring-1 ring-white/30 transition hover:bg-white/25 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
      aria-label={`${t.nav.languageLabel}: ${t.nav.switchToZh}`}
    >
      {t.nav.switchToZh}
    </button>
  );
}
