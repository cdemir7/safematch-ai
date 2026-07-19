"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Car, Check, ChevronDown, Ship, TrainFront, TriangleAlert } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { getCriterionLabels } from "@/lib/criteriaLabels";
import { getMatchTicks } from "@/lib/matchTicks";
import { cn } from "@/lib/utils";
import { ScoreBar } from "@/components/results/ScoreBar";
import type {
  NeighborhoodResult,
  OfisUlasimModu,
  UserProfile,
} from "@/types/recommendation";

interface NeighborhoodCardProps {
  result: NeighborhoodResult;
  profile: UserProfile;
  rank?: number;
}

const COMMUTE_MODE_ICON: Record<OfisUlasimModu, typeof Car> = {
  karayolu: Car,
  raylı_sistem: TrainFront,
  vapur: Ship,
};

export function NeighborhoodCard({ result, profile, rank }: NeighborhoodCardProps) {
  const t = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const labels = getCriterionLabels(t);
  const ticks = getMatchTicks(profile, result);

  const price = result.avg_m2_fiyat
    ? `${result.avg_m2_fiyat.toLocaleString("tr-TR")} ${t.results.priceUnit}`
    : t.results.noPriceData;

  const commuteMode = result.raw.ofis_ulasim_modu;
  const CommuteModeIcon = commuteMode ? COMMUTE_MODE_ICON[commuteMode] : null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-slate-300">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          {rank !== undefined && (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-soft text-sm font-bold text-primary">
              {rank}
            </div>
          )}
          <div>
            <p className="text-lg font-bold text-dark">{result.mahalle_adi}</p>
            <p className="text-sm text-gray">{result.ilce}</p>
          </div>
        </div>

        <div className="shrink-0 text-right">
          <p className="text-2xl font-bold text-primary">
            {Math.round(result.uygunluk_skoru)}
          </p>
          <p className="text-xs text-gray">{t.results.scoreLabel}</p>
        </div>
      </div>

      {ticks.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {ticks.map((tick) => (
            <span
              key={tick.criterion}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium",
                tick.tone === "positive"
                  ? "border-success/30 bg-success-soft text-success-dark"
                  : "border-warning/30 bg-warning-soft text-warning"
              )}
            >
              {tick.tone === "positive" ? (
                <Check className="h-3.5 w-3.5" strokeWidth={3} />
              ) : (
                <TriangleAlert className="h-3.5 w-3.5" strokeWidth={2.5} />
              )}
              {(tick.tone === "positive"
                ? t.results.matchTickPositive
                : t.results.matchTickWarning
              ).replace("{criterion}", labels[tick.criterion])}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-gray">
          {t.results.priceLabel}: <span className="font-medium text-dark">{price}</span>
          {result.raw.ofis_tahmini_sure_dk != null && (
            <>
              {" · "}
              {t.results.commuteLabel}:{" "}
              <span className="inline-flex items-center gap-1 font-medium text-dark">
                {CommuteModeIcon && <CommuteModeIcon className="h-3.5 w-3.5" />}
                ~{Math.round(result.raw.ofis_tahmini_sure_dk)} dk
                {commuteMode && ` (${t.results.commuteModeLabels[commuteMode]})`}
              </span>
            </>
          )}
        </span>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="inline-flex items-center gap-1 font-medium text-primary hover:text-primary-dark"
        >
          {expanded ? t.results.collapseLabel : t.results.expandLabel}
          <ChevronDown
            className={cn("h-4 w-4 transition-transform", expanded && "rotate-180")}
          />
        </button>
      </div>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="mt-5 grid grid-cols-1 gap-3 border-t border-slate-100 pt-5 sm:grid-cols-2">
              {(Object.keys(labels) as (keyof typeof labels)[]).map((criterion) => (
                <ScoreBar
                  key={criterion}
                  label={labels[criterion]}
                  score={result.score_breakdown[criterion]}
                />
              ))}
            </div>

            {result.ai_aciklama && (
              <div className="mt-5 rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray">
                  {t.results.aiExplanationLabel}
                </p>
                <p className="mt-1.5 text-sm text-dark">{result.ai_aciklama}</p>
              </div>
            )}

            <p className="mt-4 text-xs italic text-gray">{result.disclaimer}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
