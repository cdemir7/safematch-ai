from pathlib import Path
import json

import geopandas as gpd
import requests


BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = BASE_DIR / "sources" / "boundaries"
OUTPUT_DIR = BASE_DIR / "output"

DISTRICT_RAW = SOURCE_DIR / "istanbul_ilceler_raw.geojson"
NEIGHBORHOOD_RAW = SOURCE_DIR / "istanbul_mahalleler_raw.geojson"
NEIGHBORHOOD_FIXED = SOURCE_DIR / "istanbul_mahalleler_fixed.geojson"

DISTRICT_OUTPUT = OUTPUT_DIR / "istanbul_ilceler.geojson"
NEIGHBORHOOD_OUTPUT = OUTPUT_DIR / "istanbul_mahalleler.geojson"

DISTRICT_URL = (
    "https://raw.githubusercontent.com/"
    "sahircansurmeli/istanbul-geojson/master/ilce_geojson.json"
)

NEIGHBORHOOD_URL = (
    "https://raw.githubusercontent.com/"
    "sahircansurmeli/istanbul-geojson/master/mahalle_geojson.json"
)


def download_file(url: str, destination: Path) -> None:
    """Download a file and save it to destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    destination.write_bytes(response.content)
    print(f"Downloaded: {destination}")


def validate_json(path: Path) -> None:
    """Raise an error if the file is not valid JSON."""
    with path.open("r", encoding="utf-8") as file:
        json.load(file)

    print(f"Valid JSON: {path}")


def repair_neighborhood_geojson(source: Path, destination: Path) -> None:
    """
    Repair the known missing comma in the source neighborhood GeoJSON.
    """
    lines = source.read_text(encoding="utf-8").splitlines()

    target_index = 42701

    if len(lines) <= target_index:
        raise ValueError("Neighborhood GeoJSON is shorter than expected.")

    current_line = lines[target_index].rstrip()

    if not current_line.endswith(","):
        lines[target_index] = current_line + ","

    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"Repaired copy created: {destination}")


def validate_geodata(
    districts: gpd.GeoDataFrame,
    neighborhoods: gpd.GeoDataFrame,
) -> None:
    """Validate basic record counts and coordinate systems."""
    if len(districts) != 39:
        raise ValueError(f"Expected 39 districts, found {len(districts)}.")

    if len(neighborhoods) != 968:
        raise ValueError(
            f"Expected 968 neighborhoods, found {len(neighborhoods)}."
        )

    if districts.crs is None or neighborhoods.crs is None:
        raise ValueError("CRS information is missing.")

    print(f"District count: {len(districts)}")
    print(f"Neighborhood count: {len(neighborhoods)}")
    print(f"District CRS: {districts.crs}")
    print(f"Neighborhood CRS: {neighborhoods.crs}")


def build_clean_neighborhood_layer(
    districts: gpd.GeoDataFrame,
    neighborhoods: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Assign each neighborhood to a district using spatial matching."""

    districts = districts.copy()
    neighborhoods = neighborhoods.copy()

    districts["ilce_adi"] = (
        districts["display_name"]
        .str.split(",")
        .str[0]
        .str.strip()
    )
    districts["ilce_osm_id"] = districts["osm_id"]

    def extract_neighborhood_name(
        address: object,
        display_name: str,
    ) -> str:
        if isinstance(address, dict):
            for key in ("suburb", "city", "neighbourhood"):
                value = address.get(key)

                if value:
                    return str(value).strip()

        return display_name.split(",")[0].strip()

    neighborhoods["mahalle_adi"] = neighborhoods.apply(
        lambda row: extract_neighborhood_name(
            row["address"],
            row["display_name"],
        ),
        axis=1,
    )

    neighborhoods["mahalle_osm_id"] = neighborhoods["osm_id"]

    district_layer = districts[
        ["ilce_adi", "ilce_osm_id", "geometry"]
    ].copy()

    neighborhood_layer = neighborhoods[
        ["mahalle_adi", "mahalle_osm_id", "geometry"]
    ].copy()

    neighborhood_points = neighborhood_layer.copy()
    neighborhood_points["geometry"] = (
        neighborhood_points.geometry.representative_point()
    )

    matched = gpd.sjoin(
        neighborhood_points,
        district_layer,
        how="left",
        predicate="within",
    ).sort_index()

    neighborhood_layer["ilce_adi"] = matched["ilce_adi"]
    neighborhood_layer["ilce_osm_id"] = matched["ilce_osm_id"]

    missing_mask = neighborhood_layer["ilce_adi"].isna()
    missing_count = int(missing_mask.sum())

    print(f"Neighborhoods without district match: {missing_count}")

    if missing_count > 0:
        districts_metric = district_layer.to_crs(epsg=3857)

        missing_points = neighborhood_layer.loc[
            missing_mask,
            ["mahalle_adi", "mahalle_osm_id", "geometry"],
        ].copy()

        missing_points["geometry"] = (
            missing_points.geometry.representative_point()
        )
        missing_points = missing_points.to_crs(epsg=3857)

        nearest_matches = gpd.sjoin_nearest(
            missing_points,
            districts_metric,
            how="left",
            distance_col="district_distance_m",
        )

        for index, row in nearest_matches.iterrows():
            neighborhood_layer.loc[index, "ilce_adi"] = row["ilce_adi"]
            neighborhood_layer.loc[index, "ilce_osm_id"] = row["ilce_osm_id"]

            print(
                "Nearest district assignment: "
                f"{neighborhood_layer.loc[index, 'mahalle_adi']} -> "
                f"{row['ilce_adi']} "
                f"({row['district_distance_m']:.1f} m)"
            )

    final_missing_count = int(
        neighborhood_layer["ilce_adi"].isna().sum()
    )
    print(f"Final unmatched neighborhood count: {final_missing_count}")

    return neighborhood_layer[
        [
            "mahalle_adi",
            "ilce_adi",
            "mahalle_osm_id",
            "ilce_osm_id",
            "geometry",
        ]
    ]


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    download_file(DISTRICT_URL, DISTRICT_RAW)
    download_file(NEIGHBORHOOD_URL, NEIGHBORHOOD_RAW)

    validate_json(DISTRICT_RAW)

    try:
        validate_json(NEIGHBORHOOD_RAW)
        neighborhood_input = NEIGHBORHOOD_RAW

    except json.JSONDecodeError:
        print("Neighborhood source JSON is invalid. Applying known repair.")

        repair_neighborhood_geojson(
            NEIGHBORHOOD_RAW,
            NEIGHBORHOOD_FIXED,
        )

        validate_json(NEIGHBORHOOD_FIXED)
        neighborhood_input = NEIGHBORHOOD_FIXED

    districts = gpd.read_file(DISTRICT_RAW)
    neighborhoods = gpd.read_file(neighborhood_input)

    validate_geodata(districts, neighborhoods)

    clean_neighborhoods = build_clean_neighborhood_layer(
        districts,
        neighborhoods,
    )

    districts.to_file(
        DISTRICT_OUTPUT,
        driver="GeoJSON",
    )

    clean_neighborhoods.to_file(
        NEIGHBORHOOD_OUTPUT,
        driver="GeoJSON",
    )

    print(f"Saved: {DISTRICT_OUTPUT}")
    print(f"Saved: {NEIGHBORHOOD_OUTPUT}")


if __name__ == "__main__":
    main()