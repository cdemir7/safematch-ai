"""
User profile schemas.

Responsibilities
----------------
- Incoming user profile payload validation (Pydantic v2)
- All fields correspond to frontend wizard steps
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    Kullanıcının çok adımlı formdan gönderdiği profil verisi.

    Slider değerleri 1 (düşük öncelik) — 5 (yüksek öncelik) arasındadır.
    """

    # --- Bütçe ---
    budget_m2: Optional[int] = Field(
        default=None,
        ge=1000,
        description="Kullanıcının TL/m2 bütçesi. None ise filtre uygulanmaz.",
    )

    # --- Demografik ---
    has_children: bool = Field(default=False, description="Hanede çocuk var mı?")
    has_car: bool = Field(default=True, description="Araç sahipliği")
    elderly_in_household: bool = Field(
        default=False, description="Hanede yaşlı birey var mı?"
    )

    # --- Tercih slider'ları (1-5) ---
    deprem_onceligi: int = Field(
        default=3, ge=1, le=5,
        description="Deprem güvenliği önceliği",
    )
    saglik_onceligi: int = Field(
        default=3, ge=1, le=5,
        description="Sağlık hizmetlerine yakınlık önceliği",
    )
    egitim_onceligi: int = Field(
        default=3, ge=1, le=5,
        description="Okul yakınlığı önceliği",
    )
    ulasim_onceligi: int = Field(
        default=3, ge=1, le=5,
        description="Toplu taşıma önceliği",
    )
    sosyal_onceligi: int = Field(
        default=3, ge=1, le=5,
        description="Sosyal yaşam önceliği",
    )

    # --- Opsiyonel serbest metin ---
    calisma_tipi: Literal["ofis", "hibrit", "uzaktan"] = Field(
        default="hibrit",
        description="Çalışma tipi: ofis/hibrit için ulaşım ağırlığı artar.",
    )
    calisma_ilcesi: Optional[str] = Field(
        default=None,
        description="Kullanıcının çalıştığı ilçe (ulaşım hesabında kullanılacak)",
    )
    office_lat: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Ofis konumu enlemi (haritadan seçildiyse). Mahalle-ofis mesafesi tahmininde kullanılır.",
    )
    office_lon: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        description="Ofis konumu boylamı (haritadan seçildiyse).",
    )
    max_commute_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Kullanıcının kabul edebileceği maksimum işe gidiş süresi (dakika).",
    )
    free_text: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Serbest tercih açıklaması (AI katmanına iletilir)",
    )
