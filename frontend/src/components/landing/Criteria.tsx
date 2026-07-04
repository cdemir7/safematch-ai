"use client";

import {
  ShieldAlert,
  Bus,
  HeartPulse,
  GraduationCap,
  Users,
  Trees,
} from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const ICONS = [ShieldAlert, Bus, HeartPulse, GraduationCap, Users, Trees];

export function Criteria() {
  const t = useTranslation();

  return (
    <Section className="bg-white">
      <Container>
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold tracking-wide text-primary">
            {t.criteria.eyebrow}
          </p>
          <h2 className="mt-3 text-4xl font-bold text-dark">
            {t.criteria.title}
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            {t.criteria.description}
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {t.criteria.items.map((item, index) => {
            const Icon = ICONS[index];
            return (
              <div
                key={item.title}
                className="rounded-2xl border border-slate-200 bg-background p-8 transition-shadow hover:shadow-md"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                  <Icon className="h-6 w-6 text-primary" strokeWidth={2} />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-dark">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm text-gray">{item.description}</p>
              </div>
            );
          })}
        </div>
      </Container>
    </Section>
  );
}
