"use client";

import { useLanguage } from "@/lib/i18n";
import Icon from "./Icon";
import LanguageSwitch from "./LanguageSwitch";

/**
 * The one place the app commits to colour. A solid brand band gives Anxin an
 * identity the moment it loads and, more usefully, anchors the top of the
 * page so the off-white working area below reads as calm rather than blank.
 * Everything under this stays quiet on purpose -- risk colour has to be the
 * loudest thing on the results screen, and it cannot be if the chrome shouts.
 */
export default function Header() {
  const { t } = useLanguage();
  return (
    <header className="bg-anxin-brand text-white">
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-5 sm:px-6">
        <div className="flex items-center gap-3">
          <span
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/25"
            aria-hidden="true"
          >
            <Icon name="shield" className="h-6 w-6" strokeWidth={1.9} />
          </span>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">{t.app.name}</h1>
            <p className="text-sm leading-snug text-white/80">{t.app.tagline}</p>
          </div>
        </div>
        <LanguageSwitch />
      </div>

      <div className="mx-auto max-w-3xl px-4 pb-5 sm:px-6">
        <p className="flex items-start gap-2.5 rounded-xl bg-white/10 px-3.5 py-3 text-xs leading-relaxed text-white/90 ring-1 ring-white/15">
          <Icon name="sparkle" className="mt-0.5 h-4 w-4 text-white/70" />
          <span>{t.app.poweredBy}</span>
        </p>
      </div>
    </header>
  );
}
