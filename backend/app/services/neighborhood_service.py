"""
Neighborhood service.

Responsibilities
----------------
- Build Overpass QL queries for nearby POI categories
- Parse Overpass API responses into typed POIItem objects
- Compute Haversine distances and sort results
- Return NearbyResponse to the API layer
"""
from __future__ import annotations

import logging
import math
from typing import List, Optional

from app.schemas.neighborhood import (
    NearbyLocation,
    NearbyResponse,
    POICategory,
    POIItem,
)
from app.utils.overpass_client import run_query

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OSM tag mapping
# Each category maps to one or more (key, value) OSM tag pairs.
# Results whose tags match ANY entry in the list are kept.
# ---------------------------------------------------------------------------

_CATEGORY_TAGS: dict[POICategory, list[tuple[str, str]]] = {
    POICategory.mosque: [
        ("amenity", "place_of_worship"),
        # We further filter by religion=muslim in the QL query
    ],
    POICategory.hospital: [
        ("amenity", "hospital"),
        ("amenity", "clinic"),
        ("amenity", "doctors"),
    ],
    POICategory.school: [
        ("amenity", "school"),
        ("amenity", "university"),
        ("amenity", "college"),
        ("amenity", "kindergarten"),
    ],
    POICategory.assembly_point: [
        ("emergency", "assembly_point"),
        ("amenity", "shelter"),
    ],
}

# ---------------------------------------------------------------------------
# Overpass QL builder
# ---------------------------------------------------------------------------

def _build_query(
    lat: float,
    lon: float,
    radius_m: int,
    categories: List[POICategory],
) -> str:
    """Build a single batched Overpass QL query for all requested categories."""
    around = f"around:{radius_m},{lat},{lon}"
    timeout = min(25, max(10, radius_m // 200))  # scale timeout with radius

    statements: list[str] = []

    for cat in categories:
        if cat == POICategory.mosque:
            # Mosques: place_of_worship filtered by religion=muslim
            for osm_type in ("node", "way"):
                statements.append(
                    f'  {osm_type}[amenity=place_of_worship][religion=muslim]({around});'
                )
        elif cat == POICategory.hospital:
            for tag_key, tag_val in _CATEGORY_TAGS[cat]:
                for osm_type in ("node", "way"):
                    statements.append(
                        f'  {osm_type}[{tag_key}={tag_val}]({around});'
                    )
        elif cat == POICategory.school:
            for tag_key, tag_val in _CATEGORY_TAGS[cat]:
                for osm_type in ("node", "way"):
                    statements.append(
                        f'  {osm_type}[{tag_key}={tag_val}]({around});'
                    )
        elif cat == POICategory.assembly_point:
            for tag_key, tag_val in _CATEGORY_TAGS[cat]:
                for osm_type in ("node", "way"):
                    statements.append(
                        f'  {osm_type}[{tag_key}={tag_val}]({around});'
                    )

    body = "\n".join(statements)
    return (
        f"[out:json][timeout:{timeout}];\n"
        f"(\n"
        f"{body}\n"
        f");\n"
        f"out center;"
    )

# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

_EARTH_RADIUS_M = 6_371_000.0


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in metres between two WGS-84 points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))

# ---------------------------------------------------------------------------
# Element → POIItem parser
# ---------------------------------------------------------------------------

def _classify(tags: dict) -> Optional[tuple[POICategory, str]]:
    """
    Return (category, raw_tag_value) for a tag dict, or None if unrecognised.
    Priority: assembly_point > hospital > school > mosque
    """
    amenity = tags.get("amenity", "")
    emergency = tags.get("emergency", "")
    religion = tags.get("religion", "")

    if emergency == "assembly_point":
        return POICategory.assembly_point, "assembly_point"
    if amenity == "shelter":
        return POICategory.assembly_point, "shelter"
    if amenity in ("hospital", "clinic", "doctors"):
        return POICategory.hospital, amenity
    if amenity in ("school", "university", "college", "kindergarten"):
        return POICategory.school, amenity
    if amenity == "place_of_worship" and religion == "muslim":
        return POICategory.mosque, "place_of_worship"

    return None


def _element_latlon(element: dict) -> Optional[tuple[float, float]]:
    """Extract lat/lon from a node or way (via center) element."""
    if element["type"] == "node":
        return element.get("lat"), element.get("lon")
    # ways returned with `out center;` have a "center" sub-object
    center = element.get("center", {})
    if center:
        return center.get("lat"), center.get("lon")
    return None, None


def _parse_elements(
    elements: list[dict],
    query_lat: float,
    query_lon: float,
    wanted_categories: set[POICategory],
) -> list[POIItem]:
    items: list[POIItem] = []
    seen: set[tuple[str, int]] = set()  # deduplicate by (type, osm_id)

    for el in elements:
        el_type = el.get("type", "node")
        osm_id = el.get("id", 0)
        key = (el_type, osm_id)
        if key in seen:
            continue
        seen.add(key)

        tags = el.get("tags", {})
        classification = _classify(tags)
        if classification is None:
            continue

        cat, tag_val = classification
        if cat not in wanted_categories:
            continue

        lat, lon = _element_latlon(el)
        if lat is None or lon is None:
            continue

        dist = _haversine(query_lat, query_lon, lat, lon)

        items.append(
            POIItem(
                osm_id=osm_id,
                osm_type=el_type,
                name=tags.get("name") or tags.get("name:en") or tags.get("name:tr"),
                category=cat,
                amenity_tag=tag_val,
                lat=lat,
                lon=lon,
                distance_m=round(dist, 1),
            )
        )

    return sorted(items, key=lambda p: p.distance_m)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

ALL_CATEGORIES = list(POICategory)


async def find_nearby_pois(
    lat: float,
    lon: float,
    radius_m: int = 2000,
    categories: Optional[List[POICategory]] = None,
) -> NearbyResponse:
    """
    Query the Overpass API and return nearby POIs.

    Parameters
    ----------
    lat, lon:
        WGS-84 coordinates of the search centre.
    radius_m:
        Search radius in metres.
    categories:
        Which POI categories to include. Defaults to all.

    Returns
    -------
    NearbyResponse
    """
    wanted = list(categories) if categories else ALL_CATEGORIES
    ql = _build_query(lat, lon, radius_m, wanted)

    logger.info(
        "Overpass query | lat=%.6f lon=%.6f radius=%d m categories=%s",
        lat, lon, radius_m, [c.value for c in wanted],
    )
    logger.debug("Overpass QL:\n%s", ql)

    data = await run_query(ql)
    elements: list[dict] = data.get("elements", [])

    items = _parse_elements(elements, lat, lon, set(wanted))

    return NearbyResponse(
        location=NearbyLocation(lat=lat, lon=lon),
        radius_m=radius_m,
        total=len(items),
        results=items,
    )
