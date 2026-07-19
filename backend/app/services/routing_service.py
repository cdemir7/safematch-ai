"""
OSRM routing service.

Responsibilities
----------------
- Query the free public OSRM Table API (https://router.project-osrm.org)
  for real road distance/duration between one office point and many
  neighborhood candidate points, in a single request.
- No API key, no cost — but it's a shared public instance, so callers must
  keep the candidate list small (see scoring.scorer.select_top_candidates).

Rules
-----
- Never raises on network/timeout/bad-response errors: returns None per
  destination so the caller can fall back to the haversine-based estimate.
  This is the only place in the app that calls OSRM — scoring/ itself stays
  pure and HTTP-free per CLAUDE.md's architecture rule.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving/"
REQUEST_TIMEOUT_S = 8.0


@dataclass
class TravelEstimate:
    distance_km: float
    duration_min: float


async def get_travel_times(
    origin: tuple[float, float],
    destinations: list[tuple[float, float]],
) -> list[TravelEstimate | None]:
    """
    Ofis (origin) ile her bir mahalle merkezi (destinations) arasındaki
    gerçek karayolu mesafesini ve sürüş süresini tek istekte döner.

    Parameters
    ----------
    origin: (lat, lon)
    destinations: [(lat, lon), ...] — küçük tutulmalı (bkz. scorer.py'daki
        select_top_candidates ön filtresi, genelde 25 civarı).

    Returns
    -------
    list[TravelEstimate | None]
        `destinations` ile aynı sırada ve uzunlukta. Ulaşılamayan noktalar
        veya herhangi bir hata durumunda ilgili eleman(lar) None olur —
        exception fırlatılmaz.
    """
    if not destinations:
        return []

    coords = [origin] + destinations
    coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
    destination_indices = ";".join(str(i) for i in range(1, len(coords)))
    url = f"{OSRM_TABLE_URL}{coord_str}"
    params = {
        "sources": "0",
        "destinations": destination_indices,
        "annotations": "distance,duration",
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning(
            "OSRM Table API isteği başarısız (%d hedef): %s — kuş uçuşu tahmine düşülüyor.",
            len(destinations),
            exc,
        )
        return [None] * len(destinations)

    if data.get("code") != "Ok":
        logger.warning("OSRM Table API 'Ok' dönmedi: %s", data.get("code"))
        return [None] * len(destinations)

    try:
        distances_m = data["distances"][0]
        durations_s = data["durations"][0]
    except (KeyError, IndexError) as exc:
        logger.warning("OSRM Table API yanıt şekli beklenmedik: %s", exc)
        return [None] * len(destinations)

    results: list[TravelEstimate | None] = []
    for dist_m, dur_s in zip(distances_m, durations_s):
        if dist_m is None or dur_s is None:
            results.append(None)
        else:
            results.append(TravelEstimate(distance_km=dist_m / 1000.0, duration_min=dur_s / 60.0))

    return results
