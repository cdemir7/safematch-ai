import type { Translations } from "@/contexts/LanguageContext";
import type { ScoreCriterion } from "@/types/recommendation";

/**
 * Five of the six ScoreBreakdown criteria already have a localized label in
 * t.criteria.items (shared with the marketing page); yasam_kalitesi is
 * results-page-only and lives in t.results instead.
 */
export function getCriterionLabels(
  t: Translations
): Record<ScoreCriterion, string> {
  return {
    deprem_guvenlik: t.criteria.items[0].title,
    ulasim: t.criteria.items[1].title,
    saglik: t.criteria.items[2].title,
    egitim: t.criteria.items[3].title,
    sosyal_yasam: t.criteria.items[5].title,
    yasam_kalitesi: t.results.yasamKalitesiLabel,
  };
}
