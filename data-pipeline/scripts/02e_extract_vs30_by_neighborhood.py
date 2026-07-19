from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask


BASE_DIR = Path(__file__).resolve().parents[1]

MAHALLE_FILE = (
    BASE_DIR
    / "output"
    / "istanbul_mahalleler.geojson"
)

VS30_FILE = (
    BASE_DIR
    / "sources"
    / "earthquake"
    / "vs30"
    / "istanbul_vs30.tif"
)

OUTPUT_FILE = (
    BASE_DIR
    / "output"
    / "earthquake_neighborhood_vs30.csv"
)


def calculate_statistics(
    geometry,
    raster: rasterio.io.DatasetReader,
) -> dict:
    try:
        clipped, _ = mask(
            raster,
            [geometry],
            crop=True,
            all_touched=True,
            filled=False,
        )

        values = clipped[0]

        if np.ma.isMaskedArray(values):
            values = values.compressed()
        else:
            values = values.flatten()

        values = values[
            np.isfinite(values)
            & (values > 0)
        ]

        if len(values) == 0:
            return {
                "vs30_ortalama": None,
                "vs30_min": None,
                "vs30_max": None,
                "vs30_piksel_sayisi": 0,
            }

        return {
            "vs30_ortalama": round(float(values.mean()), 2),
            "vs30_min": round(float(values.min()), 2),
            "vs30_max": round(float(values.max()), 2),
            "vs30_piksel_sayisi": int(len(values)),
        }

    except ValueError:
        return {
            "vs30_ortalama": None,
            "vs30_min": None,
            "vs30_max": None,
            "vs30_piksel_sayisi": 0,
        }


def main() -> None:
    neighborhoods = gpd.read_file(MAHALLE_FILE)

    print(f"Mahalle sayisi: {len(neighborhoods)}")
    print(f"GeoJSON CRS: {neighborhoods.crs}")

    results = []

    with rasterio.open(VS30_FILE) as raster:
        print(f"Raster CRS: {raster.crs}")

        if neighborhoods.crs != raster.crs:
            neighborhoods = neighborhoods.to_crs(raster.crs)

        for index, row in neighborhoods.iterrows():
            statistics = calculate_statistics(
                row.geometry,
                raster,
            )

            result = {
                "ilce_adi": row.get("ilce_adi"),
                "mahalle_adi": row.get("mahalle_adi"),
                **statistics,
            }

            results.append(result)

            if (index + 1) % 100 == 0:
                print(
                    f"{index + 1} mahalle islendi..."
                )

    dataframe = pd.DataFrame(results)
    dataframe["vs30_guven_seviyesi"] = pd.cut(
    dataframe["vs30_piksel_sayisi"],
    bins=[0, 3, 9, float("inf")],
    labels=["dusuk", "orta", "yuksek"],
)

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
    print(f"Kaydedildi: {OUTPUT_FILE}")
    print(f"Satir sayisi: {len(dataframe)}")
    print(
        "Vs30 bulunamayan mahalle sayisi:",
        dataframe["vs30_ortalama"].isna().sum(),
    )

    print()
    print(dataframe.head())


if __name__ == "__main__":
    main()