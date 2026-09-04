"use client";

import { useLanguage } from "@/lib/i18n";
import LanguageSwitch from "./LanguageSwitch";

export default function Header() {
  const { t } = useLanguage();
  return (
    <header className="border-b border-anxin-border bg-anxin-surface">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 sm:px-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-anxin-brand-dark">{t.app.name}</h1>
          <p className="text-sm text-anxin-ink-muted">{t.app.tagline}</p>
        </div>
        <LanguageSwitch />
      </div>
      <div className="mx-auto max-w-3xl px-4 pb-3 sm:px-6">
        <p className="rounded-lg bg-anxin-brand-soft px-3 py-2 text-xs text-anxin-brand-dark">
          {t.app.poweredBy}
        </p>
      </div>
    </header>
  );
}
