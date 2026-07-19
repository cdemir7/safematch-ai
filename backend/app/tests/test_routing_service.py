"""
Unit tests: services/routing_service.py

No real network calls — httpx.AsyncClient.get is monkeypatched with a fake
response so these stay fast and deterministic, same spirit as the rest of
the test suite even though this module itself is I/O by design.
"""
from __future__ import annotations

import asyncio

import httpx
import pytest

from app.services.routing_service import TravelEstimate, get_travel_times


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse | None = None, raise_exc: Exception | None = None):
        self._response = response
        self._raise_exc = raise_exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None):
        if self._raise_exc is not None:
            raise self._raise_exc
        return self._response


def _run(coro):
    return asyncio.run(coro)


class TestGetTravelTimes:
    def test_empty_destinations_short_circuits(self):
        result = _run(get_travel_times((41.0, 29.0), []))
        assert result == []

    def test_successful_response_parsed(self, monkeypatch):
        payload = {
            "code": "Ok",
            "distances": [[1500.0, 3000.0]],
            "durations": [[120.0, 300.0]],
        }
        monkeypatch.setattr(
            "app.services.routing_service.httpx.AsyncClient",
            lambda timeout: _FakeAsyncClient(_FakeResponse(payload)),
        )
        result = _run(
            get_travel_times((41.0, 29.0), [(41.01, 29.01), (41.02, 29.02)])
        )
        assert result == [
            TravelEstimate(distance_km=1.5, duration_min=2.0),
            TravelEstimate(distance_km=3.0, duration_min=5.0),
        ]

    def test_null_entries_become_none(self, monkeypatch):
        payload = {"code": "Ok", "distances": [[None]], "durations": [[None]]}
        monkeypatch.setattr(
            "app.services.routing_service.httpx.AsyncClient",
            lambda timeout: _FakeAsyncClient(_FakeResponse(payload)),
        )
        result = _run(get_travel_times((41.0, 29.0), [(41.01, 29.01)]))
        assert result == [None]

    def test_non_ok_code_returns_all_none(self, monkeypatch):
        payload = {"code": "NoRoute"}
        monkeypatch.setattr(
            "app.services.routing_service.httpx.AsyncClient",
            lambda timeout: _FakeAsyncClient(_FakeResponse(payload)),
        )
        result = _run(get_travel_times((41.0, 29.0), [(41.01, 29.01), (41.02, 29.02)]))
        assert result == [None, None]

    def test_network_error_returns_all_none(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.routing_service.httpx.AsyncClient",
            lambda timeout: _FakeAsyncClient(raise_exc=httpx.ConnectTimeout("timeout")),
        )
        result = _run(get_travel_times((41.0, 29.0), [(41.01, 29.01)]))
        assert result == [None]

    def test_malformed_payload_returns_all_none(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.routing_service.httpx.AsyncClient",
            lambda timeout: _FakeAsyncClient(_FakeResponse({"code": "Ok"})),
        )
        result = _run(get_travel_times((41.0, 29.0), [(41.01, 29.01)]))
        assert result == [None]
