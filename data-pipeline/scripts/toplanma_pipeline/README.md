# toplanma_pipeline/ — AFAD acil toplanma alanı eşleştirme

Bu alt klasör, her mahalleye en yakın AFAD acil toplanma alanını eşleştiren
tek seferlik script zincirini bir arada tutar. `data-pipeline/scripts/`
kökündeki `NN_isim.py` scriptlerinin aksine bunlar `DATA_DIR`/`OUTPUT_DIR`
sabitleri kullanmaz — dosya adlarını **çalıştırıldıkları dizine göreli**
olarak açar. Yeniden çalıştırmadan önce ham girdi dosyalarını (OSM Overpass
çıktısı, ilçe/mahalle geojson'ları) script ile aynı dizine kopyalayın.

## Çalışma sırası

1. **01_fetch_assembly_points.py** — Overpass API'den `emergency=assembly_point`
   noktalarını çeker → `istanbul_toplanma_alanlari.json`.
2. **02_merge_mahalle_ilce.py** — mahalle + ilçe poligonlarını spatial join
   ile birleştirir (bu script'in çıktısı `../../output/istanbul_mahalle_ilce_birlesik.geojson`
   ile aynı köke sahiptir).
3. **03_assign_assembly_points_raw.py** — toplanma alanı noktalarını ham
   olarak mahallelerle ilişkilendirmeye çalışan ara adım.
4. **04_match_nearest_assembly_point.py** — her mahalle merkezine **en yakın**
   toplanma alanını (isim, koordinat, mesafe metre) eşleştirir → çıktısı
   `../../output/mahalle_toplanma_eslesme.geojson`.

## Neden ayrı tutuluyor?

Bu scriptler farklı bir katkı sağlayıcı tarafından ad-hoc olarak yazıldı ve
kökteki numaralı pipeline'ın (`01_fetch_boundaries.py` → … →
`07_enrich_mahalle_features.py`) konvansiyonlarını (parametrik `DATA_DIR`,
`--help`, idempotent yeniden çalıştırma) takip etmiyor. Üretilen çıktılar
(`output/mahalle_toplanma_eslesme.geojson`, `output/istanbul_mahalle_ilce_birlesik.geojson`)
zaten `git` ile takip ediliyor ve `07_enrich_mahalle_features.py` tarafından
tüketiliyor — bu scriptleri yeniden çalıştırmak zorunda değilsiniz. Zamanla
kök pipeline konvansiyonuna taşınabilirler; şimdilik hızlı bulunabilmeleri
için burada gruplandı.
