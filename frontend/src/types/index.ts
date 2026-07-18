export type FamilyStatus = "single" | "couple" | "married" | "withChildren";
export type WorkArrangement = "remote" | "hybrid" | "office";
export type ImportanceLevel = "high" | "medium" | "low";

export interface OnboardingData {
  lifestyle: string[];
  familyStatus: FamilyStatus | null;
  childCount: number;
  childAges: number[];
  workArrangement: WorkArrangement | null;
  officeLocation: { lat: number; lng: number } | null;
  maxCommuteMinutes: number;
  preferenceImportance: Record<string, ImportanceLevel>;
  freeText: string;
}

export const initialOnboardingData: OnboardingData = {
  lifestyle: [],
  familyStatus: null,
  childCount: 0,
  childAges: [],
  workArrangement: null,
  officeLocation: null,
  maxCommuteMinutes: 30,
  preferenceImportance: {},
  freeText: "",
};

export interface UserPreferences {
  earthquakeSafety: number;
  transport: number;
  health: number;
  education: number;
  assemblyAreas: number;
  socialLife: number;
}

export interface NeighborhoodScore {
  slug: string;
  name: string;
  district: string;
  overallScore: number;
  criteriaScores: UserPreferences;
  explanation: string;
  latitude: number;
  longitude: number;
}
