"use client";

import {
  Home,
  Building2,
  Leaf,
  Briefcase,
  Users,
  Wallet,
} from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { BentoCard } from "@/components/ui/BentoCard";
import { useOnboarding } from "@/components/onboarding/OnboardingContext";
import { StepNavButtons } from "@/components/onboarding/StepNavButtons";

const ICONS = [Home, Building2, Leaf, Briefcase, Users, Wallet];

export function Step2LifestyleProfile() {
  const t = useTranslation();
  const { data, update } = useOnboarding();
  const s = t.onboarding.step2;

  const toggle = (id: string) => {
    const next = data.lifestyle.includes(id)
      ? data.lifestyle.filter((v) => v !== id)
      : [...data.lifestyle, id];
    update({ lifestyle: next });
  };

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-3xl font-bold text-dark">{s.title}</h2>
      <p className="mt-3 text-lg text-slate-600">{s.description}</p>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {s.options.map((option, index) => {
          const Icon = ICONS[index];
          return (
            <BentoCard
              key={option.id}
              icon={<Icon className="h-5 w-5" strokeWidth={2} />}
              title={option.title}
              description={option.description}
              selected={data.lifestyle.includes(option.id)}
              onClick={() => toggle(option.id)}
            />
          );
        })}
      </div>

      <StepNavButtons disabled={data.lifestyle.length === 0} />
    </div>
  );
}
