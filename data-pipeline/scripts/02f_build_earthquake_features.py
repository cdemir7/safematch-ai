from pathlib import Path
import re
import unicodedata

import geopandas as gpd
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

NEIGHBORHOODS_FILE = (
    BASE_DIR
    / "output"
    / "istanbul_mahalleler.geojson"
)

VS30_FILE = (
    BASE_DIR
    / "output"
    / "earthquake_neighborhood_vs30.csv"
)

DISTRICT_METRICS_FILE = (
    BASE_DIR
    / "output"
    / "earthquake_district_metrics.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "output"
    / "earthquake_neighborhood_features.geojson"
)


def normalize_name(value: object) -> str:
    if pd.isna(value):
        return ""

    text = str(value).strip().lower()

    replacements = {
        "ı": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = re.sub(r"\bmahallesi\b", "", text)
    text = re.sub(r"\bmah\b", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    
    aliases = {
        "eyup": "eyupsultan",
    }

    text = " ".join(text.split())
    return aliases.get(text, text)
    return " ".join(text.split())


def main() -> None:
    neighborhoods = gpd.read_file(NEIGHBORHOODS_FILE)
    vs30 = pd.read_csv(VS30_FILE)
    district_metrics = pd.read_csv(DISTRICT_METRICS_FILE)

    print(f"Mahalle GeoJSON satiri: {len(neighborhoods)}")
    print(f"Vs30 satiri: {len(vs30)}")
    print(f"Ilce deprem metrigi satiri: {len(district_metrics)}")

    neighborhoods["ilce_key"] = (
        neighborhoods["ilce_adi"].apply(normalize_name)
    )
    neighborhoods["mahalle_key"] = (
        neighborhoods["mahalle_adi"].apply(normalize_name)
    )

    vs30["ilce_key"] = vs30["ilce_adi"].apply(normalize_name)
    vs30["mahalle_key"] = vs30["mahalle_adi"].apply(normalize_name)

    district_metrics["ilce_key"] = (
        district_metrics["ilce_adi"].apply(normalize_name)
    )

    vs30_columns = [
        "ilce_key",
        "mahalle_key",
        "vs30_ortalama",
        "vs30_min",
        "vs30_max",
        "vs30_piksel_sayisi",
        "vs30_guven_seviyesi",
    ]

    district_columns = [
        column
        for column in district_metrics.columns
        if column not in ["ilce_adi"]
    ]

    merged = neighborhoods.merge(
        vs30[vs30_columns],
        on=["ilce_key", "mahalle_key"],
        how="left",
        validate="one_to_one",
    )

    merged = merged.merge(
        district_metrics[district_columns],
        on="ilce_key",
        how="left",
        validate="many_to_one",
    )

    missing_vs30 = merged["vs30_ortalama"].isna().sum()
    missing_district = merged["toplam_bina"].isna().sum()

    duplicate_count = merged.duplicated(
        ["ilce_key", "mahalle_key"]
    ).sum()

    print()
    print(f"Birlesmis satir sayisi: {len(merged)}")
    print(f"Vs30 eslesmeyen mahalle: {missing_vs30}")
    print(f"Ilce metrigi eslesmeyen mahalle: {missing_district}")
    print(f"Tekrarlanan ilce-mahalle: {duplicate_count}")

    if missing_vs30 > 0:
        print()
        print("Vs30 eslesmeyen ilk kayitlar:")
        print(
            merged.loc[
                merged["vs30_ortalama"].isna(),
                ["ilce_adi", "mahalle_adi"],
            ].head(10)
        )

    if missing_district > 0:
        print()
        print("Ilce metrigi eslesmeyen ilk kayitlar:")
        print(
            merged.loc[
                merged["toplam_bina"].isna(),
                ["ilce_adi", "mahalle_adi"],
            ].head(10)
        )

    merged = merged.drop(
        columns=["ilce_key", "mahalle_key"]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    merged.to_file(
        OUTPUT_FILE,
        driver="GeoJSON",
    )

    print()
    print(f"Kaydedildi: {OUTPUT_FILE}")
    print(f"Kolon sayisi: {len(merged.columns)}")


if __name__ == "__main__":
    main()