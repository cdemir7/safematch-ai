"""
05_build_features.py
────────────────────
Tüm ara dosyaları birleştirerek backend'in kullandığı
mahalle_features.json dosyasını üretir.

Girdiler
--------
    output/istanbul_mahalleler.geojson  mahalle geometrileri + ilçe adı
    data/poi_counts.json         mahalle başına POI sayısı
    data/earthquake_scores.json  mahalle başına deprem_guvenlik skoru
    data/ilce_fiyat.csv          ilçe bazlı m2 fiyat proxy

Çıktı
-----
    output/mahalle_features.json

Her mahalle objesi şu yapıdadır:
{
  "mahalle_id": "IST-0001",
  "mahalle_adi": "Cihangir",
  "ilce": "Beyoğlu",
  "geometry": { GeoJSON Polygon },
  "scores": {
    "deprem_guvenlik": 45,   // 0-100, yüksek = güvenli
    "saglik":          62,
    "egitim":          58,
    "ulasim":          55,   // Sprint 1: sabit 55 (ulaşım verisi eklenmedi)
    "sosyal_yasam":    50,   // Sprint 1: POI çeşitliliğinden türetildi
    "yasam_kalitesi":  52
  },
  "raw": {
    "hastane_count":   3,
    "okul_count":      7,
    "cami_count":      2,
    "toplanma_count":  1
  },
  "avg_m2_fiyat": 35000
}

Kullanım
--------
    python scripts/05_build_features.py
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import sys
import unicodedata
from typing import Any

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "output"

BOUNDARIES_FILE = OUTPUT_DIR / "istanbul_mahalleler.geojson"
POI_COUNTS_FILE = DATA_DIR / "poi_counts.json"
EARTHQUAKE_FILE = DATA_DIR / "earthquake_scores.json"
FIYAT_CSV = DATA_DIR / "ilce_fiyat.csv"
OUTPUT_FILE = OUTPUT_DIR / "mahalle_features.json"

# Ulaşım verisi yoksa (transit_raw.json boşsa) kullanılan varsayılan
DEFAULT_ULASIM_SCORE = 45


def normalize_str(s: str) -> str:
    s = s.strip().lower()
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def load_fiyat_csv() -> dict[str, int]:
    fiyat: dict[str, int] = {}
    with open(FIYAT_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = normalize_str(row["ilce"])
            fiyat[key] = int(row["avg_m2_fiyat_tl"])
    return fiyat


def percentile_rank_score(value: int, all_values: list[int]) -> float:
    """
    Verilen değerin tüm değerler arasındaki yüzdelik sıralamasını 0-100 olarak döner.
    Yüksek değer = iyi (POI çok olması iyi).
    """
    if not all_values:
        return 50.0
    rank = sum(1 for v in all_values if v <= value)
    return round((rank / len(all_values)) * 100, 1)


def compute_sosyal_yasam(poi_counts: dict) -> float:
    """
    Kategori çeşitliliği + toplam POI yoğunluğundan sosyal yaşam skoru.
    En az 3 farklı kategori → bonus.
    """
    total = sum(poi_counts.values())
    diversity = sum(1 for v in poi_counts.values() if v > 0)
    base = min(total * 3, 60)  # Maksimum 60 puan toplam yoğunluktan
    bonus = diversity * 10     # Her kategori 10 puan bonus, max 40
    return min(round(base + bonus, 1), 100.0)


def check_inputs() -> None:
    missing = []
    for f in (BOUNDARIES_FILE, POI_COUNTS_FILE, EARTHQUAKE_FILE, FIYAT_CSV):
        if not f.exists():
            missing.append(str(f))
    if missing:
        print("✗ Eksik dosyalar — önce diğer scriptleri çalıştırın:")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)


def main() -> None:
    check_inputs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    boundaries = json.loads(BOUNDARIES_FILE.read_text(encoding="utf-8"))
    poi_counts: dict[str, dict] = json.loads(POI_COUNTS_FILE.read_text(encoding="utf-8"))
    eq_scores: dict[str, float] = json.loads(EARTHQUAKE_FILE.read_text(encoding="utf-8"))
    fiyat_data = load_fiyat_csv()

    features = boundaries["features"]
    print(f"Mahalle sayısı: {len(features)}")

    # Percentile rank için global listeler
    all_saglik        = [poi_counts.get(str(f["properties"]["mahalle_osm_id"]), {}).get("saglik", 0)        for f in features]
    all_egitim        = [poi_counts.get(str(f["properties"]["mahalle_osm_id"]), {}).get("egitim", 0)        for f in features]
    all_transit       = [poi_counts.get(str(f["properties"]["mahalle_osm_id"]), {}).get("transit", 0)       for f in features]
    all_transit_hizli = [poi_counts.get(str(f["properties"]["mahalle_osm_id"]), {}).get("transit_hizli", 0) for f in features]

    has_transit_data = any(v > 0 for v in all_transit)

    output_features: list[dict[str, Any]] = []

    for feature in features:
        props = feature["properties"]
        mahalle_id = str(props["mahalle_osm_id"])
        ilce_raw = props.get("ilce_adi", "")
        ilce_key = normalize_str(ilce_raw)

        counts = poi_counts.get(mahalle_id, {
            "saglik": 0, "egitim": 0, "toplanma": 0,
            "transit": 0, "transit_hizli": 0,
        })

        # Skor hesaplamaları
        deprem_score = eq_scores.get(mahalle_id, 40.0)
        saglik_score = percentile_rank_score(counts.get("saglik", 0), all_saglik)
        egitim_score = percentile_rank_score(counts.get("egitim", 0), all_egitim)

        # Ulaşım skoru: gerçek transit verisi varsa percentile rank, yoksa varsayılan
        if has_transit_data:
            transit_score      = percentile_rank_score(counts.get("transit", 0),       all_transit)
            transit_hizli_score = percentile_rank_score(counts.get("transit_hizli", 0), all_transit_hizli)
            # Genel ulaşım = %60 tüm transit + %40 hızlı transit (ofis odaklı)
            ulasim_score = round(transit_score * 0.6 + transit_hizli_score * 0.4, 1)
        else:
            ulasim_score = DEFAULT_ULASIM_SCORE
            transit_hizli_score = DEFAULT_ULASIM_SCORE

        sosyal_score = compute_sosyal_yasam(counts)
        yasam_score  = round((saglik_score * 0.3 + egitim_score * 0.3 + sosyal_score * 0.4), 1)

        # Fiyat eşleştirmesi
        fiyat = fiyat_data.get(ilce_key)
        if fiyat is None:
            match = next((k for k in fiyat_data if ilce_key in k or k in ilce_key), None)
            fiyat = fiyat_data.get(match, 30000) if match else 30000

        output_features.append({
            "mahalle_id":  mahalle_id,
            "mahalle_adi": props["mahalle_adi"],
            "ilce":        ilce_raw,
            "geometry":    feature["geometry"],
            "scores": {
                "deprem_guvenlik":    round(deprem_score, 1),
                "saglik":             round(saglik_score, 1),
                "egitim":             round(egitim_score, 1),
                "ulasim":             round(ulasim_score, 1),
                "ulasim_hizli":       round(transit_hizli_score, 1),  # ofis/hibrit için
                "sosyal_yasam":       round(sosyal_score, 1),
                "yasam_kalitesi":     round(yasam_score, 1),
            },
            "raw": {
                "hastane_count":      counts.get("saglik", 0),
                "okul_count":         counts.get("egitim", 0),
                "toplanma_count":     counts.get("toplanma", 0),
                "transit_count":      counts.get("transit", 0),
                "transit_hizli_count": counts.get("transit_hizli", 0),
            },
            "avg_m2_fiyat": fiyat,
        })

    OUTPUT_FILE.write_text(
        json.dumps(output_features, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Özet istatistik
    import statistics
    deprem_scores_all = [f["scores"]["deprem_guvenlik"] for f in output_features]
    print(f"\n✓ {len(output_features)} mahalle → {OUTPUT_FILE}")
    print(f"\n  deprem_guvenlik — ort: {statistics.mean(deprem_scores_all):.1f}  "
          f"min: {min(deprem_scores_all):.1f}  max: {max(deprem_scores_all):.1f}")
    print("\n  Sonraki adımlar:")
    print("  → output/mahalle_features.json dosyasını backend/app/data/ klasörüne kopyalayın.")
    print("  → veya backend config'te FEATURES_PATH ortam değişkenini ayarlayın.")


if __name__ == "__main__":
    main()
