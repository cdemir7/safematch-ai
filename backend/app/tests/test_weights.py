"""
Unit tests: scoring/weights.py
"""
from __future__ import annotations

import pytest
from app.scoring.constants import CRITERIA, DEPREM_MIN_WEIGHT, MAX_SINGLE_WEIGHT
from app.scoring.weights import profile_to_weights


def _default_weights() -> dict[str, float]:
    return profile_to_weights()


class TestOutputShape:
    def test_all_criteria_present(self):
        w = _default_weights()
        for c in CRITERIA:
            assert c in w, f"Kriter eksik: {c}"

    def test_sums_to_one(self):
        w = _default_weights()
        # 4 ondalık yuvarlama nedeniyle 1e-4 tolerans kullanıyoruz
        assert abs(sum(w.values()) - 1.0) < 1e-4

    def test_no_negative_weights(self):
        w = _default_weights()
        for k, v in w.items():
            assert v >= 0.0, f"{k} negatif ağırlık: {v}"


class TestDepremMinWeight:
    def test_default_profile_respects_min(self):
        w = _default_weights()
        assert w["deprem_guvenlik"] >= DEPREM_MIN_WEIGHT

    def test_lowest_deprem_priority_still_respects_min(self):
        # Kullanıcı deprem önceliğini 1'e çekse bile taban kural geçerli
        w = profile_to_weights(deprem_onceligi=1)
        assert w["deprem_guvenlik"] >= DEPREM_MIN_WEIGHT

    def test_max_single_weight_not_exceeded(self):
        w = profile_to_weights(deprem_onceligi=5)
        assert w["deprem_guvenlik"] <= MAX_SINGLE_WEIGHT


class TestChildrenBonus:
    def test_children_increases_egitim(self):
        w_no_children = profile_to_weights(has_children=False)
        w_children    = profile_to_weights(has_children=True)
        assert w_children["egitim"] > w_no_children["egitim"]

    def test_children_increases_saglik(self):
        w_no_children = profile_to_weights(has_children=False)
        w_children    = profile_to_weights(has_children=True)
        assert w_children["saglik"] > w_no_children["saglik"]


class TestCarFlag:
    def test_no_car_increases_ulasim(self):
        w_car    = profile_to_weights(has_car=True)
        w_no_car = profile_to_weights(has_car=False)
        assert w_no_car["ulasim"] > w_car["ulasim"]


class TestElderlyBonus:
    def test_elderly_increases_saglik(self):
        w_no  = profile_to_weights(elderly_in_household=False)
        w_yes = profile_to_weights(elderly_in_household=True)
        assert w_yes["saglik"] > w_no["saglik"]


class TestCalismaType:
    def test_ofis_increases_ulasim_vs_uzaktan(self):
        w_ofis    = profile_to_weights(calisma_tipi="ofis")
        w_uzaktan = profile_to_weights(calisma_tipi="uzaktan")
        assert w_ofis["ulasim"] > w_uzaktan["ulasim"]

    def test_hibrit_between_ofis_and_uzaktan(self):
        w_ofis    = profile_to_weights(calisma_tipi="ofis")
        w_hibrit  = profile_to_weights(calisma_tipi="hibrit")
        w_uzaktan = profile_to_weights(calisma_tipi="uzaktan")
        assert w_ofis["ulasim"] >= w_hibrit["ulasim"] >= w_uzaktan["ulasim"]

    def test_calisma_ilcesi_adds_bonus(self):
        w_no_ilce = profile_to_weights(calisma_tipi="ofis", calisma_ilcesi=None)
        w_ilce    = profile_to_weights(calisma_tipi="ofis", calisma_ilcesi="Besiktas")
        assert w_ilce["ulasim"] >= w_no_ilce["ulasim"]

    def test_deprem_min_still_holds_for_heavy_office(self):
        # Ofis + araç yok + yaşlı = ulaşım maksimum basıncı
        w = profile_to_weights(
            calisma_tipi="ofis",
            has_car=False,
            elderly_in_household=True,
            calisma_ilcesi="Sisli",
        )
        assert w["deprem_guvenlik"] >= DEPREM_MIN_WEIGHT
        assert abs(sum(w.values()) - 1.0) < 1e-4
