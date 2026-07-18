"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { AutoGrowTextarea } from "@/components/ui/AutoGrowTextarea";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";
import { StepNavButtons } from "@/components/onboarding/StepNavButtons";

export function Step6FreeText() {
  const t = useTranslation();
  const { data, update } = useOnboarding();
  const s = t.onboarding.step6;

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-3xl font-bold text-dark">{s.title}</h2>
      <p className="mt-3 text-lg text-slate-600">{s.description}</p>

      <div className="mt-8">
        <AutoGrowTextarea
          value={data.freeText}
          onChange={(e) => update({ freeText: e.target.value })}
          placeholder={s.placeholder}
        />
      </div>

      <StepNavButtons />
    </div>
  );
}
