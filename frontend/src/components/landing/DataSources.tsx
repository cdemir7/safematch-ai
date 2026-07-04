"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

export function DataSources() {
  const t = useTranslation();

  return (
    <Section>
      <Container>
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold tracking-wide text-primary">
            {t.dataSources.eyebrow}
          </p>
          <h2 className="mt-3 text-4xl font-bold text-dark">
            {t.dataSources.title}
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            {t.dataSources.description}
          </p>
        </div>

        <div className="mt-14 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {t.dataSources.sources.map((source) => (
            <div
              key={source}
              className="flex h-20 items-center justify-center rounded-xl border border-slate-200 bg-white text-sm font-semibold text-gray"
            >
              {source}
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
