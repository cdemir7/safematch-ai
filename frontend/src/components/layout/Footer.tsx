"use client";

import { Container } from "@/components/ui/Container";
import { useTranslation } from "@/hooks/useTranslation";
import { ROUTES } from "@/lib/constants";
import { ShieldCheck } from "lucide-react";
import Link from "next/link";

export function Footer() {
  const t = useTranslation();

  return (
    <footer className="border-t border-slate-200 bg-white">
      <Container className="flex flex-col gap-8 py-12 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-sm">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" strokeWidth={2.25} />
            <span className="text-base font-bold tracking-tight text-dark">
              {t.footer.brand}
            </span>
          </div>
          <p className="mt-3 text-sm text-gray">{t.footer.tagline}</p>
        </div>

        <nav className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-gray">
          <Link href={ROUTES.dataSources} className="hover:text-dark">
            {t.footer.dataSources}
          </Link>
          <Link href={ROUTES.about} className="hover:text-dark">
            {t.footer.about}
          </Link>
          <Link href={ROUTES.disclaimer} className="hover:text-dark">
            {t.footer.disclaimer}
          </Link>
        </nav>
      </Container>

      <Container className="border-t border-slate-100 py-6 text-xs text-gray">
        © {new Date().getFullYear()} {t.footer.brand}. {t.footer.rights}
      </Container>
    </footer>
  );
}
