"""
Recommendation routes.

Responsibilities
----------------
- accept a user profile payload
- delegate to recommendation_service for orchestration
- return ranked neighborhood recommendations with explanations

Rules
-----
No business logic here. This module only wires HTTP request/response
to the service layer.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.profile import UserProfile
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import get_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.post(
    "",
    response_model=RecommendationResponse,
    summary="Get personalized neighborhood recommendations",
    description=(
        "Kullanıcı profilini alır, AI (veya kural tabanlı) ağırlıklandırma ile "
        "İstanbul mahallelerini puanlar ve en uygun ilk 5 + 3 alternatif "
        "öneriyi açıklamalarıyla birlikte döndürür."
    ),
)
async def recommend(profile: UserProfile) -> RecommendationResponse:
    try:
        return await get_recommendations(profile)
    except RuntimeError as exc:
        logger.error("Recommendation pipeline failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected recommendation error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Öneri üretilirken beklenmeyen bir hata oluştu.",
        ) from exc
