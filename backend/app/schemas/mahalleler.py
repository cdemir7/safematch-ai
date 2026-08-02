"""
GET /api/v1/mahalleler yanıt şemaları.

Bu endpoint kişiselleştirilmiş öneri akışından bağımsızdır: formu hiç
doldurmadan İstanbul'un tamamını deprem güvenlik skoruna göre gösteren
genel bir harita için kullanılır (landing page).
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class MahalleSummary(BaseModel):
    """Genel harita için tek bir mahallenin özet bilgisi."""

    mahalle_id: str
    mahalle_adi: str
    ilce: str
    deprem_guvenlik: float = Field(
        ..., description="0-100 deprem güvenlik skoru (yüksek = güvenli)"
    )
    geometry: Dict[str, Any] = Field(..., description="GeoJSON Polygon")


class MahallelerResponse(BaseModel):
    """GET /api/v1/mahalleler tam yanıtı."""

    mahalleler: List[MahalleSummary]
    total: int
