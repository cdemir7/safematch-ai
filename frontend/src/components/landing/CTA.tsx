"use client";

import Link from "next/link";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { buttonVariants } from "@/components/ui/Button";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function CTA() {
  const t = useTranslation();

  return (
    <section className="py-20 sm:py-28">
      <Container>
        <div className="relative overflow-hidden rounded-3xl bg-dark px-8 py-16 text-center sm:px-16">
          <div className="pointer-events-none absolute -top-24 right-0 h-64 w-64 rounded-full bg-primary/30 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 left-0 h-64 w-64 rounded-full bg-sky-400/20 blur-3xl" />

          <h2 className="relative mx-auto max-w-2xl text-4xl font-bold tracking-tight text-white">
            {t.cta.title}
          </h2>

          <Link
            href={ROUTES.profile}
            className={cn(
              buttonVariants({ size: "lg" }),
              "relative mt-8 inline-flex"
            )}
          >
            {t.cta.button}
          </Link>
        </div>
      </Container>
    </section>
  );
}
