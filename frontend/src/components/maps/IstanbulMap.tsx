"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { useTranslation } from "@/hooks/useTranslation";
import { SAFETY_LEGEND_KEYS, SAFETY_LEGEND_COLORS } from "@/lib/constants";
import { getMahalleler } from "@/lib/api";
import type { MahalleSummary } from "@/types/recommendation";

const ISTANBUL_CENTER: [number, number] = [41.0082, 28.9784];

function safetyColor(score: number): string {
  if (score >= 80) return SAFETY_LEGEND_COLORS.veryHigh;
  if (score >= 65) return SAFETY_LEGEND_COLORS.high;
  if (score >= 45) return SAFETY_LEGEND_COLORS.medium;
  if (score >= 30) return SAFETY_LEGEND_COLORS.low;
  return SAFETY_LEGEND_COLORS.veryLow;
}

/**
 * Landing page'deki genel İstanbul haritası. Kullanıcı profili doldurmadan
 * GET /api/v1/mahalleler'dan gelen 968 mahallenin tamamını deprem güvenlik
 * skoruna göre renkli gösterir — dekoratif/atmosfer amaçlıdır, kişiye özel
 * öneriden bağımsızdır (o, /compare haritasında).
 */
export function IstanbulMap() {
  const t = useTranslation();
  const legend = t.hero.map.legend;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [panning, setPanning] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getMahalleler()
      .then((res) => {
        if (cancelled || !containerRef.current || mapRef.current) return;
        renderMap(containerRef.current, res.mahalleler);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    function renderMap(el: HTMLDivElement, mahalleler: MahalleSummary[]) {
      const map = L.map(el, {
        center: ISTANBUL_CENTER,
        zoom: 10,
        scrollWheelZoom: false,
        zoomControl: true,
      });
      mapRef.current = map;
      el.classList.add("safematch-neon-map");

      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_matter/{z}/{x}/{y}{r}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
          maxZoom: 19,
        }
      ).addTo(map);

      for (const m of mahalleler) {
        if (!m.geometry || Object.keys(m.geometry).length === 0) continue;
        const color = safetyColor(m.deprem_guvenlik);
        L.geoJSON(m.geometry as unknown as GeoJSON.GeoJsonObject, {
          style: {
            color,
            weight: 1,
            fillColor: color,
            fillOpacity: 0.5,
            className: "safematch-neon-path",
          },
        })
          .bindPopup(`<strong>${m.mahalle_adi}</strong> (${m.ilce})`)
          .addTo(map);
      }

      map.on("movestart", () => setPanning(true));
      map.on("moveend", () => setPanning(false));

      const resizeObserver = new ResizeObserver(() => map.invalidateSize());
      resizeObserver.observe(el);
    }

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  return (
    <div className="relative aspect-[4/5] w-full max-w-md overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 shadow-2xl shadow-primary/10 sm:aspect-square lg:aspect-[4/5]">
      <div ref={containerRef} className="absolute inset-0" />

      {status !== "ready" && (
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-center">
          <p className="max-w-[70%] text-sm font-medium text-slate-300">
            {t.hero.map.placeholderLabel}
          </p>
          <p className="text-xs text-slate-500">
            {status === "error" ? t.hero.map.loadErrorNote : t.hero.map.placeholderNote}
          </p>
        </div>
      )}

      {status === "ready" && (
        <div
          className={`pointer-events-none absolute left-1/2 top-3 z-[1000] w-fit -translate-x-1/2 rounded-full border border-slate-700 bg-slate-900/90 px-3 py-1.5 shadow-lg backdrop-blur transition-opacity duration-200 ${
            panning ? "opacity-0" : "opacity-100"
          }`}
        >
          <ul className="flex items-center gap-2.5">
            {SAFETY_LEGEND_KEYS.map((key) => (
              <li key={key} className="flex items-center gap-1 text-[10px] text-slate-400">
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{
                    backgroundColor: SAFETY_LEGEND_COLORS[key],
                    boxShadow: `0 0 4px ${SAFETY_LEGEND_COLORS[key]}`,
                  }}
                />
                {legend[key]}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
