"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "@/hooks/useTranslation";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";
import { ROUTES, STORAGE_KEYS } from "@/lib/constants";
import { getRecommendations } from "@/lib/api";
import { toUserProfile } from "@/lib/profileMapping";

const MESSAGE_INTERVAL_MS = 1400;
const MIN_DISPLAY_MS = 2200;

export function Step8LoadingResult() {
  const t = useTranslation();
  const router = useRouter();
  const { data } = useOnboarding();
  const messages = t.onboarding.step8.loadingMessages;
  const [messageIndex, setMessageIndex] = useState(0);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % messages.length);
    }, MESSAGE_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [messages.length]);

  const criteriaLabels = t.onboarding.step5.criteria;

  const fetchRecommendations = useCallback(
    async (signal: { cancelled: boolean }) => {
      setError(false);
      const startedAt = Date.now();
      try {
        const profile = toUserProfile(data, criteriaLabels);
        const response = await getRecommendations(profile);

        const elapsed = Date.now() - startedAt;
        await new Promise((resolve) =>
          setTimeout(resolve, Math.max(MIN_DISPLAY_MS - elapsed, 0))
        );
        if (signal.cancelled) return;

        window.sessionStorage.setItem(
          STORAGE_KEYS.recommendation,
          JSON.stringify(response)
        );
        window.sessionStorage.setItem(
          STORAGE_KEYS.profile,
          JSON.stringify(profile)
        );
        router.push(ROUTES.results);
      } catch (err) {
        if (signal.cancelled) return;
        console.error("Failed to fetch recommendations", err);
        setError(true);
      }
    },
    [data, criteriaLabels, router]
  );

  useEffect(() => {
    const signal = { cancelled: false };
    fetchRecommendations(signal);
    return () => {
      signal.cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt]);

  if (error) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center text-center">
        <p className="text-lg font-semibold text-dark">{t.results.errorTitle}</p>
        <p className="mt-2 text-sm text-gray">{t.results.errorBody}</p>
        <button
          type="button"
          onClick={() => setAttempt((n) => n + 1)}
          className="mt-6 rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-white hover:bg-primary-dark"
        >
          {t.results.retry}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-md flex-col items-center text-center">
      <motion.div
        className="h-14 w-14 rounded-full border-4 border-slate-200 border-t-primary"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      />

      <div className="mt-6 h-6">
        <AnimatePresence mode="wait">
          <motion.p
            key={messageIndex}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            className="text-sm font-medium text-gray"
          >
            {messages[messageIndex]}
          </motion.p>
        </AnimatePresence>
      </div>
    </div>
  );
}
