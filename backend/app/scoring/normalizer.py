"""
Normalization utilities for the SafeMatch scoring engine.

Rules
-----
- No HTTP calls.
- No database access.
- No LLM usage.
- Pure deterministic logic. Fully testable.
"""
from __future__ import annotations

import math
from typing import Sequence


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Değeri [lo, hi] aralığına sıkıştırır."""
    return max(lo, min(hi, value))


def minmax(
    value: float,
    lo: float,
    hi: float,
    *,
    invert: bool = False,
) -> float:
    """
    Ham değeri min-max normalizasyonuyla 0-100 aralığına çevirir.

    Parameters
    ----------
    value:
        Normalize edilecek ham değer.
    lo, hi:
        Beklenen minimum ve maksimum ham değer.
    invert:
        True ise yüksek ham değer düşük skora karşılık gelir.
        Örn.: PGA (g) için invert=True → PGA arttıkça güvenlik azalır.
    """
    if hi == lo:
        return 50.0
    normalized = (value - lo) / (hi - lo)
    normalized = clamp(normalized, 0.0, 1.0)
    if invert:
        normalized = 1.0 - normalized
    return round(normalized * 100.0, 1)


def percentile_rank(value: float, population: Sequence[float]) -> float:
    """
    Verilen değerin popülasyon içindeki yüzdelik sıralamasını 0-100 olarak döner.
    Yüksek yüzdelik = değerin popülasyon içinde görece yüksek olduğu anlamına gelir.

    Örn.: Mahalle için hastane sayısı tüm mahallelerin %80'inden fazlaysa → 80 döner.
    """
    if not population:
        return 50.0
    rank = sum(1 for v in population if v <= value)
    return round((rank / len(population)) * 100.0, 1)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """
    Ağırlıklar dict'ini toplamları 1.0 olacak şekilde normalize eder.
    Sıfır toplamda tüm ağırlıkları eşit dağıtır.
    """
    total = sum(weights.values())
    if total == 0:
        equal = 1.0 / len(weights)
        return {k: equal for k in weights}
    return {k: v / total for k, v in weights.items()}
