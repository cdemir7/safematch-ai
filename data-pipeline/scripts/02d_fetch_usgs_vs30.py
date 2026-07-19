from pathlib import Path

import rasterio
from rasterio.windows import from_bounds


BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_DIR = (
    BASE_DIR
    / "sources"
    / "earthquake"
    / "vs30"
)

OUTPUT_FILE = SOURCE_DIR / "istanbul_vs30.tif"

VS30_URL = (
    "https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/"
    "67be4ac3d34e8876fcbfbd89/"
    "vs30_mosaic_median_30c.tif"
)

# İstanbul'u kapsayan yaklaşık sınırlar
WEST = 27.8
SOUTH = 40.7
EAST = 29.9
NORTH = 41.6


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    print("USGS Vs30 verisinden Istanbul alani okunuyor...")

    with rasterio.open(VS30_URL) as source:
        window = from_bounds(
            WEST,
            SOUTH,
            EAST,
            NORTH,
            transform=source.transform,
        )

        window = window.round_offsets().round_lengths()

        data = source.read(
            window=window,
        )

        transform = source.window_transform(window)

        profile = source.profile.copy()
        profile.update(
            width=data.shape[2],
            height=data.shape[1],
            transform=transform,
            compress="deflate",
        )

        with rasterio.open(
            OUTPUT_FILE,
            "w",
            **profile,
        ) as destination:
            destination.write(data)

    print(f"Kaydedildi: {OUTPUT_FILE}")
    print(f"Raster boyutu: {data.shape[2]} x {data.shape[1]}")


if __name__ == "__main__":
    main()