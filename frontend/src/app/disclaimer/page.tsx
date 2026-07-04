"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { ComingSoon } from "@/components/shared/ComingSoon";

export default function DisclaimerPage() {
  const t = useTranslation();
  return (
    <ComingSoon
      title={t.pages.disclaimer.title}
      body={t.pages.disclaimer.body}
    />
  );
}
