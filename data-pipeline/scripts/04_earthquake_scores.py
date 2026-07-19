"""
04_earthquake_scores.py
───────────────────────
İBB ilçe deprem kayıp verilerinden mahalle bazlı deprem_guvenlik
skoru üretir.

Mantık: Mahalle → ilçesinin skoru (ilk sprint için ilçe bazlı yeterli)
Uyarı : İlçe ölçeği, mahalle içi zemin farklılıklarını yansıtmaz.
         Sonraki iterasyonda zemin sınıfı (ZA-ZF) verisiyle iyileştirilecek.

Girdi : data/ilce_deprem.csv
         output/istanbul_mahalleler.geojson  (ilçe eşleştirmesi için)
Çıktı : data/earthquake_scores.json  {mahalle_id: deprem_guvenlik_skoru}

Kullanım
--------
    python scripts/04_earthquake_scores.py
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys
import unicodedata

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "output"
DEPREM_CSV = DATA_DIR / "ilce_deprem.csv"
BOUNDARIES_FILE = OUTPUT_DIR / "istanbul_mahalleler.geojson"
OUTPUT = DATA_DIR / "earthquake_scores.json"

# Risk seviyesi → 0-100 güvenlik skoru (yüksek = güvenli)
RISK_TO_SCORE = {
    "düşük": 80,
    "orta": 50,
    "yüksek": 22,
}
DEFAULT_SCORE = 40  # İlçe eşleşemezse


def normalize_str(s: str) -> str:
    """Türkçe karakterleri, büyük/küçük farklılığını ve boşlukları normalize eder."""
    s = s.strip().lower()
    # NFD ile Unicode normalize et
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def load_deprem_csv() -> dict[str, dict]:
    """İlçe adı → {risk_seviyesi, ibb_kayip_skoru} dict döndürür."""
    deprem: dict[str, dict] = {}
    with open(DEPREM_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = normalize_str(row["ilce"])
            deprem[key] = {
                "risk_seviyesi": row["deprem_risk_seviyesi"].strip(),
                "ibb_kayip_skoru": int(row["ibb_kayip_skoru"]),
            }
    return deprem


def compute_score(risk_data: dict) -> float:
    """
    İBB kayıp skoru (ham) ile risk seviyesi kategorisini birleştirir.
    İBB skoru zaten 0-100 normalize aralığında verilmiştir (yüksek = güvenli).
    """
    return float(risk_data["ibb_kayip_skoru"])


def main() -> None:
    for f in (DEPREM_CSV, BOUNDARIES_FILE):
        if not f.exists():
            print(f"✗ Dosya bulunamadı: {f}")
            sys.exit(1)

    deprem_data = load_deprem_csv()
    boundaries = json.loads(BOUNDARIES_FILE.read_text(encoding="utf-8"))
    features = boundaries["features"]

    result: dict[str, float] = {}
    unmatched: list[str] = []

    for feature in features:
        props = feature["properties"]
        mahalle_id = str(props["mahalle_osm_id"])
        ilce_raw = props.get("ilce_adi", "")
        ilce_key = normalize_str(ilce_raw)

        if ilce_key in deprem_data:
            score = compute_score(deprem_data[ilce_key])
        else:
            # Kısmi eşleşme dene (ilçe adı farklı yazılmış olabilir)
            match = next(
                (k for k in deprem_data if ilce_key in k or k in ilce_key), None
            )
            if match:
                score = compute_score(deprem_data[match])
            else:
                score = DEFAULT_SCORE
                unmatched.append(f"{mahalle_id} ({ilce_raw})")

        result[mahalle_id] = round(score, 1)

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ {len(result)} mahalle deprem skoru hesaplandı → {OUTPUT}")
    if unmatched:
        print(f"\n  ⚠ Eşleşmeyen ilçe ({len(unmatched)} mahalle) → varsayılan {DEFAULT_SCORE} kullanıldı:")
        for m in unmatched[:10]:
            print(f"    {m}")
        if len(unmatched) > 10:
            print(f"    … ve {len(unmatched) - 10} tane daha")

    # Dağılım özeti
    import statistics
    scores = list(result.values())
    print(f"\n  Skor dağılımı: min={min(scores):.0f}  ort={statistics.mean(scores):.1f}  max={max(scores):.0f}")


if __name__ == "__main__":
    main()
