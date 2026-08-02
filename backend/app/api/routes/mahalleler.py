"""
Genel mahalle listesi rotası.

Responsibilities
----------------
- GET /api/v1/mahalleler – İstanbul'daki tüm mahallelerin poligonu + deprem
  güvenlik skorunu döndürür (kullanıcı profilinden bağımsız, genel harita için)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from app.schemas.mahalleler import MahalleSummary, MahallelerResponse
from app.services.recommendation_service import load_features

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mahalleler", tags=["Mahalleler"])


@router.get(
    "",
    response_model=MahallelerResponse,
    summary="List all Istanbul neighborhoods with earthquake safety score",
    description=(
        "Kullanıcı profilinden bağımsız, İstanbul'daki tüm mahallelerin "
        "poligonu ve deprem güvenlik skorunu döndürür. Landing page'deki "
        "genel harita için kullanılır."
    ),
)
async def get_mahalleler() -> MahallelerResponse:
    neighborhoods = load_features()
    mahalleler = [
        MahalleSummary(
            mahalle_id=n["mahalle_id"],
            mahalle_adi=n["mahalle_adi"],
            ilce=n["ilce"],
            deprem_guvenlik=n["scores"]["deprem_guvenlik"],
            geometry=n["geometry"],
        )
        for n in neighborhoods
    ]
    return MahallelerResponse(mahalleler=mahalleler, total=len(mahalleler))
