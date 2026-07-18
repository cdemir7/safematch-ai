"use client";

import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/Button";
import { useTranslation } from "@/hooks/useTranslation";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";

export function StepNavButtons({ disabled }: { disabled?: boolean }) {
  const t = useTranslation();
  const { goNext } = useOnboarding();

  return (
    <div className="mt-10 flex justify-end">
      <button
        type="button"
        onClick={goNext}
        disabled={disabled}
        className={cn(buttonVariants({ size: "lg" }))}
      >
        {t.onboarding.next}
      </button>
    </div>
  );
}
