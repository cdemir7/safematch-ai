import type { ImportanceLevel, OnboardingData } from "@/types";
import type { CalismaTipi, UserProfile } from "@/types/recommendation";

/**
 * The onboarding wizard collects fewer/different signals than the backend's
 * UserProfile (no explicit numeric budget or car-ownership question, and
 * step5's criteria labels don't line up 1:1 with the backend's five
 * priority sliders). This is a best-effort mapping, not a lossless one —
 * fields the wizard never asks about fall back to UserProfile's own
 * defaults (has_car=true, elderly_in_household=false, budget_m2=null).
 */

const IMPORTANCE_TO_PRIORITY: Record<ImportanceLevel, number> = {
  high: 5,
  medium: 3,
  low: 1,
};

function priorityFor(
  data: OnboardingData,
  criteriaLabels: readonly string[],
  index: number,
  fallback: number
): number {
  const label = criteriaLabels[index];
  const level = label ? data.preferenceImportance[label] : undefined;
  return level ? IMPORTANCE_TO_PRIORITY[level] : fallback;
}

const WORK_ARRANGEMENT_TO_CALISMA_TIPI: Record<
  NonNullable<OnboardingData["workArrangement"]>,
  CalismaTipi
> = {
  remote: "uzaktan",
  hybrid: "hibrit",
  office: "ofis",
};

/**
 * `criteriaLabels` must be `t.onboarding.step5.criteria` from the active
 * locale — Step5 keys `preferenceImportance` by those same label strings,
 * so the lookup has to use the same array, in the same order:
 * [Deprem Güvenliği, Yeşil Alan, Sosyal Yaşam, Ulaşım, Bütçe].
 */
export function toUserProfile(
  data: OnboardingData,
  criteriaLabels: readonly string[]
): UserProfile {
  const hasChildren = data.familyStatus === "withChildren";
  // Only "office" collects a pinned location today (Step4WorkArrangement) —
  // "hybrid"/"remote" have no map step, so there's nothing to send for them.
  const hasOfficePin = data.workArrangement === "office" && data.officeLocation;

  return {
    budget_m2: null,
    has_children: hasChildren,
    has_car: true,
    elderly_in_household: false,
    deprem_onceligi: priorityFor(data, criteriaLabels, 0, 4),
    saglik_onceligi: 3,
    egitim_onceligi: hasChildren ? 4 : 3,
    ulasim_onceligi: priorityFor(data, criteriaLabels, 3, 3),
    sosyal_onceligi: priorityFor(data, criteriaLabels, 2, 3),
    calisma_tipi: data.workArrangement
      ? WORK_ARRANGEMENT_TO_CALISMA_TIPI[data.workArrangement]
      : "hibrit",
    calisma_ilcesi: null,
    office_lat: hasOfficePin ? data.officeLocation!.lat : null,
    office_lon: hasOfficePin ? data.officeLocation!.lng : null,
    max_commute_minutes: hasOfficePin ? data.maxCommuteMinutes : null,
    free_text: data.freeText || null,
  };
}
