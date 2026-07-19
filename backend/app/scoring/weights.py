"""
Profile → criterion weight transformation.

Rules
-----
- No HTTP calls.
- No database access.
- No LLM usage.
- Pure deterministic logic. Fully testable.
- Output weights always sum to 1.0.
- deprem_guvenlik weight can never fall below DEPREM_MIN_WEIGHT.
"""
from __future__ import annotations

from typing import Literal

from app.scoring.constants import CRITERIA, DEPREM_MIN_WEIGHT, MAX_SINGLE_WEIGHT
from app.scoring.normalizer import normalize_weights


def profile_to_weights(
    deprem_onceligi: int = 3,
    saglik_onceligi: int = 3,
    egitim_onceligi: int = 3,
    ulasim_onceligi: int = 3,
    sosyal_onceligi: int = 3,
    has_children: bool = False,
    has_car: bool = True,
    elderly_in_household: bool = False,
    calisma_tipi: Literal["ofis", "hibrit", "uzaktan"] = "hibrit",
    calisma_ilcesi: str | None = None,
) -> dict[str, float]:
    """
    Kullanıcı profil tercihlerini MCDA kriter ağırlıklarına dönüştürür.

    Parametreler (hepsi 1-5 arası tam sayı veya bool/literal):
        deprem_onceligi    : Deprem güvenliği önceliği (1=düşük, 5=yüksek)
        saglik_onceligi    : Sağlık hizmetlerine yakınlık önceliği
        egitim_onceligi    : Okul yakınlığı önceliği
        ulasim_onceligi    : Toplu taşıma önceliği
        sosyal_onceligi    : Sosyal yaşam önceliği
        has_children       : Çocuk varlığı → egitim + saglik artar
        has_car            : Araç sahipliği → araç varsa ulaşım ağırlığı azalır
        elderly_in_household: Yaşlı birey → saglik + ulasim artar
        calisma_tipi       : "ofis"/"hibrit" → ulasim önemli; "uzaktan" → etkisi yok
        calisma_ilcesi     : Ofis ilçesi seçildiyse ulasim ek bonus alır

    Returns
    -------
    dict[str, float]
        Toplamı 1.0 olan ağırlık sözlüğü.
        Anahtarlar: CRITERIA listesindekilerle aynı.
    """
    # --- Temel ağırlıklar: kullanıcı tercihlerinden (1-5) ---
    w: dict[str, float] = {
        "deprem_guvenlik": float(deprem_onceligi),
        "saglik":          float(saglik_onceligi),
        "egitim":          float(egitim_onceligi),
        "ulasim":          float(ulasim_onceligi),
        "sosyal_yasam":    float(sosyal_onceligi),
        "yasam_kalitesi":  3.0,   # sabit orta ağırlık (profilde slider yok)
    }

    # --- Kural tabanlı düzeltmeler ---

    # Çocuk varsa eğitim ve sağlık daha önemli
    if has_children:
        w["egitim"]  = min(w["egitim"] + 1.5, 5.0)
        w["saglik"]  = min(w["saglik"] + 0.5, 5.0)

    # Araç yoksa toplu taşıma çok önemli
    if not has_car:
        w["ulasim"] = min(w["ulasim"] + 2.0, 5.0)

    # Yaşlı birey varsa sağlık ve ulaşım artar
    if elderly_in_household:
        w["saglik"] = min(w["saglik"] + 1.0, 5.0)
        w["ulasim"] = min(w["ulasim"] + 0.5, 5.0)

    # ─────────────────────────────────────────────────────────
    # Çalışma tipi → ulaşım ağırlığı etkisi
    # Ofis: her gün işe gidecek → hızlı transit kritik
    # Hibrit: haftada birkaç kez → orta etkisi
    # Uzaktan: ulaşım önemi azalır
    # ─────────────────────────────────────────────────────────
    if calisma_tipi == "ofis":
        ulasim_bonus = 1.5
    elif calisma_tipi == "hibrit":
        ulasim_bonus = 0.75
    else:  # uzaktan
        ulasim_bonus = 0.0

    # Ofis ilçesi seçilmişse transit önemi biraz daha artar
    if calisma_ilcesi and calisma_tipi in ("ofis", "hibrit"):
        ulasim_bonus += 0.5

    if ulasim_bonus > 0:
        w["ulasim"] = min(w["ulasim"] + ulasim_bonus, 5.0)

    # --- Normalize et (toplam = 1.0) ---
    w = normalize_weights(w)

    # --- Taban ağırlık kuralı: deprem hiçbir zaman DEPREM_MIN_WEIGHT'in altına inemez ---
    if w["deprem_guvenlik"] < DEPREM_MIN_WEIGHT:
        deficit = DEPREM_MIN_WEIGHT - w["deprem_guvenlik"]
        w["deprem_guvenlik"] = DEPREM_MIN_WEIGHT
        others = {k: v for k, v in w.items() if k != "deprem_guvenlik"}
        total_others = sum(others.values())
        if total_others > 0:
            for k in others:
                w[k] -= deficit * (w[k] / total_others)

    # --- Maksimum tek kriter sınırı ---
    for k in w:
        if w[k] > MAX_SINGLE_WEIGHT:
            excess = w[k] - MAX_SINGLE_WEIGHT
            w[k] = MAX_SINGLE_WEIGHT
            others = {ck: cv for ck, cv in w.items() if ck != k}
            total_others = sum(others.values())
            if total_others > 0:
                for ck in others:
                    w[ck] += excess * (w[ck] / total_others)

    # Son normalize (yuvarlama hatalarını düzelt)
    w = normalize_weights(w)

    return {k: round(w.get(k, 0.0), 4) for k in CRITERIA}
