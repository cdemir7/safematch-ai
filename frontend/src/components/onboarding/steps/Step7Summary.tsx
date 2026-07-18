"use client";

import { X } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";
import { StepNavButtons } from "@/components/onboarding/StepNavButtons";

/**
 * Turns the collected onboarding state into an editable tag cloud. Each tag
 * removes itself (and its underlying data) on click, giving the "edit in
 * place" behavior the brief asks for without a separate edit mode.
 */
export function Step7Summary() {
  const t = useTranslation();
  const { data, update } = useOnboarding();
  const s = t.onboarding.step7;

  const tags = [
    ...data.lifestyle,
    data.familyStatus,
    data.workArrangement,
    ...Object.entries(data.preferenceImportance)
      .filter(([, level]) => level === "high")
      .map(([criterion]) => criterion),
  ].filter((tag): tag is string => Boolean(tag));

  const removeLifestyleTag = (tag: string) => {
    if (data.lifestyle.includes(tag)) {
      update({ lifestyle: data.lifestyle.filter((v) => v !== tag) });
    } else if (data.familyStatus === tag) {
      update({ familyStatus: null });
    } else if (data.workArrangement === tag) {
      update({ workArrangement: null });
    } else {
      const { [tag]: _removed, ...rest } = data.preferenceImportance;
      update({ preferenceImportance: rest });
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-3xl font-bold text-dark">{s.title}</h2>
      <p className="mt-3 text-lg text-slate-600">{s.description}</p>

      <div className="mt-8 flex flex-wrap gap-2">
        {tags.map((tag) => (
          <button
            key={tag}
            type="button"
            onClick={() => removeLifestyleTag(tag)}
            className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary-soft px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/10"
          >
            {tag}
            <X className="h-3.5 w-3.5" />
          </button>
        ))}
      </div>

      <StepNavButtons />
    </div>
  );
}
