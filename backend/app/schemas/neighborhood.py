"""
Neighborhood schemas.

Responsibilities
----------------
- NearbyRequest  – query parameters for the /api/v1/nearby endpoint
- POIItem        – a single point-of-interest returned from OSM/Overpass
- NearbyResponse – top-level response wrapper
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Category enum
# ---------------------------------------------------------------------------

class POICategory(str, Enum):
    mosque         = "mosque"
    hospital       = "hospital"
    school         = "school"
    assembly_point = "assembly_point"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class NearbyRequest(BaseModel):
    """Query parameters accepted by GET /api/v1/nearby."""

    lat: float = Field(..., ge=-90, le=90,  description="Latitude of the search centre")
    lon: float = Field(..., ge=-180, le=180, description="Longitude of the search centre")
    radius_m: int = Field(
        default=2000,
        ge=100,
        le=50_000,
        description="Search radius in metres (100 – 50 000, default 2 000)",
    )
    categories: Optional[List[POICategory]] = Field(
        default=None,
        description=(
            "Limit results to these categories. "
            "Omit to return all categories."
        ),
    )


# ---------------------------------------------------------------------------
# Response items
# ---------------------------------------------------------------------------

class POIItem(BaseModel):
    """A single point-of-interest from OpenStreetMap."""

    osm_id:      int
    osm_type:    str  # "node" | "way" | "relation"
    name:        Optional[str]
    category:    POICategory
    amenity_tag: str          # raw OSM tag value, e.g. "hospital"
    lat:         float
    lon:         float
    distance_m:  float = Field(..., description="Haversine distance from query point (metres)")


class NearbyLocation(BaseModel):
    lat: float
    lon: float


class NearbyResponse(BaseModel):
    """Top-level response for GET /api/v1/nearby."""

    location:  NearbyLocation
    radius_m:  int
    total:     int
    results:   List[POIItem]
