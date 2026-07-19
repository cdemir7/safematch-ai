"""
SafeMatch MCDA Scoring Engine.

Rules
-----
- No HTTP calls.
- No database access.
- No LLM usage.
- Pure deterministic logic. Fully testable.

This module never calls OSRM itself — that HTTP call lives in
services/routing_service.py, and services/recommendation_service.py
orchestrates the two together. What lives here is pure math that turns
"real road distance/duration for a candidate neighborhood" (or, absent
that, a haversine estimate) into a commute-minutes figure, by computing
every transport mode that's actually plausible for that office/neighborhood
pair — road, rail, and ferry — and picking whichever is fastest, the way a
real commuter would.

Workflow
--------
    1. Budget filter        → remove neighborhoods above price threshold
    2. Candidate pre-filter → (optional, office-location flow) nearest
                               COMMUTE_CANDIDATE_LIMIT neighborhoods by
                               straight-line distance, for the caller to
                               fetch real OSRM data for
    3. Weighted sum          → compute composite score per neighborhood,
                                blending in real/estimated commute time
    4. Rank & select         → top-N + alternatives
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from app.scoring.constants import (
    ALTERNATIVE_N,
    AVG_COMMUTE_SPEED_KMH,
    BOSPHORUS_LONGITUDE_SPLIT,
    BUDGET_TOLERANCE,
    COMMUTE_CANDIDATE_LIMIT,
    COMMUTE_TOLERANCE,
    CRITERIA,
    DEFAULT_MAX_COMMUTE_MINUTES,
    DEFAULT_SCORE,
    FERRY_SPEED_KMH,
    FERRY_WAIT_MIN,
    FERRY_WALK_MAX_KM,
    OFFICE_METRO_PROXIMITY_M,
    RAIL_AVG_SPEED_KMH,
    RAIL_CROSS_BOSPHORUS_PENALTY_MIN,
    RAIL_WALK_WAIT_MIN,
    ROAD_CROSS_BOSPHORUS_PENALTY_MIN,
    TOP_N,
    TRAFFIC_MULTIPLIER,
    WALK_SPEED_KMH,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ScoredNeighborhood:
    mahalle_id:    str
    mahalle_adi:   str
    ilce:          str
    geometry:      dict
    avg_m2_fiyat:  int | None
    uygunluk_skoru: float   # 0-100 nihai kompozit skor
    score_breakdown: dict[str, float] = field(default_factory=dict)
    raw:           dict[str, Any] = field(default_factory=dict)


@dataclass
class RoadEstimate:
    """OSRM Table API'den (veya eşdeğer bir kaynaktan) gelen tek bir sonuç."""
    distance_km: float
    duration_min: float


@dataclass
class FerryNetwork:
    """backend/app/data/ferry_terminals.json içeriğinin ayrıştırılmış hali."""
    terminals: dict[str, tuple[float, float]]   # isim -> (lat, lon)
    routes: set[frozenset[str]]                  # {"Üsküdar","Beşiktaş"} gibi çiftler

    @classmethod
    def from_raw(cls, data: dict) -> "FerryNetwork":
        terminals = {t["name"]: (t["lat"], t["lon"]) for t in data.get("terminals", [])}
        routes = {frozenset(pair) for pair in data.get("routes", [])}
        return cls(terminals=terminals, routes=routes)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def polygon_centroid(geometry: dict) -> tuple[float, float] | None:
    """
    Mahalle poligonunun kaba merkezini (lat, lon) döner.

    Gerçek geometrik centroid değil — dış halka(lar)ın köşe noktalarının
    aritmetik ortalamasıdır. mahalle_features.json'daki küçük dörtgenler
    için bu yeterince doğrudur ve shapely'e bağımlılık gerektirmez.
    Hem "Polygon" hem "MultiPolygon" (örn. adalı/parçalı mahalleler —
    mahalle_features_full.json'da 7 tanesi bu tipte) destekler: her parçanın
    dış halkasından toplanan tüm noktaların ortalaması alınır. Geometri
    eksik/boşsa None döner.
    """
    coords = geometry.get("coordinates") if geometry else None
    geom_type = geometry.get("type") if geometry else None
    if not coords:
        return None

    if geom_type == "MultiPolygon":
        # coords: [ [ [outer_ring], [hole], ... ], [ [outer_ring], ... ], ... ]
        rings = [polygon[0] for polygon in coords if polygon]
    else:
        # coords: [ [outer_ring], [hole], ... ] — sadece dış halkayı kullan.
        rings = coords[:1]

    points = [pt for ring in rings for pt in ring]
    if not points:
        return None
    lats = [pt[1] for pt in points]
    lons = [pt[0] for pt in points]
    return (sum(lats) / len(lats), sum(lons) / len(lons))


_EARTH_RADIUS_KM = 6371.0


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """İki (lat, lon) noktası arasındaki kuş uçuşu mesafe (km)."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def _same_bosphorus_side(lon_a: float, lon_b: float) -> bool:
    """İki nokta aynı yakada mı (Avrupa/Anadolu)? Bkz. BOSPHORUS_LONGITUDE_SPLIT."""
    return (lon_a < BOSPHORUS_LONGITUDE_SPLIT) == (lon_b < BOSPHORUS_LONGITUDE_SPLIT)


def find_nearest_stop_distance_m(
    point: tuple[float, float], stops: list[dict]
) -> float | None:
    """
    `point`'e en yakın hızlı transit durağının mesafesini (metre) döner.
    `stops` boşsa None döner. Her stop dict'i "lat"/"lon" anahtarları içermeli
    (bkz. backend/app/data/hizli_transit_stops.json).
    """
    if not stops:
        return None
    return min(haversine_km(point, (s["lat"], s["lon"])) for s in stops) * 1000.0


def _nearest_ferry_terminal(
    point: tuple[float, float], terminals: dict[str, tuple[float, float]]
) -> tuple[str, float] | None:
    """`point`'e en yakın iskeleyi ve kuş uçuşu mesafesini (km) döner."""
    if not terminals:
        return None
    name, coord = min(terminals.items(), key=lambda item: haversine_km(point, item[1]))
    return name, haversine_km(point, coord)


def _ferry_commute_minutes(
    office: tuple[float, float],
    neighborhood_centroid: tuple[float, float],
    ferry: FerryNetwork | None,
) -> float | None:
    """
    Ofis ve mahalle merkezi, aralarında bilinen bir vapur hattı olan iki
    iskeleye yürüme mesafesindeyse (FERRY_WALK_MAX_KM) tahmini kapı-kapı
    vapur süresini (yürüme + geçiş + bekleme) döner. Aksi halde None —
    vapur bu iki nokta için gerçekçi bir seçenek değil demektir.
    """
    if ferry is None or not ferry.terminals or not ferry.routes:
        return None

    office_terminal = _nearest_ferry_terminal(office, ferry.terminals)
    neighborhood_terminal = _nearest_ferry_terminal(neighborhood_centroid, ferry.terminals)
    if office_terminal is None or neighborhood_terminal is None:
        return None

    office_name, office_walk_km = office_terminal
    neighborhood_name, neighborhood_walk_km = neighborhood_terminal
    if office_walk_km > FERRY_WALK_MAX_KM or neighborhood_walk_km > FERRY_WALK_MAX_KM:
        return None
    if office_name == neighborhood_name:
        return None  # aynı iskele — Boğaz geçişi senaryosu değil

    pair = frozenset((office_name, neighborhood_name))
    if pair not in ferry.routes:
        return None

    crossing_km = haversine_km(ferry.terminals[office_name], ferry.terminals[neighborhood_name])
    crossing_min = (crossing_km / FERRY_SPEED_KMH) * 60 + FERRY_WAIT_MIN
    walk_min = ((office_walk_km + neighborhood_walk_km) / WALK_SPEED_KMH) * 60
    return crossing_min + walk_min


# ---------------------------------------------------------------------------
# Budget filter
# ---------------------------------------------------------------------------

def _passes_budget(mahalle: dict, budget_m2: int | None) -> bool:
    """
    Mahalle bütçe filtresini geçiyor mu?

    budget_m2: Kullanıcının TL/m2 bütçesi. None ise filtre uygulanmaz.
    """
    if budget_m2 is None:
        return True
    avg_fiyat = mahalle.get("avg_m2_fiyat")
    if avg_fiyat is None:
        return True  # Fiyat bilgisi yoksa filtreden geçir
    return avg_fiyat <= budget_m2 * BUDGET_TOLERANCE


def filter_by_budget(neighborhoods: list[dict], budget_m2: int | None) -> list[dict]:
    """`_passes_budget`'ı listeye uygular. Orkestrasyon katmanının (OSRM'e
    hangi adaylar için istek atılacağını seçmeden önce) kullanması içindir.
    """
    return [m for m in neighborhoods if _passes_budget(m, budget_m2)]


# ---------------------------------------------------------------------------
# Candidate pre-filter (kuş uçuşu) — OSRM'e gitmeden önce adayı daralt
# ---------------------------------------------------------------------------

def select_top_candidates(
    neighborhoods: list[dict],
    office: tuple[float, float],
    limit: int = COMMUTE_CANDIDATE_LIMIT,
) -> list[dict]:
    """
    900+ mahalleyi kuş uçuşu mesafeye göre sıralar ve en yakın `limit`
    tanesini döner. OSRM ücretsiz public instance'ına sadece bu adaylar
    için istek atılır (performans + nezaket). Centroid çıkarılamayan
    (geometrisi eksik) mahalleler elenir.
    """
    with_distance: list[tuple[float, dict]] = []
    for m in neighborhoods:
        centroid = polygon_centroid(m.get("geometry", {}))
        if centroid is None:
            continue
        with_distance.append((haversine_km(office, centroid), m))

    with_distance.sort(key=lambda pair: pair[0])
    return [m for _, m in with_distance[:limit]]


# ---------------------------------------------------------------------------
# Hybrid commute-minutes formula
# ---------------------------------------------------------------------------

def _hybrid_commute_minutes(
    *,
    road_distance_km: float,
    road_duration_min: float,
    same_side: bool,
    has_rail_at_neighborhood: bool,
    office_has_metro: bool,
    ferry_minutes: float | None = None,
) -> tuple[float, str]:
    """
    OSRM'in gerçek karayolu mesafesi/süresinden — ve varsa vapur/raylı
    sistem seçeneklerinden — en gerçekçi (en hızlı) işe gidiş süresini
    üretir. Gerçek bir commuter gibi, hangi ulaşım biçimi mevcutsa en
    hızlısını seçer; tek bir moda kilitlenmez.

    Karayolu (her zaman hesaplanır): OSRM'in sürüş süresi İstanbul trafiği
    çarpanıyla büyütülür; farklı yakadaysa köprü/tünel trafiği cezası eklenir.

    Raylı sistem (mahallede raylı sistem VE ofis bir raylı sistem/metrobüs
    durağına yakınsa): karayolu mesafesi ortalama raylı sistem hızıyla
    süreye çevrilir + yürüme/bekleme; farklı yakadaysa aktarma cezası eklenir.

    Vapur (ofis ve mahalle merkezine yakın, aralarında bilinen bir hat olan
    iki iskele varsa — bkz. _ferry_commute_minutes): doğrudan kapı-kapı süre.

    Returns
    -------
    (dakika, mod) — mod: "karayolu" | "raylı_sistem" | "vapur"
    """
    road_minutes = road_duration_min * TRAFFIC_MULTIPLIER
    if not same_side:
        road_minutes += ROAD_CROSS_BOSPHORUS_PENALTY_MIN
    candidates: dict[str, float] = {"karayolu": road_minutes}

    if has_rail_at_neighborhood and office_has_metro:
        rail_minutes = (road_distance_km / RAIL_AVG_SPEED_KMH) * 60 + RAIL_WALK_WAIT_MIN
        if not same_side:
            rail_minutes += RAIL_CROSS_BOSPHORUS_PENALTY_MIN
        candidates["raylı_sistem"] = rail_minutes

    if ferry_minutes is not None:
        candidates["vapur"] = ferry_minutes

    best_mode = min(candidates, key=lambda mode: candidates[mode])
    return candidates[best_mode], best_mode


def _commute_estimate(
    mahalle: dict,
    office: tuple[float, float] | None,
    road_data: dict[str, RoadEstimate] | None,
    office_has_metro: bool,
    ferry: FerryNetwork | None = None,
) -> tuple[float, float, str | None] | None:
    """
    (mesafe_km, tahmini_sure_dk, ulaşım_modu) döner; ofis konumu veya
    mahalle geometrisi yoksa None.

    `road_data`'da bu mahalle için gerçek bir OSRM sonucu varsa (aday
    ön-filtresini geçmiş ve OSRM isteği başarılı olmuşsa) karayolu, raylı
    sistem ve vapur seçenekleri hesaplanıp en hızlısı seçilir (bkz.
    _hybrid_commute_minutes). Yoksa — aday listesi dışında kaldıysa ya da
    OSRM isteği başarısız olduysa — kuş uçuşu mesafeden AVG_COMMUTE_SPEED_KMH
    ile kaba bir tahmine düşülür ve ulaşım_modu None döner.
    """
    if office is None:
        return None
    centroid = polygon_centroid(mahalle.get("geometry", {}))
    if centroid is None:
        return None

    road = road_data.get(mahalle["mahalle_id"]) if road_data else None

    if road is not None:
        has_rail = mahalle.get("raw", {}).get("transit_hizli_count", 0) > 0
        same_side = _same_bosphorus_side(office[1], centroid[1])
        ferry_minutes = _ferry_commute_minutes(office, centroid, ferry)
        minutes, mode = _hybrid_commute_minutes(
            road_distance_km=road.distance_km,
            road_duration_min=road.duration_min,
            same_side=same_side,
            has_rail_at_neighborhood=has_rail,
            office_has_metro=office_has_metro,
            ferry_minutes=ferry_minutes,
        )
        return road.distance_km, minutes, mode

    distance_km = haversine_km(office, centroid)
    minutes = (distance_km / AVG_COMMUTE_SPEED_KMH) * 60
    return distance_km, minutes, None


def _commute_proximity_score(minutes: float, max_commute_minutes: int) -> float:
    """
    Süreyi 0-100 "yakınlık" skoruna çevirir: 0 dk → 100, max_commute_minutes
    dk → 0, daha uzağı 0'da sabitlenir. _compute_composite içinde genel
    ulaşım skoruyla harmanlanır.
    """
    if max_commute_minutes <= 0:
        return DEFAULT_SCORE
    score = 100.0 * (1 - minutes / max_commute_minutes)
    return max(0.0, min(100.0, score))


# ---------------------------------------------------------------------------
# Weighted sum
# ---------------------------------------------------------------------------

def _compute_composite(
    scores: dict[str, float],
    weights: dict[str, float],
    calisma_tipi: str = "hibrit",
    commute_proximity: float | None = None,
) -> float:
    """
    Ağırlıklı toplam skoru hesaplar.

    score(mahalle) = Σ w_i × s_i

    Ofis/hibrit çalışanlar için ulaşım skoru yerine
    "ulasim_hizli" (metro + metrobüs + Marmaray) kullanılır.

    commute_proximity verildiyse (kullanıcı ofis konumu işaretlediyse),
    genel ulaşım skoruyla eşit ağırlıkta harmanlanır — böylece hem POI
    yoğunluğu hem de gerçek ofise yakınlık ulaşım kriterine yansır.
    """
    total = 0.0
    for criterion in CRITERIA:
        w = weights.get(criterion, 0.0)
        if criterion == "ulasim" and calisma_tipi in ("ofis", "hibrit"):
            # Hızlı transit skoru varsa onu kullan, yoksa genel skora düş
            s = scores.get("ulasim_hizli") or scores.get(criterion, DEFAULT_SCORE)
            if commute_proximity is not None:
                s = (s + commute_proximity) / 2
        else:
            s = scores.get(criterion, DEFAULT_SCORE)
        total += w * s
    return round(total, 2)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def score_neighborhoods(
    neighborhoods: list[dict],
    weights: dict[str, float],
    budget_m2: int | None = None,
    calisma_tipi: Literal["ofis", "hibrit", "uzaktan"] = "hibrit",
    office_lat: float | None = None,
    office_lon: float | None = None,
    max_commute_minutes: int | None = None,
    road_data: dict[str, RoadEstimate] | None = None,
    hizli_transit_stops: list[dict] | None = None,
    ferry: FerryNetwork | None = None,
) -> tuple[list[ScoredNeighborhood], list[ScoredNeighborhood]]:
    """
    Tüm İstanbul mahallelerini profil ağırlıklarıyla puanlar ve sıralar.

    Parameters
    ----------
    neighborhoods:
        mahalle_features.json'daki mahalle listesi.
    weights:
        profile_to_weights() veya AI weighting'den gelen {kriter: ağırlık} dict.
        Toplamı 1.0 olmalıdır.
    budget_m2:
        Kullanıcının TL/m2 bütçesi. None = filtre yok.
    calisma_tipi:
        "ofis" veya "hibrit" ise hızlı transit (metro/metrobüs/Marmaray)
        skoru genel ulaşım yerine kullanılır.
    office_lat, office_lon:
        Kullanıcının haritada işaretlediği ofis konumu. İkisi de verilmezse
        işe gidiş mesafesi hesaba katılmaz (mevcut davranış korunur).
    max_commute_minutes:
        Kullanıcının kabul edebileceği maksimum işe gidiş süresi. Ofis
        konumu verilmişse, tahmini süre bunun COMMUTE_TOLERANCE katını
        aşan mahalleler bütçe filtresiyle aynı mantıkla elenir.
    road_data:
        {mahalle_id: RoadEstimate} — services.routing_service.get_travel_times
        çağrısından derlenmiş gerçek OSRM sonuçları (bkz. select_top_candidates).
        Bir mahalle burada yoksa (aday dışı kaldıysa ya da OSRM başarısız
        olduysa) kuş uçuşu tahmine düşülür. None = hiç OSRM verisi yok,
        tüm mahalleler için kuş uçuşu tahmin kullanılır.
    hizli_transit_stops:
        backend/app/data/hizli_transit_stops.json içeriği — ofisin bir
        raylı sistem/metrobüs durağına OFFICE_METRO_PROXIMITY_M içinde
        olup olmadığını belirlemek için kullanılır (raylı sistem seçeneği
        için).
    ferry:
        backend/app/data/ferry_terminals.json'dan yüklenmiş FerryNetwork —
        ofis/mahalle bir iskeleye yakınsa ve aralarında bilinen bir vapur
        hattı varsa bu seçenek de değerlendirilir.

    Returns
    -------
    (top_n, alternatives)
        top_n      : İlk TOP_N mahalle, uygunluk skoru azalan sırada.
        alternatives: Sonraki ALTERNATIVE_N mahalle.
    """
    office = (
        (office_lat, office_lon)
        if office_lat is not None and office_lon is not None
        else None
    )
    commute_cap = max_commute_minutes or DEFAULT_MAX_COMMUTE_MINUTES

    office_metro = False
    if office is not None and hizli_transit_stops:
        nearest_m = find_nearest_stop_distance_m(office, hizli_transit_stops)
        office_metro = nearest_m is not None and nearest_m <= OFFICE_METRO_PROXIMITY_M

    scored: list[ScoredNeighborhood] = []

    for m in neighborhoods:
        if not _passes_budget(m, budget_m2):
            continue

        commute = _commute_estimate(m, office, road_data, office_metro, ferry)
        if commute is not None:
            _, minutes, _ = commute
            if minutes > commute_cap * COMMUTE_TOLERANCE:
                continue

        scores_raw = m.get("scores", {})
        commute_proximity = (
            _commute_proximity_score(commute[1], commute_cap)
            if commute is not None
            else None
        )
        composite = _compute_composite(scores_raw, weights, calisma_tipi, commute_proximity)

        raw = dict(m.get("raw", {}))
        if commute is not None:
            distance_km, minutes, mode = commute
            raw["ofis_mesafesi_km"] = round(distance_km, 2)
            raw["ofis_tahmini_sure_dk"] = round(minutes, 1)
            raw["ofis_ulasim_modu"] = mode

        scored.append(
            ScoredNeighborhood(
                mahalle_id=m["mahalle_id"],
                mahalle_adi=m["mahalle_adi"],
                ilce=m["ilce"],
                geometry=m.get("geometry", {}),
                avg_m2_fiyat=m.get("avg_m2_fiyat"),
                uygunluk_skoru=composite,
                score_breakdown={k: scores_raw.get(k, DEFAULT_SCORE) for k in CRITERIA},
                raw=raw,
            )
        )

    scored.sort(key=lambda s: s.uygunluk_skoru, reverse=True)

    top_n = scored[:TOP_N]
    alternatives = scored[TOP_N : TOP_N + ALTERNATIVE_N]

    return top_n, alternatives
