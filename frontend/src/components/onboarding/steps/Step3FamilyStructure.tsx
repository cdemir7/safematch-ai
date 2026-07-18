"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "@/hooks/useTranslation";
import { PillButton } from "@/components/ui/PillButton";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";
import { StepNavButtons } from "@/components/onboarding/StepNavButtons";
import type { FamilyStatus } from "@/types";

/**
 * The children age-picker only exists in the DOM while "withChildren" is
 * selected. Animating `height: auto` directly causes jumpy transitions, so
 * we animate a wrapper's opacity + a small upward shift while grid-template-
 * rows handles the height (1fr <-> 0fr), which auto-sizes to content
 * without ever needing a fixed pixel height.
 */
export function Step3FamilyStructure() {
  const t = useTranslation();
  const { data, update } = useOnboarding();
  const s = t.onboarding.step3;
  const showChildren = data.familyStatus === "withChildren";

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-3xl font-bold text-dark">{s.title}</h2>
      <p className="mt-3 text-lg text-slate-600">{s.description}</p>

      <div className="mt-8 flex flex-wrap gap-3">
        {s.options.map((option) => (
          <PillButton
            key={option.id}
            selected={data.familyStatus === option.id}
            onClick={() => update({ familyStatus: option.id as FamilyStatus })}
          >
            {option.label}
          </PillButton>
        ))}
      </div>

      <AnimatePresence initial={false}>
        {showChildren && (
          <motion.div
            key="children-picker"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
              <label className="text-sm font-medium text-dark">
                {s.childCountLabel}
              </label>
              <div className="mt-3 flex gap-2">
                {[1, 2, 3, 4].map((count) => (
                  <PillButton
                    key={count}
                    selected={data.childCount === count}
                    onClick={() => update({ childCount: count })}
                  >
                    {count}
                  </PillButton>
                ))}
              </div>

              <label className="mt-6 block text-sm font-medium text-dark">
                {s.childAgeLabel}
              </label>
              <div className="mt-3 flex flex-wrap gap-2">
                {["0-3", "4-6", "7-12", "13-18"].map((range) => (
                  <PillButton key={range} selected={false}>
                    {range}
                  </PillButton>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <StepNavButtons disabled={!data.familyStatus} />
    </div>
  );
}
