"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  initialOnboardingData,
  type OnboardingData,
} from "@/types";

export const TOTAL_STEPS = 8;

interface OnboardingContextValue {
  step: number;
  data: OnboardingData;
  update: (patch: Partial<OnboardingData>) => void;
  goNext: () => void;
  goBack: () => void;
  goToStep: (step: number) => void;
}

const OnboardingContext = createContext<OnboardingContextValue | undefined>(
  undefined
);

/**
 * Holds onboarding wizard state in memory for the duration of the flow.
 * Deliberately not persisted to localStorage/sessionStorage here — once the
 * FastAPI backend is wired up, submission happens step-by-step or on the
 * summary step instead of relying on client storage.
 */
export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<OnboardingData>(initialOnboardingData);

  const update = (patch: Partial<OnboardingData>) =>
    setData((prev) => ({ ...prev, ...patch }));

  const goNext = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  const goBack = () => setStep((s) => Math.max(s - 1, 1));
  const goToStep = (target: number) =>
    setStep(Math.min(Math.max(target, 1), TOTAL_STEPS));

  const value = useMemo<OnboardingContextValue>(
    () => ({ step, data, update, goNext, goBack, goToStep }),
    [step, data]
  );

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const ctx = useContext(OnboardingContext);
  if (!ctx) {
    throw new Error("useOnboarding must be used within an OnboardingProvider");
  }
  return ctx;
}
