"""
02_fetch_poi.py
───────────────
Overpass API aracılığıyla İstanbul içindeki POI'leri indirir.

Kategoriler
-----------
  saglik   : hastane, klinik, sağlık ocağı
  egitim   : okul, üniversite, kolej, anaokulu
  toplanma : acil toplanma alanı, barınak, CAMİ (afet sonrası toplanma noktası)
  transit  : otobüs durağı, metro istasyonu, metrobüs, Marmaray, tramvay

Not: Camiler ayrı bir kategori değildir; afet sonrası toplanma noktası
     işlevi nedeniyle "toplanma" kategorisine dahildir.

Kaynak: OpenStreetMap / Overpass API (overpass-api.de)
Çıktı : data/poi_raw.json
         data/transit_raw.json  (ayrı dosya — büyük olabilir)

Kullanım
--------
    python scripts/02_fetch_poi.py

Lisans: OSM verileri ODbL lisansı altındadır.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
OUTPUT_POI     = DATA_DIR / "poi_raw.json"
OUTPUT_TRANSIT = DATA_DIR / "transit_raw.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# İstanbul bounding box (güney, batı, kuzey, doğu)
ISTANBUL_BBOX = "40.802, 27.996, 41.620, 29.960"

# ─────────────────────────────────────────────
# 1) POI sorgusu (saglik + egitim + toplanma)
# ─────────────────────────────────────────────
OVERPASS_POI_QL = f"""
[out:json][timeout:90];
(
  node[amenity=hospital]({ISTANBUL_BBOX});
  way[amenity=hospital]({ISTANBUL_BBOX});
  node[amenity=clinic]({ISTANBUL_BBOX});
  node[amenity=doctors]({ISTANBUL_BBOX});

  node[amenity=school]({ISTANBUL_BBOX});
  way[amenity=school]({ISTANBUL_BBOX});
  node[amenity=university]({ISTANBUL_BBOX});
  way[amenity=university]({ISTANBUL_BBOX});
  node[amenity=college]({ISTANBUL_BBOX});
  node[amenity=kindergarten]({ISTANBUL_BBOX});

  node[emergency=assembly_point]({ISTANBUL_BBOX});
  node[amenity=shelter]({ISTANBUL_BBOX});
  node[amenity=place_of_worship][religion=muslim]({ISTANBUL_BBOX});
  way[amenity=place_of_worship][religion=muslim]({ISTANBUL_BBOX});
);
out center;
""".strip()

# ─────────────────────────────────────────────
# 2) Transit sorgusu (otobüs + metro + metrobüs + Marmaray + tramvay)
# ─────────────────────────────────────────────
OVERPASS_TRANSIT_QL = f"""
[out:json][timeout:90];
(
  node[highway=bus_stop]({ISTANBUL_BBOX});
  node[amenity=bus_station]({ISTANBUL_BBOX});

  node[station=subway]({ISTANBUL_BBOX});
  way[station=subway]({ISTANBUL_BBOX});
  node[railway=subway_entrance]({ISTANBUL_BBOX});

  node[railway=station]({ISTANBUL_BBOX});
  node[railway=halt]({ISTANBUL_BBOX});

  node[railway=tram_stop]({ISTANBUL_BBOX});
  node[highway=platform]({ISTANBUL_BBOX});
);
out center;
""".strip()

# ─────────────────────────────────────────────
# OSM tag → SafeMatch kategori
# ─────────────────────────────────────────────

def _classify_poi(tags: dict) -> str:
    emergency = tags.get("emergency", "")
    amenity   = tags.get("amenity", "")
    religion  = tags.get("religion", "")

    if emergency == "assembly_point":
        return "toplanma"
    if amenity == "shelter":
        return "toplanma"
    # Camiler toplanma alanı olarak sınıflandırılır
    if amenity == "place_of_worship" and religion == "muslim":
        return "toplanma"
    if amenity in ("hospital", "clinic", "doctors"):
        return "saglik"
    if amenity in ("school", "university", "college", "kindergarten"):
        return "egitim"
    return "diger"


def _classify_transit(tags: dict) -> str | None:
    highway  = tags.get("highway", "")
    railway  = tags.get("railway", "")
    amenity  = tags.get("amenity", "")
    station  = tags.get("station", "")
    name     = tags.get("name", "").lower()

    # Metrobüs — İstanbul'a özgü BRT hattı
    if "metrobüs" in name or "metrobus" in name:
        return "metrobus"

    # Metro / subway
    if station == "subway" or railway == "subway_entrance":
        return "metro"

    # Marmaray / banliyö treni
    if railway in ("station", "halt"):
        if "marmaray" in name or "banliyö" in name or "tcdd" in name:
            return "marmaray"
        return "marmaray"  # Tüm demiryolu istasyonlarını Marmaray olarak say

    # Tramvay
    if railway == "tram_stop":
        return "tramvay"

    # Otobüs
    if highway == "bus_stop" or amenity == "bus_station":
        return "otobus"

    return None


def _element_latlon(el: dict) -> tuple[float, float] | None:
    if el["type"] == "node":
        lat, lon = el.get("lat"), el.get("lon")
        return (lat, lon) if lat is not None else None
    center = el.get("center", {})
    if center:
        lat, lon = center.get("lat"), center.get("lon")
        return (lat, lon) if lat is not None else None
    return None


def fetch_overpass(ql: str, retries: int = 2) -> dict:
    data = urllib.parse.urlencode({"data": ql}).encode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "SafeMatchAI/1.0 (github.com/cdemir7/safematch-ai)",
    }
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(OVERPASS_URL, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries:
                wait = 10 * (attempt + 1)
                print(f"  ⚠ 429 Too Many Requests — {wait}s bekleniyor…")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Overpass sorgusu başarısız")


def fetch_pois() -> None:
    if OUTPUT_POI.exists():
        existing = json.loads(OUTPUT_POI.read_text(encoding="utf-8"))
        print(f"✓ {OUTPUT_POI} zaten mevcut — {len(existing)} POI yüklendi.")
        return

    print("POI sorgusu (saglik / egitim / toplanma + cami)…")
    raw = fetch_overpass(OVERPASS_POI_QL)
    elements = raw.get("elements", [])
    print(f"  Ham element: {len(elements)}")

    pois = []
    skipped = 0
    from collections import Counter
    counts: Counter = Counter()

    for el in elements:
        coords = _element_latlon(el)
        if coords is None:
            skipped += 1
            continue
        tags = el.get("tags", {})
        cat  = _classify_poi(tags)
        if cat == "diger":
            skipped += 1
            continue
        counts[cat] += 1
        pois.append({
            "osm_id":   el["id"],
            "osm_type": el["type"],
            "category": cat,
            "name":     tags.get("name") or tags.get("name:tr"),
            "lat":      coords[0],
            "lon":      coords[1],
            "tags":     tags,
        })

    OUTPUT_POI.write_text(json.dumps(pois, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(pois)} POI kaydedildi → {OUTPUT_POI}  (atlanan: {skipped})")
    for cat, n in sorted(counts.items()):
        print(f"  {cat:12s}: {n:5d}")


def fetch_transit() -> None:
    if OUTPUT_TRANSIT.exists():
        existing = json.loads(OUTPUT_TRANSIT.read_text(encoding="utf-8"))
        print(f"✓ {OUTPUT_TRANSIT} zaten mevcut — {len(existing)} transit durağı yüklendi.")
        return

    print("\nTransit sorgusu (otobüs / metro / metrobüs / Marmaray / tramvay)…")
    print("  Bu 30-60 saniye sürebilir…")
    raw = fetch_overpass(OVERPASS_TRANSIT_QL)
    elements = raw.get("elements", [])
    print(f"  Ham element: {len(elements)}")

    stops = []
    skipped = 0
    from collections import Counter
    counts: Counter = Counter()

    for el in elements:
        coords = _element_latlon(el)
        if coords is None:
            skipped += 1
            continue
        tags  = el.get("tags", {})
        ttype = _classify_transit(tags)
        if ttype is None:
            skipped += 1
            continue
        counts[ttype] += 1
        stops.append({
            "osm_id":       el["id"],
            "osm_type":     el["type"],
            "transit_type": ttype,
            "name":         tags.get("name") or tags.get("name:tr"),
            "lat":          coords[0],
            "lon":          coords[1],
        })

    OUTPUT_TRANSIT.write_text(json.dumps(stops, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(stops)} transit durağı kaydedildi → {OUTPUT_TRANSIT}  (atlanan: {skipped})")
    for ttype, n in sorted(counts.items()):
        print(f"  {ttype:12s}: {n:5d}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fetch_pois()
    # İki sorgu arasında Overpass'ı biraz dinlendir
    time.sleep(3)
    fetch_transit()
    print("\n✓ Tüm veriler indirildi.")


if __name__ == "__main__":
    main()
