export const SITE_NAME = "SafeMatch AI";

export const ROUTES = {
  home: "/",
  howItWorks: "/#how-it-works",
  about: "/about",
  dataSources: "/data-sources",
  disclaimer: "/disclaimer",
  profile: "/profile",
  results: "/results",
  compare: "/compare",
  neighborhood: (slug: string) => `/neighborhood/${slug}`,
} as const;

/** sessionStorage keys used to pass the recommendation result from the
 *  onboarding flow to the results page without a global store. */
export const STORAGE_KEYS = {
  recommendation: "safematch:recommendation",
  profile: "safematch:profile",
} as const;

export const SOCIAL_LINKS = {
  github: "https://github.com/",
  linkedin: "https://linkedin.com/",
} as const;

/**
 * Ordered to match the six criteria entries in the locale files
 * (src/locales/tr.json / en.json -> criteria.items).
 */
export const CRITERIA_ICON_KEYS = [
  "earthquake",
  "transport",
  "health",
  "education",
  "assembly",
  "social",
] as const;

/** Legend severity keys, ordered from safest to riskiest. */
export const SAFETY_LEGEND_KEYS = [
  "veryHigh",
  "high",
  "medium",
  "low",
  "veryLow",
] as const;

export const SAFETY_LEGEND_COLORS: Record<
  (typeof SAFETY_LEGEND_KEYS)[number],
  string
> = {
  veryHigh: "#10b981",
  high: "#84cc16",
  medium: "#f59e0b",
  low: "#f97316",
  veryLow: "#ef4444",
};
