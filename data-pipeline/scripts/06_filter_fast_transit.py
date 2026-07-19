"""
06_filter_fast_transit.py
──────────────────────────
data/transit_raw.json içindeki tüm toplu taşıma duraklarından sadece
"hızlı transit" olanları (metro, metrobüs, marmaray) filtreleyip
backend'in kullandığı hizli_transit_stops.json dosyasını üretir.

Girdi
-----
    data/transit_raw.json
    Beklenen şema: [{"name": str, "lat": float, "lon": float,
                      "transit_type": str, ...}, ...]
    transit_type değerleri arasında en az "metro", "metrobus", "marmaray"
    olmalı (büyük/küçük harf ve boşluk farkları normalize edilir).

Çıktı
-----
    ../backend/app/data/hizli_transit_stops.json
    [{"name": str, "lat": float, "lon": float, "type": "metro"|"metrobus"|"marmaray"}, ...]

Davranış
--------
transit_raw.json henüz yoksa (OSM/İBB toplu taşıma pipeline'ı Sprint 1'de
tamamlanmadıysa) bu script hiçbir şey YAZMAZ ve mevcut
hizli_transit_stops.json'u olduğu gibi bırakır — böylece elle hazırlanan
(gerçek istasyon adları/koordinatlarıyla) yedek veri seti kazara boş bir
dosyayla ezilmez. Bkz. backend/app/data/README.md.

Kullanım
--------
    python scripts/06_filter_fast_transit.py
"""
from __future__ import annotations

import json
import pathlib

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
TRANSIT_RAW_FILE = DATA_DIR / "transit_raw.json"
OUTPUT_FILE = (
    pathlib.Path(__file__).parent.parent.parent / "backend" / "app" / "data" / "hizli_transit_stops.json"
)

FAST_TRANSIT_TYPES = {"metro", "metrobus", "marmaray"}


def normalize_type(raw_type: str) -> str | None:
    t = raw_type.strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    if t in ("metro",):
        return "metro"
    if t in ("metrobus", "metrobüs"):
        return "metrobus"
    if t in ("marmaray",):
        return "marmaray"
    return None


def main() -> None:
    if not TRANSIT_RAW_FILE.exists():
        print(f"✗ {TRANSIT_RAW_FILE} bulunamadı — filtreleme atlanıyor.")
        print("  Mevcut hizli_transit_stops.json (varsa) değiştirilmedi.")
        print("  Gerçek toplu taşıma verisi geldiğinde bu scripti tekrar çalıştırın.")
        return

    raw = json.loads(TRANSIT_RAW_FILE.read_text(encoding="utf-8"))

    filtered = []
    for stop in raw:
        transit_type = normalize_type(str(stop.get("transit_type", "")))
        if transit_type is None:
            continue
        if "lat" not in stop or "lon" not in stop:
            continue
        filtered.append({
            "name": stop.get("name", "Bilinmeyen Durak"),
            "lat": float(stop["lat"]),
            "lon": float(stop["lon"]),
            "type": transit_type,
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(filtered, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✓ {len(filtered)} hızlı transit durağı → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
