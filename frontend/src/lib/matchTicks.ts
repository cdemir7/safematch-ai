import type {
  NeighborhoodResult,
  ScoreCriterion,
  UserProfile,
} from "@/types/recommendation";

export type MatchTickTone = "positive" | "warning";

export interface MatchTick {
  criterion: ScoreCriterion;
  tone: MatchTickTone;
  score: number;
}

const STRONG_SCORE = 65;
const WEAK_SCORE = 40;
const HIGH_PRIORITY = 4; // 1-5 slider, >=4 counts as "user cares about this"

const PRIORITY_BY_CRITERION: Record<
  Exclude<ScoreCriterion, "yasam_kalitesi">,
  keyof UserProfile
> = {
  deprem_guvenlik: "deprem_onceligi",
  saglik: "saglik_onceligi",
  egitim: "egitim_onceligi",
  ulasim: "ulasim_onceligi",
  sosyal_yasam: "sosyal_onceligi",
};

/**
 * Turns "what the user said mattered" + "how this neighborhood actually
 * scored" into a short checklist for a result card. Earthquake safety is
 * always evaluated regardless of the user's slider — SafeMatch's core rule
 * is that it's never allowed to be ignored (CLAUDE.md §2.1).
 */
export function getMatchTicks(
  profile: UserProfile,
  result: NeighborhoodResult
): MatchTick[] {
  const ticks: MatchTick[] = [];
  const sb = result.score_breakdown;

  for (const [criterion, priorityField] of Object.entries(
    PRIORITY_BY_CRITERION
  ) as [Exclude<ScoreCriterion, "yasam_kalitesi">, keyof UserProfile][]) {
    const priority = profile[priorityField] as number;
    const isPriority = criterion === "deprem_guvenlik" || priority >= HIGH_PRIORITY;
    if (!isPriority) continue;

    const score = sb[criterion];
    if (score >= STRONG_SCORE) {
      ticks.push({ criterion, tone: "positive", score });
    } else if (score < WEAK_SCORE) {
      ticks.push({ criterion, tone: "warning", score });
    }
  }

  return ticks.sort((a, b) => (a.tone === b.tone ? 0 : a.tone === "positive" ? -1 : 1));
}
