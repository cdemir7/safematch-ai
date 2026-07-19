/**
 * Types mirroring backend/app/schemas/profile.py and
 * backend/app/schemas/recommendation.py field-for-field (snake_case kept
 * on purpose — these cross the wire as-is via lib/api.ts).
 */

export type CalismaTipi = "ofis" | "hibrit" | "uzaktan";

export interface UserProfile {
  budget_m2?: number | null;
  has_children: boolean;
  has_car: boolean;
  elderly_in_household: boolean;
  deprem_onceligi: number;
  saglik_onceligi: number;
  egitim_onceligi: number;
  ulasim_onceligi: number;
  sosyal_onceligi: number;
  calisma_tipi: CalismaTipi;
  calisma_ilcesi?: string | null;
  office_lat?: number | null;
  office_lon?: number | null;
  max_commute_minutes?: number | null;
  free_text?: string | null;
}

export interface ScoreBreakdown {
  deprem_guvenlik: number;
  saglik: number;
  egitim: number;
  ulasim: number;
  sosyal_yasam: number;
  yasam_kalitesi: number;
}

export type ScoreCriterion = keyof ScoreBreakdown;

export type OfisUlasimModu = "karayolu" | "raylı_sistem" | "vapur";

export interface RawData {
  hastane_count: number;
  okul_count: number;
  cami_count: number;
  toplanma_count: number;
  ofis_mesafesi_km: number | null;
  ofis_tahmini_sure_dk: number | null;
  ofis_ulasim_modu: OfisUlasimModu | null;
}

export interface NeighborhoodResult {
  mahalle_id: string;
  mahalle_adi: string;
  ilce: string;
  uygunluk_skoru: number;
  score_breakdown: ScoreBreakdown;
  raw: RawData;
  avg_m2_fiyat: number | null;
  geometry: Record<string, unknown>;
  ai_aciklama: string | null;
  disclaimer: string;
}

export interface RecommendationResponse {
  top5: NeighborhoodResult[];
  alternatifler: NeighborhoodResult[];
  applied_weights: Record<string, number>;
  weight_source: "ai" | "rule_based";
  total_considered: number;
}
