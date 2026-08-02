"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import L from "leaflet";
import { useTranslation } from "@/hooks/useTranslation";
import { SAFETY_LEGEND_KEYS, SAFETY_LEGEND_COLORS } from "@/lib/constants";
import type { NeighborhoodResult } from "@/types/recommendation";

const ISTANBUL_CENTER: [number, number] = [41.0082, 28.9784];
const LEAFLET_VERSION = "1.9.4";
const ICON_BASE = `https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/images`;

// bkz. onboarding/OfficeLocationMap.tsx — bundler'lar Leaflet'in varsayılan
// marker ikonunu bulamadığı için CDN'den açıkça besleniyor.
const officeIcon = L.icon({
  iconUrl: `${ICON_BASE}/marker-icon.png`,
  iconRetinaUrl: `${ICON_BASE}/marker-icon-2x.png`,
  shadowUrl: `${ICON_BASE}/marker-shadow.png`,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

interface ResultsMapProps {
  neighborhoods: NeighborhoodResult[];
  office: { lat: number; lon: number } | null;
}

function safetyColor(score: number): string {
  if (score >= 80) return SAFETY_LEGEND_COLORS.veryHigh;
  if (score >= 65) return SAFETY_LEGEND_COLORS.high;
  if (score >= 45) return SAFETY_LEGEND_COLORS.medium;
  if (score >= 30) return SAFETY_LEGEND_COLORS.low;
  return SAFETY_LEGEND_COLORS.veryLow;
}

/**
 * Sonuç ekranındaki mahalle poligonlarını (deprem güvenlik skoruna göre
 * renkli) ve varsa girilen iş yeri konumunu tek bir Leaflet haritasında
 * gösterir. Backend her NeighborhoodResult'ta gerçek GeoJSON geometri
 * döndürdüğü için ek bir API çağrısı gerekmez.
 */
export function ResultsMap({ neighborhoods, office }: ResultsMapProps) {
  const t = useTranslation();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: ISTANBUL_CENTER,
      zoom: 11,
      scrollWheelZoom: false,
      zoomControl: true,
    });
    mapRef.current = map;

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);

    const boundsLayers: L.Layer[] = [];

    for (const n of neighborhoods) {
      if (!n.geometry || Object.keys(n.geometry).length === 0) continue;
      const score = n.score_breakdown.deprem_guvenlik;
      const color = safetyColor(score);
      const layer = L.geoJSON(n.geometry as unknown as GeoJSON.GeoJsonObject, {
        style: {
          color,
          weight: 2,
          fillColor: color,
          fillOpacity: 0.35,
        },
      }).bindPopup(
        `<strong>${n.mahalle_adi}</strong> (${n.ilce})<br/>` +
          `${Math.round(n.uygunluk_skoru)}/100 · deprem güvenlik: ${Math.round(score)}/100`
      );
      layer.addTo(map);
      boundsLayers.push(layer);
    }

    if (office) {
      const officeMarker = L.marker([office.lat, office.lon], { icon: officeIcon })
        .bindPopup(t.compare.officeMarkerLabel)
        .addTo(map);
      boundsLayers.push(officeMarker);
    }

    if (boundsLayers.length > 0) {
      const group = L.featureGroup(boundsLayers);
      map.fitBounds(group.getBounds().pad(0.15));
    }

    const resizeObserver = new ResizeObserver(() => map.invalidateSize());
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
    };
    // Harita bir kez kurulur; neighborhoods/office prop'ları sonuç ekranında
    // sayfa yaşam döngüsü boyunca değişmez.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className="h-96 w-full overflow-hidden rounded-2xl border border-slate-200"
      />
      <div className="absolute bottom-4 right-4 w-48 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-lg backdrop-blur">
        <p className="text-xs font-semibold text-dark">{t.hero.map.legendTitle}</p>
        <ul className="mt-2 space-y-1.5">
          {SAFETY_LEGEND_KEYS.map((key) => (
            <li key={key} className="flex items-center gap-2 text-xs text-gray">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: SAFETY_LEGEND_COLORS[key] }}
              />
              {t.hero.map.legend[key]}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
