"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { Language } from "./types";
import en from "./dictionaries/en";
import zh from "./dictionaries/zh";
import type { Dictionary } from "./dictionaries/types";

const dictionaries = { en, zh } as const;
export type { Dictionary };

/**
 * Keys of the results dictionary whose values are plain strings.
 *
 * The dictionary also holds formatter functions (e.g. modelGap(points)), so a
 * bare `keyof Dictionary["results"]` lets a component try to render a function
 * as a ReactNode. This narrows label lookups to the renderable keys, catching
 * that mistake at compile time instead of as a blank space in the UI.
 */
export type ResultsStringKey = {
  [K in keyof Dictionary["results"]]: Dictionary["results"][K] extends string ? K : never;
}[keyof Dictionary["results"]];

const STORAGE_KEY = "anxin-language";

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Dictionary;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

// UI-02: language switch works from day one across all core screens, with
// no reload and no hardcoded strings scattered through components -- every
// piece of UI chrome text is pulled from `t` (see dictionaries/en.ts, zh.ts).
export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (stored === "en" || stored === "zh") {
      setLanguageState(stored);
      return;
    }
    const browserPrefersZh = typeof navigator !== "undefined" && /^zh/i.test(navigator.language ?? "");
    if (browserPrefersZh) setLanguageState("zh");
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // localStorage can be unavailable (private browsing, disabled storage) -- language
      // still works for this session, it just won't persist. Never crash the UI for this.
    }
  };

  const value = useMemo<LanguageContextValue>(
    () => ({ language, setLanguage, t: dictionaries[language] }),
    [language],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}

/** Pick the EN/ZH field of a bilingual API payload based on current UI language. */
export function pickBilingual(language: Language, en_: string, zh_: string): string {
  return language === "zh" ? zh_ : en_;
}
