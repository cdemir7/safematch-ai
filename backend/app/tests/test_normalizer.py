"""
Unit tests: scoring/normalizer.py
"""
from __future__ import annotations

import pytest
from app.scoring.normalizer import clamp, minmax, normalize_weights, percentile_rank


class TestClamp:
    def test_within_range(self):
        assert clamp(50.0) == 50.0

    def test_below_min(self):
        assert clamp(-5.0) == 0.0

    def test_above_max(self):
        assert clamp(110.0) == 100.0

    def test_custom_bounds(self):
        assert clamp(15.0, lo=10.0, hi=20.0) == 15.0
        assert clamp(5.0,  lo=10.0, hi=20.0) == 10.0


class TestMinmax:
    def test_basic(self):
        assert minmax(5.0, 0.0, 10.0) == 50.0

    def test_min_value(self):
        assert minmax(0.0, 0.0, 10.0) == 0.0

    def test_max_value(self):
        assert minmax(10.0, 0.0, 10.0) == 100.0

    def test_invert(self):
        # Yüksek PGA → düşük güvenlik skoru
        assert minmax(10.0, 0.0, 10.0, invert=True) == 0.0
        assert minmax(0.0,  0.0, 10.0, invert=True) == 100.0

    def test_equal_bounds_returns_50(self):
        assert minmax(5.0, 5.0, 5.0) == 50.0

    def test_out_of_range_clamped(self):
        result = minmax(15.0, 0.0, 10.0)
        assert result == 100.0


class TestPercentileRank:
    def test_empty_population(self):
        assert percentile_rank(5.0, []) == 50.0

    def test_top_value(self):
        # En yüksek değer
        assert percentile_rank(10.0, [1, 5, 10]) == 100.0

    def test_bottom_value(self):
        # En düşük değer
        assert percentile_rank(1.0, [1, 5, 10]) == pytest.approx(33.3, abs=0.2)

    def test_median(self):
        pop = list(range(1, 101))
        assert percentile_rank(50.0, pop) == 50.0


class TestNormalizeWeights:
    def test_sums_to_one(self):
        w = {"a": 2.0, "b": 3.0, "c": 5.0}
        result = normalize_weights(w)
        assert abs(sum(result.values()) - 1.0) < 1e-9

    def test_proportions(self):
        w = {"a": 1.0, "b": 1.0}
        result = normalize_weights(w)
        assert result["a"] == pytest.approx(0.5)

    def test_zero_total_equal_distribution(self):
        w = {"a": 0.0, "b": 0.0}
        result = normalize_weights(w)
        assert result["a"] == pytest.approx(0.5)
        assert result["b"] == pytest.approx(0.5)
