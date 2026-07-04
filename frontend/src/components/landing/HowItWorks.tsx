"use client";

import { UserPlus, SlidersHorizontal, MapPinned, ArrowRight } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const ICONS = [UserPlus, SlidersHorizontal, MapPinned];

export function HowItWorks() {
  const t = useTranslation();

  return (
    <Section id="how-it-works">
      <Container>
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold tracking-wide text-primary">
            {t.howItWorks.eyebrow}
          </p>
          <h2 className="mt-3 text-4xl font-bold text-dark">
            {t.howItWorks.title}
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            {t.howItWorks.description}
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 items-center gap-6 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
          {t.howItWorks.steps.map((step, index) => {
            const Icon = ICONS[index];
            return (
              <div key={step.title} className="contents">
                <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm transition-shadow hover:shadow-md">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                    <Icon className="h-6 w-6 text-primary" strokeWidth={2} />
                  </div>
                  <h3 className="mt-5 text-lg font-semibold text-dark">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm text-gray">{step.description}</p>
                </div>

                {index < t.howItWorks.steps.length - 1 && (
                  <ArrowRight
                    className="mx-auto hidden h-6 w-6 shrink-0 rotate-90 text-slate-300 md:block md:rotate-0"
                    strokeWidth={2}
                  />
                )}
              </div>
            );
          })}
        </div>
      </Container>
    </Section>
  );
}
