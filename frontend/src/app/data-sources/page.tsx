"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { ComingSoon } from "@/components/shared/ComingSoon";

export default function DataSourcesPage() {
  const t = useTranslation();
  return (
    <ComingSoon
      title={t.pages.dataSources.title}
      body={t.pages.dataSources.body}
    />
  );
}
