"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { getCriterionLabels } from "@/lib/criteriaLabels";
import { ROUTES, STORAGE_KEYS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type {
  RecommendationResponse,
  ScoreCriterion,
  UserProfile,
} from "@/types/recommendation";

const ResultsMap = dynamic(
  () => import("@/components/maps/ResultsMap").then((mod) => mod.ResultsMap),
  {
    ssr: false,
    loading: () => (
      <div className="h-96 w-full animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
    ),
  }
);

const CRITERIA_ORDER: ScoreCriterion[] = [
  "deprem_guvenlik",
  "saglik",
  "egitim",
  "ulasim",
  "sosyal_yasam",
];

function scoreColor(score: number): string {
  if (score >= 65) return "text-success";
  if (score >= 40) return "text-warning";
  return "text-danger";
}

interface StoredResult {
  profile: UserProfile;
  response: RecommendationResponse;
}

function readStoredResult(): StoredResult | null {
  const rawResponse = window.sessionStorage.getItem(STORAGE_KEYS.recommendation);
  const rawProfile = window.sessionStorage.getItem(STORAGE_KEYS.profile);
  if (!rawResponse || !rawProfile) return null;
  try {
    return {
      response: JSON.parse(rawResponse) as RecommendationResponse,
      profile: JSON.parse(rawProfile) as UserProfile,
    };
  } catch {
    return null;
  }
}

export default function ComparePage() {
  const t = useTranslation();
  const [stored, setStored] = useState<StoredResult | null | undefined>(undefined);

  useEffect(() => {
    setStored(readStoredResult());
  }, []);

  if (stored === undefined) {
    return null;
  }

  if (stored === null || stored.response.top5.length === 0) {
    return (
      <>
        <Navbar />
        <main>
          <Container className="flex min-h-[50vh] flex-col items-center justify-center py-24 text-center">
            <h1 className="text-3xl font-bold text-dark">{t.results.emptyTitle}</h1>
            <p className="mt-3 max-w-md text-gray">{t.results.emptyBody}</p>
            <Link
              href={ROUTES.profile}
              className="mt-6 rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-white hover:bg-primary-dark"
            >
              {t.results.startProfile}
            </Link>
          </Container>
        </main>
        <Footer />
      </>
    );
  }

  const { profile, response } = stored;
  const labels = getCriterionLabels(t);
  const neighborhoods = response.top5;

  return (
    <>
      <Navbar />
      <main>
        <Container className="py-16">
          <h1 className="text-3xl font-bold text-dark sm:text-4xl">{t.compare.title}</h1>
          <p className="mt-3 text-lg text-gray">{t.compare.subtitle}</p>

          <div className="mt-8 overflow-x-auto rounded-2xl border border-slate-200">
            <table className="w-full min-w-[640px] border-collapse text-sm">
              <thead>
                <tr>
                  <th className="w-44 border-b border-slate-200 bg-slate-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray">
                    {t.compare.criterionColumn}
                  </th>
                  {neighborhoods.map((n) => (
                    <th
                      key={n.mahalle_id}
                      className="border-b border-slate-200 bg-slate-50 px-4 py-3 text-left align-bottom"
                    >
                      <p className="text-base font-bold text-dark">{n.mahalle_adi}</p>
                      <p className="text-xs font-normal text-gray">{n.ilce}</p>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-100">
                  <td className="px-4 py-3 text-sm font-semibold text-dark">
                    {t.compare.overallScore}
                  </td>
                  {neighborhoods.map((n) => (
                    <td key={n.mahalle_id} className="px-4 py-3 text-lg font-bold text-primary">
                      {Math.round(n.uygunluk_skoru)}
                    </td>
                  ))}
                </tr>
                {CRITERIA_ORDER.map((criterion) => (
                  <tr key={criterion} className="border-b border-slate-100">
                    <td className="px-4 py-3 text-sm text-gray">{labels[criterion]}</td>
                    {neighborhoods.map((n) => (
                      <td
                        key={n.mahalle_id}
                        className={cn(
                          "px-4 py-3 font-semibold",
                          scoreColor(n.score_breakdown[criterion])
                        )}
                      >
                        {Math.round(n.score_breakdown[criterion])}
                      </td>
                    ))}
                  </tr>
                ))}
                <tr>
                  <td className="px-4 py-3 text-sm text-gray">{t.compare.priceRow}</td>
                  {neighborhoods.map((n) => (
                    <td key={n.mahalle_id} className="px-4 py-3 text-dark">
                      {n.avg_m2_fiyat
                        ? `${n.avg_m2_fiyat.toLocaleString("tr-TR")} ${t.results.priceUnit}`
                        : t.results.noPriceData}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mt-6 text-xs italic text-gray">{neighborhoods[0]?.disclaimer}</p>

          <h2 className="mt-12 text-xl font-bold text-dark">{t.compare.mapTitle}</h2>
          <div className="mt-4">
            <ResultsMap
              neighborhoods={neighborhoods}
              office={
                profile.office_lat != null && profile.office_lon != null
                  ? { lat: profile.office_lat, lon: profile.office_lon }
                  : null
              }
            />
          </div>
        </Container>
      </main>
      <Footer />
    </>
  );
}
