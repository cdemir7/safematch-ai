"""
Recommendation service.

Orchestrates the full SafeMatch recommendation pipeline:

    1. Load mahalle_features_full.json (cached at startup; override with
       FEATURES_PATH env var, e.g. to fall back to the 16-entry hand-curated
       mahalle_features.json)
    2. AI weighting  → profile → {criterion: weight}  (Gemini or rule-based fallback)
    3. Scoring       → weighted MCDA → ranked neighborhoods
    4. AI explain    → Turkish explanation per top-N result  (Gemini or template fallback)
    5. Build RecommendationResponse

Rules
-----
- This module orchestrates; it does NOT contain business logic.
- Scoring logic lives in app.scoring.*
- AI logic lives in app.ai.*
"""
from __future__ import annotations

import asyncio
import json
import logging
import pathlib
import os

from app.ai.explain import get_explanation
from app.ai.weighting import get_weights_from_ai
from app.schemas.profile import UserProfile
from app.schemas.recommendation import (
    NeighborhoodResult,
    RawData,
    RecommendationResponse,
    ScoreBreakdown,
)
from app.scoring.scorer import (
    FerryNetwork,
    RoadEstimate,
    ScoredNeighborhood,
    filter_by_budget,
    polygon_centroid,
    score_neighborhoods,
    select_top_candidates,
)
from app.services.routing_service import get_travel_times

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature store (loaded once at startup)
# ---------------------------------------------------------------------------

_FEATURES_PATH = pathlib.Path(
    os.getenv(
        "FEATURES_PATH",
        str(pathlib.Path(__file__).parent.parent / "data" / "mahalle_features_full.json"),
    )
)

_TRANSIT_STOPS_PATH = pathlib.Path(
    os.getenv(
        "TRANSIT_STOPS_PATH",
        str(pathlib.Path(__file__).parent.parent / "data" / "hizli_transit_stops.json"),
    )
)

_FERRY_TERMINALS_PATH = pathlib.Path(
    os.getenv(
        "FERRY_TERMINALS_PATH",
        str(pathlib.Path(__file__).parent.parent / "data" / "ferry_terminals.json"),
    )
)

_NEIGHBORHOOD_CACHE: list[dict] | None = None
_TRANSIT_STOPS_CACHE: list[dict] | None = None
_FERRY_NETWORK_CACHE: FerryNetwork | None = None


def load_features() -> list[dict]:
    """mahalle_features.json dosyasını yükler (ilk çağrıda cache'e alır)."""
    global _NEIGHBORHOOD_CACHE
    if _NEIGHBORHOOD_CACHE is not None:
        return _NEIGHBORHOOD_CACHE

    if not _FEATURES_PATH.exists():
        logger.error(
            "mahalle_features.json bulunamadı: %s\n"
            "Lütfen data-pipeline/scripts/05_build_features.py scriptini çalıştırın.",
            _FEATURES_PATH,
        )
        return []

    data = json.loads(_FEATURES_PATH.read_text(encoding="utf-8"))
    _NEIGHBORHOOD_CACHE = data
    logger.info("Mahalle feature'ları yüklendi: %d mahalle (%s)", len(data), _FEATURES_PATH)
    return data


def load_transit_stops() -> list[dict]:
    """hizli_transit_stops.json dosyasını yükler (ilk çağrıda cache'e alır).

    Dosya yoksa/boşsa sessizce boş liste döner — ofis konumu ⇄ metro
    yakınlığı hesaplanamaz, scorer bu durumda tüm mahalleleri "Durum B"
    (trafikli karayolu) formülüyle değerlendirir. Bu bir hata değildir.
    """
    global _TRANSIT_STOPS_CACHE
    if _TRANSIT_STOPS_CACHE is not None:
        return _TRANSIT_STOPS_CACHE

    if not _TRANSIT_STOPS_PATH.exists():
        logger.warning("hizli_transit_stops.json bulunamadı: %s", _TRANSIT_STOPS_PATH)
        _TRANSIT_STOPS_CACHE = []
        return _TRANSIT_STOPS_CACHE

    data = json.loads(_TRANSIT_STOPS_PATH.read_text(encoding="utf-8"))
    _TRANSIT_STOPS_CACHE = data
    logger.info("Hızlı transit durakları yüklendi: %d durak (%s)", len(data), _TRANSIT_STOPS_PATH)
    return data


def load_ferry_network() -> FerryNetwork:
    """ferry_terminals.json dosyasını yükler (ilk çağrıda cache'e alır).

    Dosya yoksa/boşsa boş bir FerryNetwork döner — vapur seçeneği hiçbir
    mahalle için hesaba katılmaz, scorer otomatik olarak karayolu/raylı
    sistem seçeneklerine düşer. Bu bir hata değildir.
    """
    global _FERRY_NETWORK_CACHE
    if _FERRY_NETWORK_CACHE is not None:
        return _FERRY_NETWORK_CACHE

    if not _FERRY_TERMINALS_PATH.exists():
        logger.warning("ferry_terminals.json bulunamadı: %s", _FERRY_TERMINALS_PATH)
        _FERRY_NETWORK_CACHE = FerryNetwork(terminals={}, routes=set())
        return _FERRY_NETWORK_CACHE

    data = json.loads(_FERRY_TERMINALS_PATH.read_text(encoding="utf-8"))
    _FERRY_NETWORK_CACHE = FerryNetwork.from_raw(data)
    logger.info(
        "Vapur ağı yüklendi: %d iskele, %d hat (%s)",
        len(_FERRY_NETWORK_CACHE.terminals), len(_FERRY_NETWORK_CACHE.routes), _FERRY_TERMINALS_PATH,
    )
    return _FERRY_NETWORK_CACHE


async def _build_road_data(
    neighborhoods: list[dict],
    office: tuple[float, float],
) -> dict[str, RoadEstimate]:
    """
    En yakın COMMUTE_CANDIDATE_LIMIT mahalle için OSRM'den gerçek karayolu
    mesafe/süre verisi çeker. Aday dışı kalan mahalleler bu dict'te yer
    almaz — scorer bunlar için otomatik olarak kuş uçuşu tahmine düşer.
    """
    candidates = select_top_candidates(neighborhoods, office)
    centroids = [polygon_centroid(m["geometry"]) for m in candidates]

    # select_top_candidates zaten centroid'i olmayanları eledi, ama tip
    # güvenliği için None'ları da filtrele.
    valid = [(m, c) for m, c in zip(candidates, centroids) if c is not None]
    if not valid:
        return {}

    estimates = await get_travel_times(office, [c for _, c in valid])

    road_data: dict[str, RoadEstimate] = {}
    for (mahalle, _), estimate in zip(valid, estimates):
        if estimate is not None:
            road_data[mahalle["mahalle_id"]] = RoadEstimate(
                distance_km=estimate.distance_km,
                duration_min=estimate.duration_min,
            )
    return road_data


def _to_neighborhood_result(
    scored: ScoredNeighborhood,
    explanation: str | None,
) -> NeighborhoodResult:
    """ScoredNeighborhood → NeighborhoodResult (API response modeli)."""
    sb = scored.score_breakdown
    raw = scored.raw

    return NeighborhoodResult(
        mahalle_id=scored.mahalle_id,
        mahalle_adi=scored.mahalle_adi,
        ilce=scored.ilce,
        uygunluk_skoru=scored.uygunluk_skoru,
        score_breakdown=ScoreBreakdown(
            deprem_guvenlik=sb.get("deprem_guvenlik", 50.0),
            saglik=sb.get("saglik", 50.0),
            egitim=sb.get("egitim", 50.0),
            ulasim=sb.get("ulasim", 50.0),
            sosyal_yasam=sb.get("sosyal_yasam", 50.0),
            yasam_kalitesi=sb.get("yasam_kalitesi", 50.0),
        ),
        raw=RawData(
            hastane_count=raw.get("hastane_count", 0),
            okul_count=raw.get("okul_count", 0),
            cami_count=raw.get("cami_count", 0),
            toplanma_count=raw.get("toplanma_count", 0),
            ofis_mesafesi_km=raw.get("ofis_mesafesi_km"),
            ofis_tahmini_sure_dk=raw.get("ofis_tahmini_sure_dk"),
            ofis_ulasim_modu=raw.get("ofis_ulasim_modu"),
        ),
        avg_m2_fiyat=scored.avg_m2_fiyat,
        geometry=scored.geometry,
        ai_aciklama=explanation,
    )


async def get_recommendations(profile: UserProfile) -> RecommendationResponse:
    """
    Kullanıcı profiline göre en uygun İstanbul mahallelerini döndürür.

    Parameters
    ----------
    profile:
        Doğrulanmış kullanıcı profili (POST body).

    Returns
    -------
    RecommendationResponse
        top5, alternatifler, uygulanan ağırlıklar ve AI açıklamaları.
    """
    # 1. Veri yükle
    neighborhoods = load_features()
    if not neighborhoods:
        raise RuntimeError(
            "Mahalle verisi yüklenemedi. "
            "data-pipeline scriptlerini çalıştırarak mahalle_features.json oluşturun."
        )

    # 2. Ağırlıkları belirle (AI veya kural tabanlı)
    weights, weight_source = await get_weights_from_ai(profile)
    logger.info("Ağırlık kaynağı: %s | ağırlıklar: %s  | çalışma: %s",
                weight_source, weights, profile.calisma_tipi)

    # 2b. Ofis konumu verildiyse: bütçeyi geçen mahalleler arasından en
    # yakın COMMUTE_CANDIDATE_LIMIT tanesi için OSRM'den gerçek karayolu
    # verisi çek. Diğer mahalleler scorer içinde kuş uçuşu tahmine düşer.
    road_data: dict[str, RoadEstimate] = {}
    transit_stops: list[dict] = []
    ferry = FerryNetwork(terminals={}, routes=set())
    if profile.office_lat is not None and profile.office_lon is not None:
        office = (profile.office_lat, profile.office_lon)
        budget_eligible = filter_by_budget(neighborhoods, profile.budget_m2)
        road_data = await _build_road_data(budget_eligible, office)
        transit_stops = load_transit_stops()
        ferry = load_ferry_network()
        logger.info(
            "Ofis konumu: %s | OSRM verisi alınan mahalle sayısı: %d/%d | "
            "hızlı transit durak sayısı: %d | vapur iskele sayısı: %d",
            office, len(road_data), len(budget_eligible), len(transit_stops), len(ferry.terminals),
        )

    # 3. Skorla
    top_scored, alt_scored = score_neighborhoods(
        neighborhoods=neighborhoods,
        weights=weights,
        budget_m2=profile.budget_m2,
        calisma_tipi=profile.calisma_tipi,
        office_lat=profile.office_lat,
        office_lon=profile.office_lon,
        max_commute_minutes=profile.max_commute_minutes,
        road_data=road_data,
        hizli_transit_stops=transit_stops,
        ferry=ferry,
    )
    total_considered = len(top_scored) + len(alt_scored)

    # 4. AI açıklamaları (eşzamanlı)
    explain_tasks = [
        get_explanation(r, profile, weights) for r in top_scored
    ]
    explanations = await asyncio.gather(*explain_tasks, return_exceptions=True)

    # Exception'ları None'a çevir
    explanations_clean: list[str | None] = [
        e if isinstance(e, str) else None
        for e in explanations
    ]

    # Alternatifler için açıklama istemiyoruz (hız için)
    alt_explanations: list[str | None] = [None] * len(alt_scored)

    # 5. Response oluştur
    top5_results = [
        _to_neighborhood_result(scored, exp)
        for scored, exp in zip(top_scored, explanations_clean)
    ]
    alt_results = [
        _to_neighborhood_result(scored, exp)
        for scored, exp in zip(alt_scored, alt_explanations)
    ]

    return RecommendationResponse(
        top5=top5_results,
        alternatifler=alt_results,
        applied_weights=weights,
        weight_source=weight_source,
        total_considered=total_considered,
    )
