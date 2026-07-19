"""
Gemini weighting layer.

Responsibilities
----------------
- Transform user profile into criterion weights via Gemini 2.5 Flash
- Parse and validate structured JSON output
- Apply DEPREM_MIN_WEIGHT constraint on top of AI output
- Fall back to rule-based weights on any error

Safety rules
------------
- Minimum deprem_guvenlik weight is ALWAYS enforced in code, not trusted from AI.
- All AI output is validated with Pydantic before use.
- On timeout, parse error, or API error → fallback to scoring.weights.profile_to_weights()
"""
from __future__ import annotations

import json
import logging
import os
import pathlib

from app.schemas.profile import UserProfile
from app.scoring.constants import CRITERIA, DEPREM_MIN_WEIGHT, MAX_SINGLE_WEIGHT
from app.scoring.normalizer import normalize_weights
from app.scoring.weights import profile_to_weights

logger = logging.getLogger(__name__)

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "weighting_v1.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def _enforce_constraints(weights: dict[str, float]) -> dict[str, float]:
    """Güvenlik kurallarını AI çıktısına uygular (koda güven, AI'ya değil)."""
    # DEPREM_MIN_WEIGHT
    if weights.get("deprem_guvenlik", 0.0) < DEPREM_MIN_WEIGHT:
        deficit = DEPREM_MIN_WEIGHT - weights["deprem_guvenlik"]
        weights["deprem_guvenlik"] = DEPREM_MIN_WEIGHT
        others = {k: v for k, v in weights.items() if k != "deprem_guvenlik"}
        total = sum(others.values())
        if total > 0:
            for k in others:
                weights[k] -= deficit * (weights[k] / total)

    # MAX_SINGLE_WEIGHT
    for k in list(weights.keys()):
        if weights[k] > MAX_SINGLE_WEIGHT:
            excess = weights[k] - MAX_SINGLE_WEIGHT
            weights[k] = MAX_SINGLE_WEIGHT
            others = {ck: cv for ck, cv in weights.items() if ck != k}
            total = sum(others.values())
            if total > 0:
                for ck in others:
                    weights[ck] += excess * (weights[ck] / total)

    return normalize_weights(weights)


def _parse_ai_weights(raw_json: str) -> dict[str, float] | None:
    """JSON string'i parse eder ve şema doğrulaması yapar."""
    try:
        data = json.loads(raw_json.strip())
    except json.JSONDecodeError as exc:
        logger.error("AI weight JSON parse hatası: %s | raw: %s", exc, raw_json[:200])
        return None

    if not isinstance(data, dict):
        logger.error("AI weight yanıtı dict değil: %s", type(data))
        return None

    weights: dict[str, float] = {}
    for criterion in CRITERIA:
        val = data.get(criterion)
        if val is None:
            logger.error("AI weight yanıtında eksik kriter: %s", criterion)
            return None
        try:
            weights[criterion] = float(val)
        except (TypeError, ValueError):
            logger.error("AI weight değeri float'a çevrilemedi: %s=%s", criterion, val)
            return None

    return weights


async def get_weights_from_ai(profile: UserProfile) -> tuple[dict[str, float], str]:
    """
    Gemini API aracılığıyla profili ağırlıklara dönüştürür.

    Returns
    -------
    (weights, source)
        weights : Kriter ağırlıkları dict (toplamı 1.0)
        source  : "ai" veya "rule_based"
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY bulunamadı — kural tabanlı ağırlık kullanılıyor.")
        return _fallback(profile), "rule_based"

    try:
        import google as genai
    except ImportError:
        logger.warning("google kurulu değil — kural tabanlı fallback.")
        return _fallback(profile), "rule_based"

    profile_json = profile.model_dump_json(indent=2)
    prompt = _PROMPT_TEMPLATE.format(profile_json=profile_json)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = await model.generate_content_async(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 256},
        )
        raw_text = response.text.strip()
        logger.debug("Gemini weighting yanıtı: %s", raw_text)

        parsed = _parse_ai_weights(raw_text)
        if parsed is None:
            logger.warning("AI weight parse başarısız — kural tabanlı fallback.")
            return _fallback(profile), "rule_based"

        weights = _enforce_constraints(parsed)
        return {k: round(v, 4) for k, v in weights.items()}, "ai"

    except Exception as exc:
        logger.error("Gemini weighting hatası: %s — kural tabanlı fallback.", exc)
        return _fallback(profile), "rule_based"


def _fallback(profile: UserProfile) -> dict[str, float]:
    """Kural tabanlı ağırlık hesaplama (AI olmadan)."""
    return profile_to_weights(
        deprem_onceligi=profile.deprem_onceligi,
        saglik_onceligi=profile.saglik_onceligi,
        egitim_onceligi=profile.egitim_onceligi,
        ulasim_onceligi=profile.ulasim_onceligi,
        sosyal_onceligi=profile.sosyal_onceligi,
        has_children=profile.has_children,
        has_car=profile.has_car,
        elderly_in_household=profile.elderly_in_household,
        calisma_tipi=profile.calisma_tipi,
        calisma_ilcesi=profile.calisma_ilcesi,
    )
