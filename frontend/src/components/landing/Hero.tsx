"use client";

import Link from "next/link";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { buttonVariants } from "@/components/ui/Button";
import { IstanbulMap } from "@/components/maps/IstanbulMap";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function Hero() {
  const t = useTranslation();

  return (
    <section className="relative overflow-hidden pb-20 pt-16 sm:pb-28 sm:pt-24">
      <Container className="grid grid-cols-1 items-center gap-16 lg:grid-cols-2">
        {/* Left column */}
        <div>
          <span className="inline-flex items-center rounded-full bg-primary/10 px-4 py-1.5 text-xs font-semibold tracking-wide text-primary">
            {t.hero.badge}
          </span>

          <h1 className="mt-6 text-5xl font-bold tracking-tight text-dark sm:text-6xl">
            {t.hero.titleLine1}
            {t.hero.titleLine2Prefix ? (
              <>
                <br />
                {t.hero.titleLine2Prefix}{" "}
              </>
            ) : (
              " "
            )}
            <span className="bg-gradient-to-r from-primary to-sky-400 bg-clip-text text-transparent">
              {t.hero.titleHighlight}
            </span>
          </h1>

          <p className="mt-6 max-w-lg text-lg text-slate-600">
            {t.hero.description}
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link href={ROUTES.profile} className={buttonVariants({ size: "lg" })}>
              {t.hero.primaryCta}
            </Link>
            <Link
              href={ROUTES.howItWorks}
              className={cn(buttonVariants({ variant: "secondary", size: "lg" }))}
            >
              {t.hero.secondaryCta}
            </Link>
          </div>

          <div className="mt-10 flex flex-wrap items-center gap-3">
            {t.hero.sourceTags.map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-gray"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div className="flex justify-center lg:justify-end">
          <IstanbulMap />
        </div>
      </Container>
    </section>
  );
}
