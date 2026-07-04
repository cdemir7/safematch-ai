"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { Container } from "@/components/ui/Container";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

export function ComingSoon({ title, body }: { title: string; body: string }) {
  const t = useTranslation();
  void t; // ensures this stays inside the translation-provided tree

  return (
    <>
      <Navbar />
      <main>
        <Container className="flex min-h-[50vh] flex-col items-center justify-center py-24 text-center">
          <h1 className="text-4xl font-bold text-dark">{title}</h1>
          <p className="mt-4 max-w-xl text-lg text-slate-600">{body}</p>
        </Container>
      </main>
      <Footer />
    </>
  );
}
