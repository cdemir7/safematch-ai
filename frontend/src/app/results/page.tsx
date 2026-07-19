"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { NeighborhoodCard } from "@/components/results/NeighborhoodCard";
import { ROUTES, STORAGE_KEYS } from "@/lib/constants";
import type { RecommendationResponse, UserProfile } from "@/types/recommendation";

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

export default function ResultsPage() {
  const t = useTranslation();
  const [stored, setStored] = useState<StoredResult | null | undefined>(undefined);

  useEffect(() => {
    setStored(readStoredResult());
  }, []);

  if (stored === undefined) {
    return null;
  }

  if (stored === null) {
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

  return (
    <>
      <Navbar />
      <main>
        <Container className="py-16">
          <h1 className="text-3xl font-bold text-dark sm:text-4xl">{t.results.title}</h1>
          <p className="mt-3 text-lg text-gray">{t.results.subtitle}</p>
          <p className="mt-1 text-sm text-gray">
            {t.results.totalConsidered.replace(
              "{count}",
              String(response.total_considered)
            )}
            {" · "}
            {response.weight_source === "ai"
              ? t.results.weightSourceAi
              : t.results.weightSourceRuleBased}
          </p>

          <h2 className="mt-10 text-xl font-bold text-dark">{t.results.topPicksTitle}</h2>
          <div className="mt-4 space-y-4">
            {response.top5.map((result, index) => (
              <NeighborhoodCard
                key={result.mahalle_id}
                result={result}
                profile={profile}
                rank={index + 1}
              />
            ))}
          </div>

          {response.alternatifler.length > 0 && (
            <>
              <h2 className="mt-12 text-xl font-bold text-dark">
                {t.results.alternativesTitle}
              </h2>
              <div className="mt-4 space-y-4">
                {response.alternatifler.map((result) => (
                  <NeighborhoodCard key={result.mahalle_id} result={result} profile={profile} />
                ))}
              </div>
            </>
          )}
        </Container>
      </main>
      <Footer />
    </>
  );
}
