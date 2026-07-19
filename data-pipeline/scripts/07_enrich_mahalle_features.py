"""
07_enrich_mahalle_features.py
──────────────────────────────
İstanbul'un TÜM mahallelerini (968) kapsayan, backend'in kullandığı 16
kayıtlık elle hazırlanmış `mahalle_features.json` yerine geçmeye aday
zenginleştirilmiş bir özellik dosyası üretir.

`backend/app/data/mahalle_features.json` dosyasına DOKUNMAZ — bu script'in
çıktısı ayrı bir isimle yazılır (bkz. OUTPUT_FILE). Ekip hazır olduğunda
backend'i `FEATURES_PATH` ortam değişkeniyle bu dosyaya yönlendirebilir
(bkz. backend/app/services/recommendation_service.py).

Girdiler
--------
    output/istanbul_mahalleler.geojson          968 mahalle: geometri + isim (temel katman)
    output/earthquake_neighborhood_features.geojson
                                                  968 mahalle: Vs30 (zemin) + ilçe bazlı
                                                  İBB Mw7.5 hasar tahmini (bkz. CLAUDE.md §4.2)
    output/mahalle_toplanma_eslesme.geojson      966 mahalle: en yakın AFAD toplanma alanı
    data/ilce_fiyat.csv                          39 ilçe: ortalama m² fiyat proxy'si
    data/manual_overrides.json                   opsiyonel elle düzeltme katmanı (bkz.
                                                  data/MANUAL_OVERRIDES.md)

Henüz VERİSİ OLMAYAN kriterler (saglik, egitim, ulasim, sosyal_yasam,
yasam_kalitesi — gerçek POI/ulaşım pipeline'ı Faz 1'de tamamlanmadı):
DEFAULT_SCORE ile doldurulur ve `data_quality` bloğunda "veri_yok" olarak
işaretlenir. Skoru UYDURMAK yerine eksikliği göstermek CLAUDE.md ilke 4'tür.

Deprem güvenlik skoru NASIL hesaplanır (CLAUDE.md §4.2 "zemin mantığı"):
    %60  ilçe bazlı İBB hasar oranı (orta+ağır+çok ağır hasarlı bina yüzdesi,
         39 ilçe arasında min-max ölçeklenip ters çevrilir — düşük hasar = yüksek skor)
    %40  mahalle bazlı Vs30 (USGS, m/s — yüksek Vs30 = daha sert/kaya zemin =
         daha az deprem dalgası büyütmesi = daha güvenli), 968 mahalle arasında
         min-max ölçeklenir.
Bu sayede aynı ilçedeki iki mahalle, zemin farkına göre farklı skor alabilir
— tamamen ilçe ortalamasına indirgemek yerine.

Çıktı
-----
    backend/app/data/mahalle_features_full.json

Kullanım
--------
    python scripts/07_enrich_mahalle_features.py
"""
from __future__ import annotations

import copy
import csv
import json
import pathlib
import statistics
import unicodedata
from typing import Any

BASE_DIR = pathlib.Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
BACKEND_DATA_DIR = BASE_DIR.parent / "backend" / "app" / "data"

BOUNDARIES_FILE = OUTPUT_DIR / "istanbul_mahalleler.geojson"
EARTHQUAKE_FILE = OUTPUT_DIR / "earthquake_neighborhood_features.geojson"
TOPLANMA_FILE = OUTPUT_DIR / "mahalle_toplanma_eslesme.geojson"
FIYAT_CSV = DATA_DIR / "ilce_fiyat.csv"
MANUAL_OVERRIDES_FILE = DATA_DIR / "manual_overrides.json"

OUTPUT_FILE = BACKEND_DATA_DIR / "mahalle_features_full.json"

# scoring/constants.py::DEFAULT_SCORE ile aynı tutulur — henüz veri olmayan
# kriterler için kullanılır. Backend testlerinden bağımsız kalması için burada
# da ayrı sabitlenir (data-pipeline backend'i import etmez).
DEFAULT_SCORE = 50.0

# Deprem skorunda ilçe hasar oranı vs. mahalle Vs30 ağırlıkları.
ILCE_DAMAGE_WEIGHT = 0.6
VS30_WEIGHT = 0.4

# Fiyat verisi hiçbir ilçeyle eşleşmezse kullanılan varsayılan (TL/m²).
DEFAULT_FIYAT = 30_000
FIYAT_MATCH_QUALITY_KEY = "fiyat"

CRITERIA = [
    "deprem_guvenlik",
    "saglik",
    "egitim",
    "ulasim",
    "sosyal_yasam",
    "yasam_kalitesi",
]

# Gerçek POI/ulaşım pipeline'ı çalışana kadar TÜM mahalleler için DEFAULT_SCORE
# ile doldurulan kriterler. Bu sabit değişmediği sürece 968 kaydın her birine
# "veri_yok" yazmanın anlamı yok — tek kaynak burasıdır (bkz. record başına
# data_quality bloğu, sadece mahalleye göre DEĞİŞEN alanları taşır).
PLACEHOLDER_CRITERIA = ["saglik", "egitim", "ulasim", "sosyal_yasam", "yasam_kalitesi"]


def normalize_str(s: str) -> str:
    s = (s or "").strip().lower()
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def minmax_score(value: float | None, all_values: list[float], invert: bool = False) -> float | None:
    """value'yu all_values aralığında 0-100'e ölçekler. invert=True → düşük değer yüksek skor demek."""
    if value is None or not all_values:
        return None
    lo, hi = min(all_values), max(all_values)
    if hi == lo:
        return 50.0
    ratio = (value - lo) / (hi - lo)
    if invert:
        ratio = 1 - ratio
    return round(max(0.0, min(1.0, ratio)) * 100, 1)


def load_boundaries() -> list[dict]:
    data = json.loads(BOUNDARIES_FILE.read_text(encoding="utf-8"))
    return data["features"]


def load_earthquake_by_id() -> dict[str, dict]:
    data = json.loads(EARTHQUAKE_FILE.read_text(encoding="utf-8"))
    result = {}
    for feature in data["features"]:
        props = feature["properties"]
        mahalle_id = str(props["mahalle_osm_id"])
        result[mahalle_id] = props
    return result


def load_toplanma_by_id() -> dict[str, dict]:
    data = json.loads(TOPLANMA_FILE.read_text(encoding="utf-8"))
    result = {}
    for feature in data["features"]:
        props = feature["properties"]
        mahalle_id = str(props["osm_id_left"])
        result[mahalle_id] = props
    return result


def load_fiyat_csv() -> dict[str, int]:
    fiyat: dict[str, int] = {}
    with open(FIYAT_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fiyat[normalize_str(row["ilce"])] = int(row["avg_m2_fiyat_tl"])
    return fiyat


def match_fiyat(ilce_raw: str, fiyat_data: dict[str, int]) -> tuple[int, str]:
    """(fiyat, kalite_etiketi) döner. kalite: 'ilce_eslesme' | 'ilce_kismi_eslesme' | 'varsayilan'."""
    ilce_key = normalize_str(ilce_raw)
    if ilce_key in fiyat_data:
        return fiyat_data[ilce_key], "ilce_eslesme"
    match = next((k for k in fiyat_data if ilce_key in k or k in ilce_key), None)
    if match:
        return fiyat_data[match], "ilce_kismi_eslesme"
    return DEFAULT_FIYAT, "varsayilan"


def load_manual_overrides() -> dict[str, dict]:
    if not MANUAL_OVERRIDES_FILE.exists():
        return {}
    return json.loads(MANUAL_OVERRIDES_FILE.read_text(encoding="utf-8"))


def apply_manual_override(record: dict, override: dict, data_quality: dict) -> None:
    """override içindeki alanları record'un üzerine yazar, data_quality'i günceller."""
    for score_key, value in override.get("scores", {}).items():
        record["scores"][score_key] = value
        data_quality[score_key] = "manuel_duzeltme"
    for raw_key, value in override.get("raw", {}).items():
        record["raw"][raw_key] = value
    if "raw" in override:
        data_quality["raw"] = "manuel_duzeltme"
    if "avg_m2_fiyat" in override:
        record["avg_m2_fiyat"] = override["avg_m2_fiyat"]
        data_quality[FIYAT_MATCH_QUALITY_KEY] = "manuel_duzeltme"
    if "not" in override:
        record["manuel_not"] = override["not"]


def main() -> None:
    for f in (BOUNDARIES_FILE, EARTHQUAKE_FILE, TOPLANMA_FILE, FIYAT_CSV):
        if not f.exists():
            raise SystemExit(f"✗ Eksik girdi dosyası: {f}")

    boundaries = load_boundaries()
    earthquake_by_id = load_earthquake_by_id()
    toplanma_by_id = load_toplanma_by_id()
    fiyat_data = load_fiyat_csv()
    manual_overrides = load_manual_overrides()

    print(f"Mahalle sayısı (temel katman): {len(boundaries)}")
    print(f"Deprem verisi eşleşen mahalle: {len(earthquake_by_id)}")
    print(f"Toplanma alanı eşleşen mahalle: {len(toplanma_by_id)}")
    print(f"Elle düzeltme kaydı: {len(manual_overrides)}")

    # ── deprem skoru için global dağılımlar (min-max ölçekleme) ──────────
    all_vs30 = [
        p["vs30_ortalama"] for p in earthquake_by_id.values()
        if p.get("vs30_ortalama") is not None
    ]

    ilce_damage_ratio: dict[str, float] = {}
    for mahalle_id, p in earthquake_by_id.items():
        toplam = p.get("toplam_bina")
        hasarli = p.get("orta_ve_ustu_hasarli_bina")
        ilce = p.get("ilce_adi", "")
        if toplam and hasarli is not None and toplam > 0:
            ilce_damage_ratio.setdefault(normalize_str(ilce), hasarli / toplam * 100)
    all_damage_ratios = list(ilce_damage_ratio.values())

    output_features: list[dict[str, Any]] = []
    quality_counts: dict[str, int] = {}

    for feature in boundaries:
        props = feature["properties"]
        mahalle_id = str(props["mahalle_osm_id"])
        mahalle_adi = props["mahalle_adi"]
        ilce_raw = props.get("ilce_adi", "")
        ilce_key = normalize_str(ilce_raw)

        data_quality: dict[str, str] = {}

        # ── deprem_guvenlik ───────────────────────────────────────────
        eq = earthquake_by_id.get(mahalle_id)
        vs30_score = None
        damage_score = None
        if eq is not None:
            vs30_score = minmax_score(eq.get("vs30_ortalama"), all_vs30, invert=False)
            damage_ratio = ilce_damage_ratio.get(ilce_key)
            damage_score = minmax_score(damage_ratio, all_damage_ratios, invert=True)

        if vs30_score is not None and damage_score is not None:
            deprem_score = round(
                damage_score * ILCE_DAMAGE_WEIGHT + vs30_score * VS30_WEIGHT, 1
            )
            data_quality["deprem_guvenlik"] = "hesaplanmis_vs30_ilce"
        elif damage_score is not None:
            deprem_score = round(damage_score, 1)
            data_quality["deprem_guvenlik"] = "kismi_sadece_ilce"
        else:
            deprem_score = DEFAULT_SCORE
            data_quality["deprem_guvenlik"] = "veri_yok"

        # ── henüz veri olmayan kriterler ──────────────────────────────
        # saglik/egitim/ulasim/sosyal_yasam/yasam_kalitesi için gerçek POI/ulaşım
        # verisi henüz yok — bu, 968 kaydın TAMAMI için değişmeyen sabit bir
        # gerçektir, bu yüzden her kayıtta ayrı ayrı tekrar edilmez. Tek kaynağı
        # PLACEHOLDER_CRITERIA sabiti + backend/app/data/README.md'dir.
        scores = {
            "deprem_guvenlik": deprem_score,
            "saglik": DEFAULT_SCORE,
            "egitim": DEFAULT_SCORE,
            "ulasim": DEFAULT_SCORE,
            "ulasim_hizli": DEFAULT_SCORE,
            "sosyal_yasam": DEFAULT_SCORE,
            "yasam_kalitesi": DEFAULT_SCORE,
        }

        # ── toplanma alanı ─────────────────────────────────────────────
        toplanma = toplanma_by_id.get(mahalle_id)
        if toplanma is not None:
            raw = {
                "hastane_count": 0,
                "okul_count": 0,
                "cami_count": 0,
                "toplanma_count": 1,
                "toplanma_alani_adi": toplanma.get("en_yakin_toplanma_adi"),
                "toplanma_mesafe_m": toplanma.get("en_yakin_toplanma_mesafe_m"),
            }
            data_quality["toplanma"] = "eslesti"
        else:
            raw = {
                "hastane_count": 0,
                "okul_count": 0,
                "cami_count": 0,
                "toplanma_count": 0,
                "toplanma_alani_adi": None,
                "toplanma_mesafe_m": None,
            }
            data_quality["toplanma"] = "eslesmedi"

        # ── fiyat ────────────────────────────────────────────────────
        fiyat, fiyat_quality = match_fiyat(ilce_raw, fiyat_data)
        data_quality[FIYAT_MATCH_QUALITY_KEY] = fiyat_quality

        record: dict[str, Any] = {
            "mahalle_id": mahalle_id,
            "mahalle_adi": mahalle_adi,
            "ilce": ilce_raw,
            "geometry": feature["geometry"],
            "scores": scores,
            "raw": raw,
            "avg_m2_fiyat": fiyat,
            "data_quality": data_quality,
        }

        override = manual_overrides.get(mahalle_id)
        if override:
            apply_manual_override(record, override, data_quality)

        for v in data_quality.values():
            quality_counts[v] = quality_counts.get(v, 0) + 1

        output_features.append(record)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    BACKEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(output_features, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    deprem_scores_all = [f["scores"]["deprem_guvenlik"] for f in output_features]
    print(f"\n✓ {len(output_features)} mahalle → {OUTPUT_FILE}")
    print(
        f"  deprem_guvenlik — ort: {statistics.mean(deprem_scores_all):.1f}  "
        f"min: {min(deprem_scores_all):.1f}  max: {max(deprem_scores_all):.1f}"
    )
    print("\n  Mahalleye göre değişen veri kalitesi etiketleri (kayıt sayısı):")
    for label, count in sorted(quality_counts.items(), key=lambda kv: -kv[1]):
        print(f"    {label:28s} {count}")
    print(
        f"\n  Not: {', '.join(PLACEHOLDER_CRITERIA)} — {len(output_features)} "
        f"mahallenin TAMAMI için henüz gerçek POI/ulaşım verisi yok, varsayılan "
        f"({DEFAULT_SCORE}) kullanıldı (mahalleye göre değişmediği için "
        "kayıt başına tekrarlanmıyor). Bu pipeline'lar (02_fetch_poi.py, "
        "03_count_pois.py) tamamlanınca 07 script'i yeniden çalıştırın."
    )
    print(
        "\n  backend bu dosyayı kullanmaya başlamak için:\n"
        "    FEATURES_PATH=backend/app/data/mahalle_features_full.json uvicorn app.main:app --reload"
    )


if __name__ == "__main__":
    main()
