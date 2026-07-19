"""
Recommendation response schemas.

Responsibilities
----------------
- NeighborhoodResult  : tek mahalle önerisi (skor kırılımı + geometry + AI açıklama)
- RecommendationResponse : top-5 + alternatifler + uygulanan ağırlıklar
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Her kriter için 0-100 arası bireysel skor."""
    deprem_guvenlik: float
    saglik:          float
    egitim:          float
    ulasim:          float
    sosyal_yasam:    float
    yasam_kalitesi:  float


class RawData(BaseModel):
    """Ham sayım verileri (açıklanabilirlik için)."""
    hastane_count:   int = 0
    okul_count:      int = 0
    cami_count:      int = 0
    toplanma_count:  int = 0
    ofis_mesafesi_km: float | None = Field(
        None,
        description=(
            "Kullanıcının işaretlediği ofis konumuna mesafe (km). Bu mahalle "
            "OSRM aday listesindeyse gerçek karayolu mesafesi, değilse kuş "
            "uçuşu tahmindir. Sadece office_lat/office_lon gönderildiyse hesaplanır."
        ),
    )
    ofis_tahmini_sure_dk: float | None = Field(
        None,
        description=(
            "Tahmini işe gidiş süresi (dakika). Karayolu/raylı sistem/vapur "
            "seçeneklerinden hesaplanabilenlerin en hızlısıdır (bkz. "
            "ofis_ulasim_modu); OSRM verisi yoksa kuş uçuşu kaba tahmindir."
        ),
    )
    ofis_ulasim_modu: Optional[Literal["karayolu", "raylı_sistem", "vapur"]] = Field(
        None,
        description=(
            "ofis_tahmini_sure_dk hangi ulaşım biçimiyle hesaplandı. Sadece "
            "gerçek OSRM verisi mevcutsa doludur — kuş uçuşu tahminde None."
        ),
    )


class NeighborhoodResult(BaseModel):
    """Tek mahalle öneri objesi."""

    mahalle_id:      str
    mahalle_adi:     str
    ilce:            str
    uygunluk_skoru:  float = Field(..., description="0-100 kompozit uygunluk skoru")
    score_breakdown: ScoreBreakdown
    raw:             RawData
    avg_m2_fiyat:    Optional[int] = Field(None, description="Tahmini TL/m2 fiyatı")
    geometry:        Dict[str, Any] = Field(..., description="GeoJSON Polygon")
    ai_aciklama:     Optional[str] = Field(
        None,
        description="Türkçe AI açıklaması (Gemini). Hata durumunda None olabilir.",
    )
    disclaimer: str = Field(
        default=(
            "⚠️ Bu sonuçlar istatistiksel bölge verilerine dayanmaktadır. "
            "Bina bazında güvenlik garantisi verilmez; mühendislik raporu veya "
            "zemin etüdü yerine geçmez."
        ),
        description="Her mahalle sonucunda görünmesi zorunlu sorumluluk reddi metni.",
    )


class RecommendationResponse(BaseModel):
    """POST /api/v1/recommend uç noktasının tam yanıtı."""

    top5:             List[NeighborhoodResult]
    alternatifler:    List[NeighborhoodResult] = Field(
        default_factory=list,
        description="6-8. sıra öneriler (karşılaştırma için)",
    )
    applied_weights:  Dict[str, float] = Field(
        ...,
        description="Skorlamada kullanılan kriter ağırlıkları (şeffaflık)",
    )
    weight_source:    str = Field(
        default="rule_based",
        description="'ai' veya 'rule_based' — ağırlık nereden geldi?",
    )
    total_considered: int = Field(
        ...,
        description="Bütçe filtresi sonrası değerlendirilen mahalle sayısı",
    )
