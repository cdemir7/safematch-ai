"use client";

import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/Button";
import { useTranslation } from "@/hooks/useTranslation";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";

export function Step1Welcome() {
  const t = useTranslation();
  const { goNext } = useOnboarding();
  const s = t.onboarding.step1;

  return (
    <div className="mx-auto max-w-2xl text-center">
      <span className="inline-flex items-center rounded-full bg-success-soft px-4 py-1.5 text-xs font-semibold tracking-wide text-success-dark">
        {s.eyebrow}
      </span>

      <h1 className="mt-6 text-4xl font-bold tracking-tight text-dark sm:text-5xl">
        {s.title}
      </h1>

      <p className="mt-5 text-lg text-slate-600">{s.description}</p>

      <button
        type="button"
        onClick={goNext}
        className={cn(buttonVariants({ size: "lg" }), "mt-10")}
      >
        {s.cta}
      </button>
    </div>
  );
}
