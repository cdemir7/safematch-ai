"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { ComingSoon } from "@/components/shared/ComingSoon";

export default function AboutPage() {
  const t = useTranslation();
  return <ComingSoon title={t.pages.about.title} body={t.pages.about.body} />;
}
