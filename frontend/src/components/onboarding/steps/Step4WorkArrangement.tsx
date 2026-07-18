"use client";

import { AnimatePresence, motion } from "framer-motion";
import { MapPin } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { PillButton } from "@/components/ui/PillButton";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";
import { StepNavButtons } from "@/components/onboarding/StepNavButtons";
import type { WorkArrangement } from "@/types";

const COMMUTE_OPTIONS = [15, 30, 45, 60];

export function Step4WorkArrangement() {
  const t = useTranslation();
  const { data, update } = useOnboarding();
  const s = t.onboarding.step4;
  const showMap = data.workArrangement === "office";

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-3xl font-bold text-dark">{s.title}</h2>
      <p className="mt-3 text-lg text-slate-600">{s.description}</p>

      <div className="mt-8 flex flex-wrap gap-3">
        {s.options.map((option) => (
          <PillButton
            key={option.id}
            selected={data.workArrangement === option.id}
            onClick={() =>
              update({ workArrangement: option.id as WorkArrangement })
            }
          >
            {option.label}
          </PillButton>
        ))}
      </div>

      <AnimatePresence initial={false}>
        {showMap && (
          <motion.div
            key="office-map"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
              <p className="text-sm font-medium text-dark">{s.mapPrompt}</p>
              {/* Minimal MapLibre placeholder — swapped for a real pin-drop
                  map when the maps integration lands. */}
              <div className="mt-3 flex h-40 items-center justify-center rounded-xl border border-dashed border-slate-300 bg-gradient-to-br from-primary-soft to-success-soft">
                <MapPin className="h-6 w-6 text-primary/60" />
              </div>

              <label className="mt-6 block text-sm font-medium text-dark">
                {s.commuteLabel}
              </label>
              <div className="mt-3 flex flex-wrap gap-2">
                {COMMUTE_OPTIONS.map((minutes) => (
                  <PillButton
                    key={minutes}
                    selected={data.maxCommuteMinutes === minutes}
                    onClick={() => update({ maxCommuteMinutes: minutes })}
                  >
                    {minutes} dk
                  </PillButton>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <StepNavButtons disabled={!data.workArrangement} />
    </div>
  );
}
