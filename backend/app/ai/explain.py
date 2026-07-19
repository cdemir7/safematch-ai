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

import logging
import os
import pathlib

from app.scoring.scorer import ScoredNeighborhood
from app.schemas.profile import UserProfile

logger = logging.getLogger(__name__)

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "explain_v1.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")

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
        import google.generativeai as genai
    except ImportError:
        return _template_explanation(result, weights)

    import json

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
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = await model.generate_content_async(
            prompt,
            generation_config={"temperature": 0.4, "max_output_tokens": 300},
        )
        text = response.text.strip()

        # Disclaimer yoksa ekle
        if "istatistiksel" not in text and "garantisi" not in text:
            text = f"{text} {_DISCLAIMER}"

        return text

    except Exception as exc:
        logger.error("Gemini explain hatası [%s]: %s", result.mahalle_id, exc)
        return _template_explanation(result, weights)
