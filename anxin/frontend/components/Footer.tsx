"use client";

import { useLanguage } from "@/lib/i18n";

export default function Footer() {
  const { t } = useLanguage();
  return (
    <footer className="mt-10 border-t border-anxin-border py-6">
      <div className="mx-auto max-w-3xl px-4 text-center text-xs text-anxin-ink-muted sm:px-6">
        <p>{t.footer.disclaimer}</p>
        <p className="mt-1">{t.footer.trackNote}</p>
      </div>
    </footer>
  );
}
