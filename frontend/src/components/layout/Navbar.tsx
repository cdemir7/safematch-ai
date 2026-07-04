"use client";

import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { buttonVariants } from "@/components/ui/Button";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function Navbar() {
  const t = useTranslation();

  const links = [
    { href: ROUTES.howItWorks, label: t.navbar.howItWorks },
    { href: ROUTES.about, label: t.navbar.about },
    { href: ROUTES.dataSources, label: t.navbar.dataSources },
    { href: ROUTES.disclaimer, label: t.navbar.disclaimer },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/70 bg-white/70 backdrop-blur-md">
      <Container className="flex h-16 items-center justify-between">
        <Link href={ROUTES.home} className="flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-primary" strokeWidth={2.25} />
          <span className="text-lg font-bold tracking-tight text-dark">
            {t.navbar.logo}
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-gray transition-colors hover:text-dark"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <Link
            href={ROUTES.profile}
            className={cn(
              buttonVariants({ size: "sm" }),
              "hidden sm:inline-flex"
            )}
          >
            {t.navbar.cta}
          </Link>
        </div>
      </Container>
    </header>
  );
}
