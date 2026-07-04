"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import { cn } from "@/lib/utils";

export function LanguageSwitcher() {
  const { locale, setLocale } = useLanguage();

  return (
    <div className="flex items-center rounded-full border border-slate-200 bg-white p-0.5 text-sm font-medium">
      <button
        type="button"
        onClick={() => setLocale("tr")}
        aria-pressed={locale === "tr"}
        className={cn(
          "rounded-full px-3 py-1.5 transition-colors",
          locale === "tr"
            ? "bg-dark text-white"
            : "text-gray hover:text-dark"
        )}
      >
        TR
      </button>
      <button
        type="button"
        onClick={() => setLocale("en")}
        aria-pressed={locale === "en"}
        className={cn(
          "rounded-full px-3 py-1.5 transition-colors",
          locale === "en"
            ? "bg-dark text-white"
            : "text-gray hover:text-dark"
        )}
      >
        EN
      </button>
    </div>
  );
}
