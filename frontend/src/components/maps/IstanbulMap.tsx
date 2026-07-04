"use client";

import { MapPin } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { SAFETY_LEGEND_KEYS, SAFETY_LEGEND_COLORS } from "@/lib/constants";

/**
 * Dummy placeholder for the Istanbul earthquake-safety map.
 *
 * Deliberately isolated in its own file / own component so that swapping
 * this out for a real MapLibre implementation later touches nothing else
 * in the Hero section.
 */
export function IstanbulMap() {
  const t = useTranslation();
  const legend = t.hero.map.legend;

  return (
    <div className="relative aspect-[4/5] w-full max-w-md overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-100 via-blue-50 to-slate-100 shadow-xl sm:aspect-square lg:aspect-[4/5]">
      {/* Dummy map surface */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center">
        <MapPin className="h-10 w-10 text-primary/60" strokeWidth={1.5} />
        <p className="max-w-[70%] text-sm font-medium text-gray">
          {t.hero.map.placeholderLabel}
        </p>
        <p className="text-xs text-gray/70">{t.hero.map.placeholderNote}</p>
      </div>

      {/* Decorative dummy risk blobs */}
      <div className="pointer-events-none absolute -left-6 top-10 h-28 w-28 rounded-full bg-emerald-400/25 blur-2xl" />
      <div className="pointer-events-none absolute right-4 top-24 h-20 w-20 rounded-full bg-amber-400/25 blur-2xl" />
      <div className="pointer-events-none absolute bottom-16 left-10 h-24 w-24 rounded-full bg-red-400/20 blur-2xl" />

      {/* Legend card, floating bottom-right */}
      <div className="absolute bottom-4 right-4 w-48 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-lg backdrop-blur">
        <p className="text-xs font-semibold text-dark">
          {t.hero.map.legendTitle}
        </p>
        <ul className="mt-2 space-y-1.5">
          {SAFETY_LEGEND_KEYS.map((key) => (
            <li key={key} className="flex items-center gap-2 text-xs text-gray">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: SAFETY_LEGEND_COLORS[key] }}
              />
              {legend[key]}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
