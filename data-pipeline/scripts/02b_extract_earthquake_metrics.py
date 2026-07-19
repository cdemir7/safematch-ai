import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parents[1]

REPORTS_DIR = (
    BASE_DIR
    / "sources"
    / "earthquake"
    / "district_reports"
)

OUTPUT_FILE = (
    BASE_DIR
    / "output"
    / "earthquake_district_metrics.csv"
)


def normalize_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def parse_number(value: str | None) -> int | None:
    if value is None:
        return None

    digits = re.sub(r"\D", "", value)

    if not digits:
        return None

    return int(digits)


def parse_percentage(value: str | None) -> float | None:
    if value is None:
        return None

    cleaned = value.replace(" ", "").replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return None


def search_number(pattern: str, text: str) -> int | None:
    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return parse_number(match.group(1))


def extract_metrics(pdf_path: Path) -> dict:
    reader = PdfReader(pdf_path)

    # Sonuç ve değerlendirme bölümü genellikle son sayfalarda bulunur.
    selected_pages = reader.pages[-10:]

    text = " ".join(
        page.extract_text() or ""
        for page in selected_pages
    )

    text = normalize_text(text)

    # Harfler arasındaki OCR boşluklarını yok etmek için.
    compact_text = re.sub(r"\s+", "", text.lower())

    total_buildings = search_number(
        r"analiz edilen toplam bina sayısı\s+([\d.\s]+)",
        text,
    )

    medium_plus_buildings = search_number(
        r"yaklaşık\s+([\d.\s]+)\s+bina\)?\s+orta ve üstü",
        text,
    )

    deaths = search_number(
        r"ortalama\s+([\d.\s]+)\s+civarında can kaybı",
        text,
    )

    serious_injured = search_number(
        r"yaklaşık\s+([\d.\s]+)\s+kişinin ağır yaralan",
        text,
    )

    hospital_treatment = search_number(
        r"([\d.\s]+)\s+kişinin de hastane şartlarında",
        text,
    )

    shelter_households = search_number(
        r"(?:yaklaşık\s+)?([\d.\s]+)\s+hanelik acil barınma",
        text,
    )

    shelter_people = search_number(
        r"(?:yaklaşık\s+)?([\d.\s]+)\s+kişinin acil barınma",
        text,
    )

    # Bazı raporlar sayıyı 0 olarak yazmak yerine
    # "can kaybı ve ağır yaralı olmayacağı" diyor.
    if deaths is None and (
        "cankaybıolmayacağı" in compact_text
        or "cankaybıveağıryaralıolmayacağı" in compact_text
    ):
        deaths = 0

    if serious_injured is None and (
        "ağıryaralıolmayacağı" in compact_text
        or "cankaybıveağıryaralıolmayacağı" in compact_text
    ):
        serious_injured = 0

    if hospital_treatment is None and (
        "hastaneşartlarındatedavigörmesigerekmeyeceği"
        in compact_text
        or "hastaneşartlarındatedavigerekmeyeceği"
        in compact_text
    ):
        hospital_treatment = 0
        
        # PDF metin yapısı diğer raporlardan farklı olan iki ilçe için
    # raporun sonuç bölümündeki açık değerler kullanılır.
    if pdf_path.stem == "Cekmekoy":
        deaths = 1
        serious_injured = 0
        hospital_treatment = 18

    if pdf_path.stem == "Sile":
        deaths = 0
        serious_injured = 0
        hospital_treatment = 0

    damage_match = re.search(
        r"%([\d.,]+).*?hasargörmeyeceği.*?"
        r"%([\d.,]+).*?hafif.*?"
        r"%([\d.,]+).*?orta.*?"
        r"%([\d.,]+).*?ağır.*?"
        r"%([\d.,]+).*?çokağır",
        compact_text,
        flags=re.IGNORECASE,
    )

    if damage_match:
        (
            undamaged_pct,
            light_damage_pct,
            medium_damage_pct,
            heavy_damage_pct,
            very_heavy_damage_pct,
        ) = [
            parse_percentage(value)
            for value in damage_match.groups()
        ]
    else:
        undamaged_pct = None
        light_damage_pct = None
        medium_damage_pct = None
        heavy_damage_pct = None
        very_heavy_damage_pct = None

    return {
        "ilce_adi": pdf_path.stem,
        "toplam_bina": total_buildings,
        "hasarsiz_yuzde": undamaged_pct,
        "hafif_hasar_yuzde": light_damage_pct,
        "orta_hasar_yuzde": medium_damage_pct,
        "agir_hasar_yuzde": heavy_damage_pct,
        "cok_agir_hasar_yuzde": very_heavy_damage_pct,
        "orta_ve_ustu_hasarli_bina": medium_plus_buildings,
        "can_kaybi": deaths,
        "agir_yarali": serious_injured,
        "hastanede_tedavi": hospital_treatment,
        "gecici_barinma_hane": shelter_households,
        "gecici_barinma_kisi": shelter_people,
        "yol_kapanma_verisi": "Harita",
        "kaynak_yili": 2020,
        "senaryo": "Mw 7.5 gece",
        "veri_duzeyi": "ilce",
        "kaynak_pdf": pdf_path.name,
    }


def main() -> None:
    pdf_files = sorted(REPORTS_DIR.glob("*.pdf"))

    print(f"PDF count: {len(pdf_files)}")

    rows = []

    for index, pdf_path in enumerate(pdf_files, start=1):
        print(f"[{index}/{len(pdf_files)}] {pdf_path.name}")

        try:
            rows.append(extract_metrics(pdf_path))
        except Exception as error:
            print(f"ERROR: {pdf_path.name}: {error}")

    dataframe = pd.DataFrame(rows)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(f"Row count: {len(dataframe)}")
    print(f"Saved: {OUTPUT_FILE}")

    print()
    print(dataframe.head().to_string(index=False))


if __name__ == "__main__":
    main()