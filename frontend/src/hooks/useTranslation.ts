"use client";

import { useLanguage, type Translations } from "@/contexts/LanguageContext";

/**
 * Returns the translation object for the current language.
 *
 * Usage:
 *   const t = useTranslation();
 *   t.hero.title
 *
 * No hardcoded strings should ever live in components — everything comes
 * from src/locales/{tr,en}.json through this hook.
 */
export function useTranslation(): Translations {
  const { t } = useLanguage();
  return t;
}
