"""
Unit tests: scoring/scorer.py
"""
from __future__ import annotations

import pytest
from app.scoring.constants import (
    ALTERNATIVE_N,
    BUDGET_TOLERANCE,
    RAIL_CROSS_BOSPHORUS_PENALTY_MIN,
    ROAD_CROSS_BOSPHORUS_PENALTY_MIN,
    TOP_N,
    TRAFFIC_MULTIPLIER,
)
from app.scoring.scorer import (
    FerryNetwork,
    RoadEstimate,
    ScoredNeighborhood,
    _ferry_commute_minutes,
    _hybrid_commute_minutes,
    _same_bosphorus_side,
    filter_by_budget,
    find_nearest_stop_distance_m,
    polygon_centroid,
    score_neighborhoods,
    select_top_candidates,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def _make_mahalle(
    mahalle_id: str,
    mahalle_adi: str = "Test Mahallesi",
    ilce: str = "Test İlçe",
    deprem: float = 50.0,
    saglik: float = 50.0,
    egitim: float = 50.0,
    ulasim: float = 50.0,
    sosyal: float = 50.0,
    yasam: float = 50.0,
    fiyat: int | None = 30_000,
    centroid: tuple[float, float] | None = None,
) -> dict:
    if centroid is not None:
        lat, lon = centroid
        geometry = {
            "type": "Polygon",
            "coordinates": [[[lon, lat], [lon, lat], [lon, lat], [lon, lat]]],
        }
    else:
        geometry = {"type": "Polygon", "coordinates": []}

    return {
        "mahalle_id": mahalle_id,
        "mahalle_adi": mahalle_adi,
        "ilce": ilce,
        "geometry": geometry,
        "avg_m2_fiyat": fiyat,
        "scores": {
            "deprem_guvenlik": deprem,
            "saglik": saglik,
            "egitim": egitim,
            "ulasim": ulasim,
            "sosyal_yasam": sosyal,
            "yasam_kalitesi": yasam,
        },
        "raw": {},
    }


EQUAL_WEIGHTS: dict[str, float] = {
    "deprem_guvenlik": 1 / 6,
    "saglik":          1 / 6,
    "egitim":          1 / 6,
    "ulasim":          1 / 6,
    "sosyal_yasam":    1 / 6,
    "yasam_kalitesi":  1 / 6,
}

# 9 mahalle: farklı deprem skorlarıyla
_NEIGHBORHOODS = [
    _make_mahalle(f"M{i:02d}", deprem=float(i * 10), fiyat=30_000)
    for i in range(1, 10)   # M01(10) … M09(90)
]


class TestOutputTypes:
    def test_returns_tuple_of_lists(self):
        top, alt = score_neighborhoods(_NEIGHBORHOODS, EQUAL_WEIGHTS)
        assert isinstance(top, list)
        assert isinstance(alt, list)

    def test_items_are_scored_neighborhoods(self):
        top, _ = score_neighborhoods(_NEIGHBORHOODS, EQUAL_WEIGHTS)
        for item in top:
            assert isinstance(item, ScoredNeighborhood)


class TestRanking:
    def test_top_n_size(self):
        top, _ = score_neighborhoods(_NEIGHBORHOODS, EQUAL_WEIGHTS)
        assert len(top) == TOP_N

    def test_alternatives_size(self):
        _, alt = score_neighborhoods(_NEIGHBORHOODS, EQUAL_WEIGHTS)
        assert len(alt) == ALTERNATIVE_N

    def test_sorted_descending(self):
        top, alt = score_neighborhoods(_NEIGHBORHOODS, EQUAL_WEIGHTS)
        all_results = top + alt
        scores = [r.uygunluk_skoru for r in all_results]
        assert scores == sorted(scores, reverse=True)

    def test_highest_deprem_wins_with_deprem_heavy_weights(self):
        deprem_weights = {k: 0.0 for k in EQUAL_WEIGHTS}
        deprem_weights["deprem_guvenlik"] = 1.0
        top, _ = score_neighborhoods(_NEIGHBORHOODS, deprem_weights)
        # M09 deprem=90 en yüksek
        assert top[0].mahalle_id == "M09"


class TestBudgetFilter:
    def test_expensive_mahalle_excluded(self):
        neighborhoods = [
            _make_mahalle("CHEAP", fiyat=20_000),
            _make_mahalle("EXPENSIVE", fiyat=100_000),
        ]
        top, alt = score_neighborhoods(neighborhoods, EQUAL_WEIGHTS, budget_m2=20_000)
        all_ids = [r.mahalle_id for r in top + alt]
        assert "EXPENSIVE" not in all_ids
        assert "CHEAP" in all_ids

    def test_budget_tolerance_applied(self):
        # 20_000 * 1.15 = 23_000 → fiyatı 22_500 olan dahil edilmeli
        neighborhoods = [
            _make_mahalle("WITHIN_TOLERANCE", fiyat=22_500),
        ]
        top, alt = score_neighborhoods(neighborhoods, EQUAL_WEIGHTS, budget_m2=20_000)
        assert len(top + alt) == 1

    def test_none_budget_includes_all(self):
        top, alt = score_neighborhoods(_NEIGHBORHOODS, EQUAL_WEIGHTS, budget_m2=None)
        assert len(top) + len(alt) == TOP_N + ALTERNATIVE_N

    def test_no_fiyat_passes_filter(self):
        # Fiyat bilgisi olmayan mahalle filtreden geçmeli
        m = _make_mahalle("NO_PRICE", fiyat=None)
        top, alt = score_neighborhoods([m], EQUAL_WEIGHTS, budget_m2=1_000)
        assert len(top + alt) == 1


class TestOfficeCommute:
    # Kadıköy'e yakın (~0 km) vs. Silivri civarı (~60 km kuş uçuşu)
    NEAR = (40.9838, 29.0262)
    FAR = (41.0736, 28.2470)

    def test_closer_neighborhood_scores_higher_when_transit_tied(self):
        neighborhoods = [
            _make_mahalle("NEAR", ulasim=50.0, centroid=self.NEAR),
            _make_mahalle("FAR", ulasim=50.0, centroid=self.FAR),
        ]
        top, _ = score_neighborhoods(
            neighborhoods,
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=90,
        )
        assert top[0].mahalle_id == "NEAR"

    def test_far_neighborhood_excluded_beyond_tolerance(self):
        neighborhoods = [
            _make_mahalle("NEAR", centroid=self.NEAR),
            _make_mahalle("FAR", centroid=self.FAR),
        ]
        top, alt = score_neighborhoods(
            neighborhoods,
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=10,  # ~4km @ 25km/h; FAR is way beyond tolerance
        )
        ids = [r.mahalle_id for r in top + alt]
        assert "FAR" not in ids
        assert "NEAR" in ids

    def test_no_office_location_leaves_scoring_unaffected(self):
        neighborhoods = [_make_mahalle("M", centroid=self.NEAR)]
        top, _ = score_neighborhoods(neighborhoods, EQUAL_WEIGHTS)
        assert top[0].raw.get("ofis_mesafesi_km") is None

    def test_office_location_populates_raw_distance(self):
        neighborhoods = [_make_mahalle("M", centroid=self.NEAR)]
        top, _ = score_neighborhoods(
            neighborhoods,
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=60,
        )
        assert top[0].raw["ofis_mesafesi_km"] == 0.0

    def test_missing_geometry_skips_commute_without_crashing(self):
        # Default _make_mahalle geometry has empty coordinates.
        neighborhoods = [_make_mahalle("NO_GEOM")]
        top, _ = score_neighborhoods(
            neighborhoods,
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=60,
        )
        assert len(top) == 1
        assert top[0].raw.get("ofis_mesafesi_km") is None


class TestHybridCommuteFormula:
    """_hybrid_commute_minutes: pure OSRM + raylı sistem birleştirme mantığı."""

    def test_rail_used_when_neighborhood_has_rail_and_office_near_metro(self):
        rail_minutes, mode = _hybrid_commute_minutes(
            road_distance_km=17.5,  # 35 km/h → tam 30 dk
            road_duration_min=200.0,  # kasıtlı olarak çok kötü trafik → karayolu asla kazanmaz
            same_side=True,
            has_rail_at_neighborhood=True,
            office_has_metro=True,
        )
        assert rail_minutes == pytest.approx(30.0 + 10.0)  # + yürüme/bekleme
        assert mode == "raylı_sistem"

    def test_road_used_when_neighborhood_has_no_rail(self):
        road_minutes, mode = _hybrid_commute_minutes(
            road_distance_km=17.5,
            road_duration_min=60.0,
            same_side=True,
            has_rail_at_neighborhood=False,
            office_has_metro=True,
        )
        assert road_minutes == pytest.approx(60.0 * TRAFFIC_MULTIPLIER)
        assert mode == "karayolu"

    def test_road_used_when_office_not_near_metro_even_if_neighborhood_has_rail(self):
        road_minutes, mode = _hybrid_commute_minutes(
            road_distance_km=17.5,
            road_duration_min=60.0,
            same_side=True,
            has_rail_at_neighborhood=True,
            office_has_metro=False,
        )
        assert road_minutes == pytest.approx(60.0 * TRAFFIC_MULTIPLIER)
        assert mode == "karayolu"

    def test_fastest_mode_wins_when_both_available(self):
        # road_duration_min çok küçük → karayolu, raylı sistemden daha hızlı olmalı
        minutes, mode = _hybrid_commute_minutes(
            road_distance_km=17.5,
            road_duration_min=5.0,
            same_side=True,
            has_rail_at_neighborhood=True,
            office_has_metro=True,
        )
        assert mode == "karayolu"
        assert minutes == pytest.approx(5.0 * TRAFFIC_MULTIPLIER)

    def test_ferry_used_when_fastest(self):
        minutes, mode = _hybrid_commute_minutes(
            road_distance_km=17.5,
            road_duration_min=60.0,
            same_side=False,
            has_rail_at_neighborhood=True,
            office_has_metro=True,
            ferry_minutes=12.0,
        )
        assert mode == "vapur"
        assert minutes == 12.0

    def test_cross_bosphorus_penalty_applied_to_rail(self):
        same, _ = _hybrid_commute_minutes(
            road_distance_km=10.0, road_duration_min=20.0,
            same_side=True, has_rail_at_neighborhood=True, office_has_metro=True,
        )
        cross, _ = _hybrid_commute_minutes(
            road_distance_km=10.0, road_duration_min=20.0,
            same_side=False, has_rail_at_neighborhood=True, office_has_metro=True,
        )
        assert cross - same == pytest.approx(RAIL_CROSS_BOSPHORUS_PENALTY_MIN)

    def test_cross_bosphorus_penalty_applied_to_road(self):
        same, _ = _hybrid_commute_minutes(
            road_distance_km=10.0, road_duration_min=20.0,
            same_side=True, has_rail_at_neighborhood=False, office_has_metro=False,
        )
        cross, _ = _hybrid_commute_minutes(
            road_distance_km=10.0, road_duration_min=20.0,
            same_side=False, has_rail_at_neighborhood=False, office_has_metro=False,
        )
        assert cross - same == pytest.approx(ROAD_CROSS_BOSPHORUS_PENALTY_MIN)

    def test_same_bosphorus_side(self):
        assert _same_bosphorus_side(28.9, 28.5) is True   # ikisi de Avrupa
        assert _same_bosphorus_side(29.5, 29.8) is True   # ikisi de Anadolu
        assert _same_bosphorus_side(28.9, 29.5) is False  # farklı yaka


class TestCandidatePrefilterAndStops:
    def test_select_top_candidates_returns_closest_first(self):
        near = _make_mahalle("NEAR", centroid=(40.9838, 29.0262))
        far = _make_mahalle("FAR", centroid=(41.0736, 28.2470))
        result = select_top_candidates([far, near], office=(40.9838, 29.0262), limit=10)
        assert [m["mahalle_id"] for m in result] == ["NEAR", "FAR"]

    def test_select_top_candidates_respects_limit(self):
        neighborhoods = [
            _make_mahalle(f"M{i}", centroid=(40.98 + i * 0.001, 29.02))
            for i in range(10)
        ]
        result = select_top_candidates(neighborhoods, office=(40.98, 29.02), limit=3)
        assert len(result) == 3

    def test_select_top_candidates_skips_missing_geometry(self):
        no_geom = _make_mahalle("NO_GEOM")  # empty coordinates
        has_geom = _make_mahalle("HAS_GEOM", centroid=(40.98, 29.02))
        result = select_top_candidates([no_geom, has_geom], office=(40.98, 29.02))
        assert [m["mahalle_id"] for m in result] == ["HAS_GEOM"]

    def test_filter_by_budget_matches_score_neighborhoods_behavior(self):
        cheap = _make_mahalle("CHEAP", fiyat=20_000)
        expensive = _make_mahalle("EXPENSIVE", fiyat=100_000)
        result = filter_by_budget([cheap, expensive], budget_m2=20_000)
        assert [m["mahalle_id"] for m in result] == ["CHEAP"]

    def test_find_nearest_stop_distance_m(self):
        stops = [{"lat": 40.9838, "lon": 29.0262}, {"lat": 41.0, "lon": 29.0}]
        distance = find_nearest_stop_distance_m((40.9838, 29.0262), stops)
        assert distance == pytest.approx(0.0, abs=1.0)

    def test_find_nearest_stop_distance_m_empty_stops(self):
        assert find_nearest_stop_distance_m((40.98, 29.02), []) is None


class TestRoadDataIntegration:
    NEAR = (40.9838, 29.0262)

    def test_road_data_overrides_haversine_estimate(self):
        # Same centroid as office → haversine distance is 0, but a supplied
        # OSRM RoadEstimate with a much larger distance/duration should win.
        m = _make_mahalle("M", centroid=self.NEAR)
        m["raw"]["transit_hizli_count"] = 0  # force "Durum B" (road) branch

        top, _ = score_neighborhoods(
            [m],
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=120,
            road_data={"M": RoadEstimate(distance_km=12.0, duration_min=25.0)},
        )
        assert top[0].raw["ofis_mesafesi_km"] == 12.0
        assert top[0].raw["ofis_tahmini_sure_dk"] == pytest.approx(
            25.0 * TRAFFIC_MULTIPLIER, abs=0.1
        )

    def test_neighborhood_outside_road_data_falls_back_to_haversine(self):
        # road_data provided but doesn't include this mahalle's id → haversine fallback.
        m = _make_mahalle("NOT_IN_ROAD_DATA", centroid=self.NEAR)
        top, _ = score_neighborhoods(
            [m],
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=120,
            road_data={"SOME_OTHER_ID": RoadEstimate(distance_km=5.0, duration_min=10.0)},
        )
        assert top[0].raw["ofis_mesafesi_km"] == 0.0

    def test_office_has_metro_enables_rail_branch(self):
        m = _make_mahalle("M", centroid=self.NEAR)
        m["raw"]["transit_hizli_count"] = 1  # mahallede raylı sistem var

        stops_near_office = [{"lat": self.NEAR[0], "lon": self.NEAR[1], "name": "Test", "type": "metro"}]
        top, _ = score_neighborhoods(
            [m],
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=120,
            road_data={"M": RoadEstimate(distance_km=17.5, duration_min=60.0)},
            hizli_transit_stops=stops_near_office,
        )
        # Rail branch: 17.5/35*60 + 10 = 40.0, not 60*1.4 = 84.0
        assert top[0].raw["ofis_tahmini_sure_dk"] == pytest.approx(40.0, abs=0.1)

    def test_office_far_from_metro_uses_road_branch_despite_rail_neighborhood(self):
        m = _make_mahalle("M", centroid=self.NEAR)
        m["raw"]["transit_hizli_count"] = 1

        stops_far_away = [{"lat": 30.0, "lon": 30.0, "name": "Faraway", "type": "metro"}]
        top, _ = score_neighborhoods(
            [m],
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=self.NEAR[0],
            office_lon=self.NEAR[1],
            max_commute_minutes=120,
            road_data={"M": RoadEstimate(distance_km=17.5, duration_min=60.0)},
            hizli_transit_stops=stops_far_away,
        )
        assert top[0].raw["ofis_tahmini_sure_dk"] == pytest.approx(60.0 * TRAFFIC_MULTIPLIER, abs=0.1)


class TestFerryCommute:
    """_ferry_commute_minutes: iskele eşleşmesi + yürüme/geçiş/bekleme süresi."""

    BESIKTAS = (41.0422, 29.0068)
    USKUDAR = (41.0225, 29.0158)
    KADIKOY = (40.9925, 29.0244)

    def _network(self) -> FerryNetwork:
        return FerryNetwork(
            terminals={
                "Beşiktaş": self.BESIKTAS,
                "Üsküdar": self.USKUDAR,
                "Kadıköy": self.KADIKOY,
            },
            routes={frozenset(("Üsküdar", "Beşiktaş")), frozenset(("Kadıköy", "Beşiktaş"))},
        )

    def test_none_when_no_ferry_network(self):
        assert _ferry_commute_minutes(self.BESIKTAS, self.USKUDAR, None) is None

    def test_none_when_no_route_between_nearest_terminals(self):
        # Üsküdar <-> Kadıköy is not in the route set for this network.
        assert _ferry_commute_minutes(self.USKUDAR, self.KADIKOY, self._network()) is None

    def test_positive_minutes_when_valid_route(self):
        minutes = _ferry_commute_minutes(self.BESIKTAS, self.USKUDAR, self._network())
        assert minutes is not None
        assert minutes > 0

    def test_none_when_office_too_far_from_any_terminal(self):
        far_from_terminals = (41.20, 29.20)
        assert _ferry_commute_minutes(far_from_terminals, self.USKUDAR, self._network()) is None

    def test_none_when_same_nearest_terminal(self):
        point_near_besiktas = (41.0420, 29.0070)
        assert _ferry_commute_minutes(self.BESIKTAS, point_near_besiktas, self._network()) is None


class TestFerryIntegration:
    def test_ferry_wins_when_faster_than_rail_and_road(self):
        besiktas, uskudar = (41.0422, 29.0068), (41.0225, 29.0158)
        m = _make_mahalle("M", centroid=uskudar)
        m["raw"]["transit_hizli_count"] = 1  # rail candidate available too

        ferry = FerryNetwork(
            terminals={"Beşiktaş": besiktas, "Üsküdar": uskudar},
            routes={frozenset(("Üsküdar", "Beşiktaş"))},
        )
        stops_near_office = [{"lat": besiktas[0], "lon": besiktas[1], "name": "Test", "type": "metro"}]

        top, _ = score_neighborhoods(
            [m],
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=besiktas[0],
            office_lon=besiktas[1],
            max_commute_minutes=120,
            # Deliberately bad road/rail data so ferry has to win on merit.
            road_data={"M": RoadEstimate(distance_km=25.0, duration_min=50.0)},
            hizli_transit_stops=stops_near_office,
            ferry=ferry,
        )
        assert top[0].raw["ofis_ulasim_modu"] == "vapur"

    def test_ferry_ignored_when_no_route_available(self):
        besiktas, uskudar = (41.0422, 29.0068), (41.0225, 29.0158)
        m = _make_mahalle("M", centroid=uskudar)

        empty_ferry = FerryNetwork(terminals={}, routes=set())
        top, _ = score_neighborhoods(
            [m],
            EQUAL_WEIGHTS,
            calisma_tipi="ofis",
            office_lat=besiktas[0],
            office_lon=besiktas[1],
            max_commute_minutes=120,
            road_data={"M": RoadEstimate(distance_km=25.0, duration_min=50.0)},
            ferry=empty_ferry,
        )
        assert top[0].raw["ofis_ulasim_modu"] == "karayolu"


class TestEdgeCases:
    def test_fewer_than_top_n(self):
        two = _NEIGHBORHOODS[:2]
        top, alt = score_neighborhoods(two, EQUAL_WEIGHTS)
        assert len(top) == 2
        assert len(alt) == 0

    def test_empty_neighborhoods(self):
        top, alt = score_neighborhoods([], EQUAL_WEIGHTS)
        assert top == []
        assert alt == []

    def test_score_breakdown_present(self):
        top, _ = score_neighborhoods(_NEIGHBORHOODS[:1], EQUAL_WEIGHTS)
        assert "deprem_guvenlik" in top[0].score_breakdown


class TestPolygonCentroid:
    def test_polygon(self):
        geometry = {
            "type": "Polygon",
            "coordinates": [[[29.0, 41.0], [29.1, 41.0], [29.1, 41.1], [29.0, 41.1]]],
        }
        lat, lon = polygon_centroid(geometry)
        assert lat == pytest.approx(41.05)
        assert lon == pytest.approx(29.05)

    def test_multipolygon(self):
        # Adalar gibi parçalı mahalleler için — bkz. mahalle_features_full.json,
        # 7 mahalle bu tipte. Eskiden polygon_centroid coords[0][0]'ı bir nokta
        # sanıp TypeError atıyordu (bkz. select_top_candidates crash, 2026-07-19).
        geometry = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[29.0, 41.0], [29.2, 41.0], [29.1, 41.2]]],
                [[[30.0, 42.0], [30.2, 42.0], [30.1, 42.2]]],
            ],
        }
        result = polygon_centroid(geometry)
        assert result is not None
        lat, lon = result
        assert 41.0 < lat < 42.2
        assert 29.0 < lon < 30.2

    def test_missing_geometry(self):
        assert polygon_centroid({}) is None
        assert polygon_centroid(None) is None
