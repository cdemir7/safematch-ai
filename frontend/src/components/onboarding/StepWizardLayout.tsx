"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { useOnboarding, TOTAL_STEPS } from "@/components/onboarding/OnboardingContext";
import { Step1Welcome } from "@/components/onboarding/steps/Step1Welcome";
import { Step2LifestyleProfile } from "@/components/onboarding/steps/Step2LifestyleProfile";
import { Step3FamilyStructure } from "@/components/onboarding/steps/Step3FamilyStructure";
import { Step4WorkArrangement } from "@/components/onboarding/steps/Step4WorkArrangement";
import { Step5Preferences } from "@/components/onboarding/steps/Step5Preferences";
import { Step6FreeText } from "@/components/onboarding/steps/Step6FreeText";
import { Step7Summary } from "@/components/onboarding/steps/Step7Summary";
import { Step8LoadingResult } from "@/components/onboarding/steps/Step8LoadingResult";

const STEPS = [
  Step1Welcome,
  Step2LifestyleProfile,
  Step3FamilyStructure,
  Step4WorkArrangement,
  Step5Preferences,
  Step6FreeText,
  Step7Summary,
  Step8LoadingResult,
];

/**
 * Step transition logic:
 * - Steps are keyed by index in AnimatePresence with `mode="wait"`, so the
 *   outgoing step fully exits before the next one enters — this avoids two
 *   steps overlapping and fighting for width on narrow screens.
 * - Each step slides in from the direction of travel (right when moving
 *   forward, left when moving back) and fades, which reads as "the wizard
 *   is a single continuous strip" rather than a stack of unrelated pages.
 * - The progress bar's width animates with a spring, not a linear tween,
 *   so it has a small settle at the end — this is the one place we spend
 *   an extra bit of motion polish, deliberately not repeated elsewhere.
 */
export function StepWizardLayout() {
  const t = useTranslation();
  const { step, goBack } = useOnboarding();
  const ActiveStep = STEPS[step - 1];
  const isFirstStep = step === 1;
  const isLoadingStep = step === TOTAL_STEPS;

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {!isLoadingStep && (
        <header className="sticky top-0 z-10 border-b border-slate-200/70 bg-white/80 backdrop-blur-md">
          <Container className="flex h-16 items-center gap-4">
            <button
              type="button"
              onClick={goBack}
              disabled={isFirstStep}
              aria-label={t.onboarding.back}
              className="flex h-9 w-9 items-center justify-center rounded-full text-gray transition-colors hover:bg-slate-100 disabled:pointer-events-none disabled:opacity-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>

            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-primary to-success"
                animate={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
                transition={{ type: "spring", stiffness: 120, damping: 20 }}
              />
            </div>

            <span className="shrink-0 text-xs font-medium text-gray">
              {step} / {TOTAL_STEPS}
            </span>
          </Container>
        </header>
      )}

      <main className="flex flex-1 items-center">
        <Container className="py-12">
          <AnimatePresence mode="wait" custom={step}>
            <motion.div
              key={step}
              custom={step}
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -24 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              <ActiveStep />
            </motion.div>
          </AnimatePresence>
        </Container>
      </main>
    </div>
  );
}
