import type { Translations } from "@/contexts/LanguageContext";
import type { ScoreCriterion } from "@/types/recommendation";

/**
 * All five ScoreBreakdown criteria have a localized label in t.criteria.items
 * (shared with the marketing page).
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
  };
}
