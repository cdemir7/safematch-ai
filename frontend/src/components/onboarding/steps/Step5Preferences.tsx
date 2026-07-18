"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { PillButton } from "@/components/ui/PillButton";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";
import { StepNavButtons } from "@/components/onboarding/StepNavButtons";
import type { ImportanceLevel } from "@/types";

const LEVELS: ImportanceLevel[] = ["high", "medium", "low"];

export function Step5Preferences() {
  const t = useTranslation();
  const { data, update } = useOnboarding();
  const s = t.onboarding.step5;

  const setLevel = (criterion: string, level: ImportanceLevel) =>
    update({
      preferenceImportance: { ...data.preferenceImportance, [criterion]: level },
    });

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-3xl font-bold text-dark">{s.title}</h2>
      <p className="mt-3 text-lg text-slate-600">{s.description}</p>

      <div className="mt-8 space-y-5">
        {s.criteria.map((criterion) => (
          <div
            key={criterion}
            className="rounded-2xl border border-slate-200 bg-white p-5"
          >
            <p className="text-sm font-semibold text-dark">{criterion}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {LEVELS.map((level, index) => (
                <PillButton
                  key={level}
                  selected={data.preferenceImportance[criterion] === level}
                  onClick={() => setLevel(criterion, level)}
                >
                  {s.importance[index]}
                </PillButton>
              ))}
            </div>
          </div>
        ))}
      </div>

      <StepNavButtons />
    </div>
  );
}
