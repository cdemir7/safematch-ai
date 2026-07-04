"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { ComingSoon } from "@/components/shared/ComingSoon";

export default function ProfilePage() {
  const t = useTranslation();
  return (
    <ComingSoon
      title={t.pages.comingSoon.title}
      body={t.pages.comingSoon.body}
    />
  );
}
