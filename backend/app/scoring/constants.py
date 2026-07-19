"""
Scoring constants.

Tüm scoring motoru boyunca kullanılan sabitler tek yerde tutulur.
Bu dosyadaki değerleri değiştirmek tüm skorlamayı etkiler — dikkatli ol.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Kriter tanımlayıcıları
# ---------------------------------------------------------------------------

CRITERIA = [
    "deprem_guvenlik",
    "saglik",
    "egitim",
    "ulasim",
    "sosyal_yasam",
    "yasam_kalitesi",
]

# ---------------------------------------------------------------------------
# Ağırlık sınırları
# ---------------------------------------------------------------------------

# Deprem kriteri hiçbir zaman bu değerin altına inemez.
# Kullanıcı deprem önceliğini en düşüğe ayarlasa bile bu kural geçerlidir.
DEPREM_MIN_WEIGHT: float = 0.20

# Tek bir kriter bu değerin üzerine çıkamaz (aşırı baskınlığı önler).
MAX_SINGLE_WEIGHT: float = 0.50

# ---------------------------------------------------------------------------
# Sıralama
# ---------------------------------------------------------------------------

TOP_N: int = 5            # Kullanıcıya sunulan ilk öneriler
ALTERNATIVE_N: int = 3   # Alternatif öneriler (6-8. sıralar)

# ---------------------------------------------------------------------------
# Bütçe filtresi
# ---------------------------------------------------------------------------

# Ortalama m2 fiyatı kullanıcı bütçesinin bu katından fazla olan
# mahalleler listeden çıkarılır.
BUDGET_TOLERANCE: float = 1.15   # %15 tolerans

# Bütçe birimi: TL / m2
# Frontend bu değeri TL/m2 olarak gönderir.

# ---------------------------------------------------------------------------
# Skor ölçeği
# ---------------------------------------------------------------------------

SCORE_MIN: float = 0.0
SCORE_MAX: float = 100.0

# ---------------------------------------------------------------------------
# Veri eksikliği
# ---------------------------------------------------------------------------

# Herhangi bir kriter için veri bulunamazsa kullanılan varsayılan skor.
DEFAULT_SCORE: float = 50.0

# ---------------------------------------------------------------------------
# Ofis konumu / işe gidiş mesafesi
# ---------------------------------------------------------------------------

# Kuş uçuşu mesafeyi kabaca "toplu taşıma + yürüme" süresine çevirmek için
# kullanılan varsayımsal ortalama hız. SADECE ön filtreleme (en yakın 25
# aday) için kullanılır — nihai süre hesabı OSRM + hibrit kurallarıyla
# yapılır (aşağıya bakın). OSRM'e ulaşılamazsa bu da nihai tahmine düşülür.
AVG_COMMUTE_SPEED_KMH: float = 25.0

# Kullanıcı maksimum işe gidiş süresi belirttiyse, tahmini süre bu değerin
# kaç katına kadar toleranslı sayılır (bütçe filtresindeki mantığın aynısı).
COMMUTE_TOLERANCE: float = 1.3

# max_commute_minutes gönderilmediyse kullanılan varsayılan tavan.
DEFAULT_MAX_COMMUTE_MINUTES: int = 60

# OSRM'e sadece kuş uçuşu mesafeye göre en yakın bu kadar mahalle için
# istek atılır (performans + ücretsiz public OSRM instance'ını yormamak).
COMMUTE_CANDIDATE_LIMIT: int = 25

# ---------------------------------------------------------------------------
# Hibrit işe gidiş süresi (OSRM + raylı sistem verisi)
# ---------------------------------------------------------------------------

# Ofis bu mesafenin (metre) içinde bir raylı sistem/metrobüs durağına
# sahipse "office_has_metro = True" kabul edilir.
OFFICE_METRO_PROXIMITY_M: float = 800.0

# Durum A (Metro Bağlantısı): mahallede raylı sistem VE ofis metroya
# yakınsa, OSRM'in karayolu mesafesi bu ortalama raylı sistem hızıyla
# (km/h) süreye çevrilir — trafik yerine tren/metro hızını temsil eder.
RAIL_AVG_SPEED_KMH: float = 35.0

# Durum A'ya eklenen sabit yürüme + bekleme süresi (dakika).
RAIL_WALK_WAIT_MIN: float = 10.0

# Durum A'da mahalle ve ofis farklı yakadaysa (Marmaray/Metrobüs
# aktarması) eklenen ek süre (dakika).
RAIL_CROSS_BOSPHORUS_PENALTY_MIN: float = 15.0

# Durum B (Trafikli Karayolu): OSRM'in sürüş süresi İstanbul trafiğini
# yansıtmak için bu katsayıyla çarpılır.
TRAFFIC_MULTIPLIER: float = 1.4

# Durum B'de mahalle ve ofis farklı yakadaysa (köprü/tünel trafiği)
# eklenen ek süre (dakika).
ROAD_CROSS_BOSPHORUS_PENALTY_MIN: float = 45.0

# Avrupa/Anadolu yaka ayrımı için kullanılan boylam eşiği.
BOSPHORUS_LONGITUDE_SPLIT: float = 29.02

# ---------------------------------------------------------------------------
# Durum C — Vapur (feribot/deniz ulaşımı)
# ---------------------------------------------------------------------------
# Beşiktaş, Kadıköy, Üsküdar gibi iskeleye yakın mahalleler için vapur çoğu
# zaman köprüden arabayla geçmekten VEYA raylı sistem aktarmasından daha
# hızlıdır. Bu yüzden araç/raylı sistem/vapur hep birlikte hesaplanır ve
# en hızlısı seçilir (bkz. scorer._hybrid_commute_minutes).

# Bir noktanın "bir iskeleye yürüme mesafesinde" sayılması için üst sınır (km).
FERRY_WALK_MAX_KM: float = 1.5

# Yürüme hızı (km/h) — hem vapur hem raylı sistem bağlantısı için kullanılır.
WALK_SPEED_KMH: float = 4.5

# Vapurun iskeleler arası kuş uçuşu mesafeyi kat etme hızı (km/h). Gerçek
# sefer hızı değil, kaba bir vekildir (Boğaz akıntısı/duraklama dahil değil).
FERRY_SPEED_KMH: float = 22.0

# İskelede ortalama bekleme süresi (dakika) — sefer sıklığının kaba bir
# vekili.
FERRY_WAIT_MIN: float = 10.0
