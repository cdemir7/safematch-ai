"""
Overpass API async HTTP client.

Responsibilities
----------------
- Build the Overpass interpreter URL
- POST a raw Overpass QL string and return parsed JSON
- Handle timeouts and a single retry on HTTP 429 (rate-limit)

Usage
-----
    from app.utils.overpass_client import run_query

    data = await run_query("[out:json]; node[amenity=hospital](around:500,41.0,28.9); out body;")
"""
from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_TIMEOUT = httpx.Timeout(30.0)
_MAX_RETRIES = 1


async def run_query(ql: str) -> dict:
    """
    POST an Overpass QL query and return the parsed JSON response.

    Parameters
    ----------
    ql:
        A complete Overpass QL string, e.g.::

            [out:json][timeout:25];
            (
              node[amenity=hospital](around:1000,41.0,28.9);
            );
            out center;

    Returns
    -------
    dict
        Parsed Overpass JSON (keys: ``version``, ``generator``, ``elements``, …).

    Raises
    ------
    httpx.HTTPStatusError
        On non-2xx responses after retries.
    httpx.TimeoutException
        When the server takes longer than 30 s.
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                logger.debug("Overpass query attempt %d", attempt + 1)
                response = await client.post(
                    _OVERPASS_URL,
                    data={"data": ql},
                    headers={"Accept": "application/json"},
                )

                if response.status_code == 429:
                    if attempt < _MAX_RETRIES:
                        # Back off 5 seconds before retrying
                        logger.warning("Overpass rate-limited (429). Retrying in 5 s…")
                        await asyncio.sleep(5)
                        continue
                    response.raise_for_status()

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                logger.error("Overpass query timed out (attempt %d)", attempt + 1)
                if attempt >= _MAX_RETRIES:
                    raise

    # Should never reach here
    raise RuntimeError("run_query exhausted retries without returning")
