"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { useTranslation } from "@/hooks/useTranslation";

const ISTANBUL_CENTER: [number, number] = [41.0082, 28.9784];
const LEAFLET_VERSION = "1.9.4";
const ICON_BASE = `https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist/images`;

// Bundlers that don't process Leaflet's CSS `url()`s (Webpack/Next included)
// break its default marker icon lookup — point it at the CDN explicitly
// instead of relying on the package's relative image paths.
const markerIcon = L.icon({
  iconUrl: `${ICON_BASE}/marker-icon.png`,
  iconRetinaUrl: `${ICON_BASE}/marker-icon-2x.png`,
  shadowUrl: `${ICON_BASE}/marker-shadow.png`,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export interface LatLng {
  lat: number;
  lng: number;
}

interface OfficeLocationMapProps {
  value: LatLng | null;
  onChange: (location: LatLng) => void;
}

export function OfficeLocationMap({ value, onChange }: OfficeLocationMapProps) {
  const t = useTranslation();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [address, setAddress] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);

  // Init map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: value ? [value.lat, value.lng] : ISTANBUL_CENTER,
      zoom: value ? 14 : 10,
      scrollWheelZoom: false,
    });
    mapRef.current = map;

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);

    map.on("click", (e: L.LeafletMouseEvent) => {
      const loc = { lat: e.latlng.lat, lng: e.latlng.lng };
      placeMarker(loc);
      onChangeRef.current(loc);
    });

    if (value) {
      placeMarker(value);
    }

    const resizeObserver = new ResizeObserver(() => map.invalidateSize());
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function placeMarker(loc: LatLng) {
    const map = mapRef.current;
    if (!map) return;
    if (markerRef.current) {
      markerRef.current.setLatLng(loc);
    } else {
      markerRef.current = L.marker(loc, { icon: markerIcon, draggable: true }).addTo(map);
      markerRef.current.on("dragend", () => {
        const pos = markerRef.current!.getLatLng();
        const dragged = { lat: pos.lat, lng: pos.lng };
        onChangeRef.current(dragged);
      });
    }
  }

  // Reverse-geocode whenever the picked point changes.
  useEffect(() => {
    if (!value) {
      setAddress(null);
      return;
    }
    const controller = new AbortController();
    setResolving(true);
    setAddress(null);

    fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${value.lat}&lon=${value.lng}&zoom=14`,
      { signal: controller.signal }
    )
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.display_name) setAddress(data.display_name);
      })
      .catch(() => {
        // Best-effort only — coordinates are already captured either way.
      })
      .finally(() => setResolving(false));

    return () => controller.abort();
  }, [value?.lat, value?.lng]);

  return (
    <div>
      <div
        ref={containerRef}
        className="h-64 w-full overflow-hidden rounded-xl border border-slate-200"
      />
      <p className="mt-2 text-xs text-gray">
        {value
          ? resolving
            ? t.onboarding.step4.resolvingAddress
            : address ?? t.onboarding.step4.addressUnavailable
          : t.onboarding.step4.mapClickHint}
      </p>
    </div>
  );
}
