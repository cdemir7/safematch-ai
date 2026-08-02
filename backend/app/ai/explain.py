"""
Gemini explanation layer.

Responsibilities
----------------
- Generate a Turkish natural-language explanation for a recommended neighborhood
- Ground explanations in actual score data (no hallucination)
- Always include the safety disclaimer
- Fall back to a template-based explanation on any error

Rules
-----
- Never claim something not present in the score data.
- Disclaimer is mandatory in every output.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib

from app.ai.json_utils import log_token_usage, parse_json_loose
from app.scoring.scorer import ScoredNeighborhood
from app.schemas.profile import UserProfile

logger = logging.getLogger(__name__)

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "explain_v1.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")

_BATCH_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "explain_batch_v1.txt"
_BATCH_PROMPT_TEMPLATE = _BATCH_PROMPT_PATH.read_text(encoding="utf-8")

# gemini-flash-lite-latest: Google'ın hep-güncel "lite" flash alias'ı. Lite
# varyantların ücretsiz katmanda normal flash'a göre ~2x RPM kotası var
# (bkz. ai.dev/rate-limit) — free-tier kotasını en verimli kullanan seçenek.
_MODEL_NAME = "gemini-flash-lite-latest"

_DISCLAIMER = (
    "⚠️ Bu analiz istatistiksel bölge verilerine dayanır; "
    "bina bazında güvenlik garantisi değildir."
)


def _template_explanation(result: ScoredNeighborhood, weights: dict[str, float]) -> str:
    """
    AI olmadan, skorlardan otomatik üretilen açıklama.
    Gemini mevcut değilken veya hata durumunda kullanılır.
    """
    sb = result.score_breakdown
    strengths = []
    weaknesses = []

    thresholds = {
        "deprem_guvenlik": ("deprem güvenlik skoru", sb["deprem_guvenlik"]),
        "saglik":          ("sağlık hizmetlerine yakınlık", sb["saglik"]),
        "egitim":          ("eğitim olanakları", sb["egitim"]),
        "ulasim":          ("ulaşım erişimi", sb["ulasim"]),
        "sosyal_yasam":    ("sosyal yaşam çeşitliliği", sb["sosyal_yasam"]),
    }
    for key, (label, score) in thresholds.items():
        if score >= 65:
            strengths.append(label)
        elif score < 40:
            weaknesses.append(label)

    strength_text = (
        f"Bu mahalle {', '.join(strengths[:2])} açısından güçlü bir seçenek."
        if strengths else "Bu mahalle dengeli bir profil sunuyor."
    )
    weakness_text = (
        f" Dikkat edilmesi gereken nokta: {weaknesses[0]}."
        if weaknesses else " Belirgin bir zayıf yön tespit edilmedi."
    )

    return (
        f"{result.mahalle_adi} ({result.ilce}): {strength_text}{weakness_text} "
        f"Genel uygunluk skoru: {result.uygunluk_skoru:.1f}/100. {_DISCLAIMER}"
    )


async def get_explanation(
    result: ScoredNeighborhood,
    profile: UserProfile,
    weights: dict[str, float],
) -> str:
    """
    Mahalle için Türkçe AI açıklaması üretir.

    Parameters
    ----------
    result  : Skorlanmış mahalle objesi.
    profile : Kullanıcı profili (kişiselleştirme için).
    weights : Kullanılan ağırlıklar (şeffaflık için).

    Returns
    -------
    str
        Türkçe açıklama + disclaimer.
        Hata durumunda template tabanlı fallback döner.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _template_explanation(result, weights)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _template_explanation(result, weights)

    mahalle_json = json.dumps({
        "mahalle_adi":     result.mahalle_adi,
        "ilce":            result.ilce,
        "uygunluk_skoru":  result.uygunluk_skoru,
        "score_breakdown": result.score_breakdown.__dict__ if hasattr(result.score_breakdown, "__dict__") else dict(result.score_breakdown),
        "avg_m2_fiyat":    result.avg_m2_fiyat,
        "raw":             result.raw,
    }, ensure_ascii=False, indent=2)

    profile_json = profile.model_dump_json(indent=2)
    weights_json = json.dumps(weights, ensure_ascii=False, indent=2)

    prompt = _PROMPT_TEMPLATE.format(
        mahalle_json=mahalle_json,
        profile_json=profile_json,
        weights_json=weights_json,
    )

    try:
        client = genai.Client(api_key=api_key)
        await log_token_usage(client, _MODEL_NAME, prompt, label="explain")
        response = await client.aio.models.generate_content(
            model=_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                # bkz. weighting.py'deki aynı not — thinking token'ları
                # görünmez şekilde bütçeyi tüketiyor, geniş pay şart.
                max_output_tokens=2048,
            ),
        )
        text = response.text.strip()

        # Disclaimer yoksa ekle
        if "istatistiksel" not in text and "garantisi" not in text:
            text = f"{text} {_DISCLAIMER}"

        return text

    except Exception as exc:
        logger.error("Gemini explain hatası [%s]: %s", result.mahalle_id, exc)
        return _template_explanation(result, weights)


def _neighborhood_payload(result: ScoredNeighborhood) -> dict:
    return {
        "mahalle_adi":     result.mahalle_adi,
        "ilce":            result.ilce,
        "uygunluk_skoru":  result.uygunluk_skoru,
        "score_breakdown": (
            result.score_breakdown.__dict__
            if hasattr(result.score_breakdown, "__dict__")
            else dict(result.score_breakdown)
        ),
        "avg_m2_fiyat":    result.avg_m2_fiyat,
        "raw":             result.raw,
    }


async def get_explanations_batch(
    results: list[ScoredNeighborhood],
    profile: UserProfile,
    weights: dict[str, float],
) -> dict[str, str]:
    """
    Birden fazla mahalle için TEK bir Gemini çağrısıyla Türkçe açıklama üretir.

    Ücretsiz katmanın dakika başına istek kotası çok kısıtlı (bkz. Gemini
    rate-limits) — her mahalle için ayrı `get_explanation` çağrısı yapmak
    (top-5 için 5 istek) kotayı anında dolduruyordu. Bu fonksiyon hepsini
    tek istekte, mahalle_id → açıklama şeklinde JSON olarak ister.

    Returns
    -------
    dict[str, str]
        mahalle_id → açıklama. Toplu çağrı tamamen başarısız olursa HER
        mahalle için template fallback döner; kısmi/parse hatasında sadece
        eksik/geçersiz olan mahalleler için template fallback kullanılır.
    """
    fallback = {r.mahalle_id: _template_explanation(r, weights) for r in results}
    if not results:
        return fallback

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return fallback

    mahalleler_json = json.dumps(
        {r.mahalle_id: _neighborhood_payload(r) for r in results},
        ensure_ascii=False, indent=2,
    )
    profile_json = profile.model_dump_json(indent=2)
    weights_json = json.dumps(weights, ensure_ascii=False, indent=2)

    prompt = _BATCH_PROMPT_TEMPLATE.format(
        mahalleler_json=mahalleler_json,
        profile_json=profile_json,
        weights_json=weights_json,
    )

    try:
        client = genai.Client(api_key=api_key)
        await log_token_usage(client, _MODEL_NAME, prompt, label="explain_batch")
        response = await client.aio.models.generate_content(
            model=_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                # N mahalle için N kat daha fazla görünür çıktı + değişken
                # thinking bütçesi — geniş pay şart (bkz. weighting.py notu).
                max_output_tokens=1024 + 1024 * len(results),
                response_mime_type="application/json",
            ),
        )
        raw_text = response.text.strip()
        parsed = parse_json_loose(raw_text)
        if not isinstance(parsed, dict):
            raise ValueError(f"Beklenen dict, gelen: {type(parsed)}")
    except Exception as exc:
        logger.error("Gemini toplu explain hatası: %s — tümü için template fallback.", exc)
        return fallback

    explanations: dict[str, str] = {}
    for r in results:
        text = parsed.get(r.mahalle_id)
        if not isinstance(text, str) or not text.strip():
            logger.warning(
                "Toplu yanıtta mahalle eksik/geçersiz [%s] — template fallback.",
                r.mahalle_id,
            )
            explanations[r.mahalle_id] = fallback[r.mahalle_id]
            continue
        text = text.strip()
        if "istatistiksel" not in text and "garantisi" not in text:
            text = f"{text} {_DISCLAIMER}"
        explanations[r.mahalle_id] = text

    return explanations
