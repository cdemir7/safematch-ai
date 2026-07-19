"""
Neighborhood / nearby POI routes.

Responsibilities
----------------
- GET /api/v1/nearby  – return POIs near a given coordinate
- Delegate all business logic to neighborhood_service
"""
from __future__ import annotations

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Query, HTTPException

from app.schemas.neighborhood import NearbyResponse, POICategory
from app.services.neighborhood_service import find_nearby_pois

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nearby", tags=["Nearby POIs"])


@router.get(
    "",
    response_model=NearbyResponse,
    summary="Find nearby POIs",
    description=(
        "Return mosques, hospitals, schools, and assembly points near a given "
        "WGS-84 coordinate using OpenStreetMap data via the Overpass API."
    ),
)
async def get_nearby_pois(
    lat: Annotated[
        float,
        Query(ge=-90, le=90, description="Latitude of the search centre"),
    ],
    lon: Annotated[
        float,
        Query(ge=-180, le=180, description="Longitude of the search centre"),
    ],
    radius_m: Annotated[
        int,
        Query(ge=100, le=50_000, description="Search radius in metres (default 2 000)"),
    ] = 2000,
    categories: Annotated[
        Optional[List[POICategory]],
        Query(description="Filter by category. Repeat the param to select multiple."),
    ] = None,
) -> NearbyResponse:
    """
    **Example**

    ```
    GET /api/v1/nearby?lat=41.0082&lon=28.9784&radius_m=1500
    GET /api/v1/nearby?lat=41.0082&lon=28.9784&radius_m=1500&categories=mosque&categories=hospital
    ```
    """
    try:
        return await find_nearby_pois(
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            categories=categories,
        )
    except Exception as exc:
        logger.error("Overpass query failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch data from the Overpass API. Please try again later.",
        ) from exc
