"""
03_count_pois.py
────────────────
Her İstanbul mahallesi için mahalle poligonu içindeki veya
yakınındaki POI ve transit durağı sayısını hesaplar.

Kategoriler
-----------
  saglik   : hastane, klinik
  egitim   : okul, üniversite
  toplanma : toplanma alanı + cami (afet noktası)
  transit  : otobüs + metro + metrobüs + marmaray + tramvay (toplam)
  transit_hizli : metro + metrobüs + marmaray (hızlı transit — ofis skoru için)

Girdi : output/istanbul_mahalleler.geojson
         data/poi_raw.json
         data/transit_raw.json
Çıktı : data/poi_counts.json

Kullanım
--------
    python scripts/03_count_pois.py

Bağımlılık: shapely (pip install shapely)
"""
from __future__ import annotations

import json
import pathlib
import sys

DATA_DIR       = pathlib.Path(__file__).parent.parent / "data"
OUTPUT_DIR     = pathlib.Path(__file__).parent.parent / "output"
BOUNDARIES_FILE = OUTPUT_DIR / "istanbul_mahalleler.geojson"
POI_FILE       = DATA_DIR / "poi_raw.json"
TRANSIT_FILE   = DATA_DIR / "transit_raw.json"
OUTPUT         = DATA_DIR / "poi_counts.json"

POI_CATEGORIES     = ["saglik", "egitim", "toplanma"]
# "transit_hizli" = metro + metrobüs + marmaray (öfis/hibrit çalışanlar için)
HIZLI_TRANSIT_TYPES = {"metro", "metrobus", "marmaray"}

# Mahalle sınırına dışarıdan bu kadar derece içindeki noktalar da sayılır (~300 m)
BUFFER_DEG = 0.003


def main() -> None:
    try:
        from shapely.geometry import Point, shape
    except ImportError:
        print("✗ shapely kurulu değil. Kurmak için: pip install shapely")
        sys.exit(1)

    for f in (BOUNDARIES_FILE, POI_FILE):
        if not f.exists():
            print(f"✗ Dosya bulunamadı: {f}")
            print("  Önce 01_fetch_boundaries.py ve 02_fetch_poi.py çalıştırın.")
            sys.exit(1)

    boundaries = json.loads(BOUNDARIES_FILE.read_text(encoding="utf-8"))
    pois       = json.loads(POI_FILE.read_text(encoding="utf-8"))

    # Transit verisi opsiyonel — yoksa transit skor hesaplanamaz
    transit_points: list[tuple[str, object]] = []
    if TRANSIT_FILE.exists():
        transit_data = json.loads(TRANSIT_FILE.read_text(encoding="utf-8"))
        for t in transit_data:
            pt = Point(t["lon"], t["lat"])
            transit_points.append((t["transit_type"], pt))
        print(f"Transit durağı yüklendi: {len(transit_points)}")
    else:
        print("⚠ transit_raw.json bulunamadı — transit skoru hesaplanmayacak.")

    features = boundaries["features"]
    print(f"Mahalle sayısı : {len(features)}")
    print(f"POI sayısı     : {len(pois)}")
    print("Sayım başlıyor (birkaç dakika sürebilir)…\n")

    # POI'leri kategoriye göre grupla
    poi_points: dict[str, list] = {cat: [] for cat in POI_CATEGORIES}
    for poi in pois:
        cat = poi.get("category")
        if cat in poi_points:
            poi_points[cat].append(Point(poi["lon"], poi["lat"]))

    result: dict[str, dict] = {}

    for i, feature in enumerate(features):
        mahalle_id  = str(feature["properties"]["mahalle_osm_id"])
        mahalle_adi = feature["properties"]["mahalle_adi"]

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(features)} işlendi…")

        try:
            geom     = shape(feature["geometry"])
            buffered = geom.buffer(BUFFER_DEG)
        except Exception as exc:
            print(f"  ⚠ Geometri hatası [{mahalle_adi}]: {exc}")
            result[mahalle_id] = {cat: 0 for cat in POI_CATEGORIES}
            result[mahalle_id].update({"transit": 0, "transit_hizli": 0})
            continue

        counts: dict[str, int] = {}

        # POI sayımı
        for cat in POI_CATEGORIES:
            counts[cat] = sum(1 for pt in poi_points[cat] if buffered.contains(pt))

        # Transit sayımı
        if transit_points:
            transit_total  = 0
            transit_hizli  = 0
            for ttype, pt in transit_points:
                if buffered.contains(pt):
                    transit_total += 1
                    if ttype in HIZLI_TRANSIT_TYPES:
                        transit_hizli += 1
            counts["transit"]       = transit_total
            counts["transit_hizli"] = transit_hizli
        else:
            counts["transit"]       = 0
            counts["transit_hizli"] = 0

        result[mahalle_id] = counts

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    total = {k: sum(r.get(k, 0) for r in result.values()) for k in POI_CATEGORIES + ["transit", "transit_hizli"]}
    print(f"\n✓ {len(result)} mahalle için sayım tamamlandı → {OUTPUT}")
    print("\n  Toplam sayımlar:")
    for cat in POI_CATEGORIES + ["transit", "transit_hizli"]:
        print(f"    {cat:18s}: {total[cat]:6d}")


if __name__ == "__main__":
    main()
