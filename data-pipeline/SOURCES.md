# Data Sources — SafeMatch AI

Tüm veri kaynakları, indirilme tarihi, lisans ve kapsam bilgisiyle burada belgelenir.

## 1. İdari Sınırlar

| Alan | Değer |
|---|---|
| **Kaynak** | `github.com/sahircansurmeli/istanbul-geojson` |
| **Format** | GeoJSON |
| **Kapsam** | İstanbul mahalle/ilçe idari sınırları |
| **Lisans** | Açık kaynak |
| **İndirilme** | Script: `01_fetch_boundaries.py` |
| **Notlar** | Türkiye İstatistik Kurumu (TÜİK) resmi mahalle sınırlarından türetilmiş |

## 2. POI Verileri (Hastane, Okul, Cami, Toplanma Alanı)

| Alan | Değer |
|---|---|
| **Kaynak** | OpenStreetMap via Overpass API (`overpass-api.de`) |
| **Format** | JSON (Overpass) → `data/poi_raw.json` |
| **Kapsam** | İstanbul bounding box içindeki tüm node/way |
| **Lisans** | ODbL (OpenStreetMap) |
| **İndirilme** | Script: `02_fetch_poi.py` |
| **OSM Taglar** | `amenity=hospital`, `amenity=clinic`, `amenity=school`, `amenity=university`, `amenity=place_of_worship[religion=muslim]`, `emergency=assembly_point` |

## 3. Deprem Risk Verileri

| Alan | Değer |
|---|---|
| **Kaynak** | İBB "Olası Deprem Kayıp Tahminleri" İlçe Kitapçıkları (Mw 7.5 senaryosu) |
| **URL** | `depremzemin.ibb.istanbul` |
| **Format** | Manuel derleme → `data/ilce_deprem.csv` |
| **Kapsam** | İlçe bazında (39 ilçe). **Mahalle ölçeğinde belirsizlik yüksektir.** |
| **Uyarı** | Tekil bina performansı hakkında bilgi içermez. Bölgesel istatistiktir. |
| **İşleme** | Script: `04_earthquake_scores.py` |

## 4. Konut Fiyatı Proxy

| Alan | Değer |
|---|---|
| **Kaynak** | Manuel derlenmiş ilçe bazlı ortalama m2 fiyatı CSV |
| **Format** | `data/ilce_fiyat.csv` |
| **Kapsam** | İlçe bazında (mahalle ortalaması ilçe değeriyle eşleştirilir) |
| **Durum** | ⚠️ Proxy — web scraping ile iyileştirilecek (sonraki sprint) |

## 5. Çıktı

| Dosya | Açıklama |
|---|---|
| `output/mahalle_features.json` | Her mahalle için normalize edilmiş (0-100) skor objesi |

## 6. AFAD Acil Toplanma Alanları

| Alan | Değer |
|---|---|
| **Kaynak** | OpenStreetMap via Overpass API (`emergency=assembly_point`) |
| **Format** | JSON (Overpass) → GeoJSON |
| **Kapsam** | İstanbul geneli toplanma alanı noktaları |
| **Lisans** | ODbL (OpenStreetMap) |
| **İşleme** | `scripts/toplanma_pipeline/` (bkz. o klasördeki README — ad-hoc,
  numaralı kök pipeline konvansiyonunu takip etmiyor) |
| **Çıktı** | `output/mahalle_toplanma_eslesme.geojson` — her mahalleye en
  yakın toplanma alanının adı, koordinatı ve mesafesi (metre) |
| **Kapsama** | 968 mahalleden 966'sı eşleşti (2 mahalle merkezine 1.5 km+ mesafede
  hiç nokta yok — `07_enrich_mahalle_features.py` bunları `data_quality.toplanma
  = "eslesmedi"` ile işaretler) |
| **Sınırlamalar** | OSM'e girilmiş noktalarla sınırlı; resmi e-Devlet/AFAD
  sorgulamasıyla birebir doğrulanmadı. |

## 7. mahalle_features_full.json — Deprem Güvenlik Skoru Metodolojisi

`scripts/07_enrich_mahalle_features.py`, 968 mahallenin tamamı için
`deprem_guvenlik` skorunu şu iki bileşenden üretir (CLAUDE.md §4.2 "zemin
mantığı"):

| Bileşen | Ağırlık | Kaynak | Yön |
|---|---|---|---|
| İlçe hasar oranı | %60 | Bölüm 3 (İBB Mw7.5 senaryosu, `orta_ve_ustu_hasarli_bina / toplam_bina`) | düşük hasar → yüksek skor |
| Mahalle Vs30 | %40 | Bölüm 8 (USGS Vs30) | yüksek Vs30 (daha sert zemin) → yüksek skor |

Her iki bileşen de kendi dağılımı içinde min-max ile 0-100'e ölçeklenir.
İlçe hasar oranı 39 ilçe arasında, Vs30 968 mahalle arasında karşılaştırılır
— böylece aynı ilçedeki mahalleler zemin farkına göre ayrışabilir. Vs30 veya
ilçe verisi eksikse skor sadece mevcut bileşenden hesaplanır ve
`data_quality.deprem_guvenlik` uyarınca etiketlenir (`"kismi_sadece_ilce"`
veya `"veri_yok"`).

⚠️ Bu skor da resmi bir mühendislik değerlendirmesi değildir — bkz. CLAUDE.md
§1.1 sorumluluk reddi.

## 8. USGS Global Vs30 (Zemin Sınıfı Proxy'si)

| Alan | Değer |
|---|---|
| **Kaynak** | USGS ScienceBase — Global Hybrid Vs30 Map |
| **Dosya** | `vs30_mosaic_median_30c.tif` |
| **Veri tarihi** | 2025 |
| **Erişim tarihi** | 19 Temmuz 2026 |
| **Kapsam** | Küresel; İstanbul sınırları kırpılarak kullanıldı |
| **Çözünürlük** | 30 arc-second, yaklaşık 900 metre |
| **Birim** | m/s |
| **Üretilen çıktı** | `output/earthquake_neighborhood_vs30.csv` |
| **Yöntem** | Mahalle poligonları raster ile kesiştirildi; ortalama, minimum ve maksimum Vs30 hesaplandı |
| **Güven etiketi** | 1–3 piksel: düşük · 4–9 piksel: orta · 10+ piksel: yüksek |
| **Sınırlamalar** | Veri model tabanlı bölgesel bir zemin proxy'sidir. Yerel mikrobölgeleme, sondaj, zemin etüdü veya bina bazlı mühendislik değerlendirmesi yerine geçmez. |
