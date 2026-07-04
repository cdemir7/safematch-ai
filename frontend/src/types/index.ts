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
