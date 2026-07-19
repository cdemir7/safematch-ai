## USGS Global Vs30

- Kaynak: USGS ScienceBase — Global Hybrid Vs30 Map
- Dosya: `vs30_mosaic_median_30c.tif`
- Veri tarihi: 2025
- Erişim tarihi: 19 Temmuz 2026
- Kapsam: Küresel; İstanbul sınırları kırpılarak kullanıldı
- Çözünürlük: 30 arc-second, yaklaşık 900 metre
- Birim: m/s
- Üretilen çıktı: `output/earthquake_neighborhood_vs30.csv`
- Yöntem: Mahalle poligonları raster ile kesiştirildi; ortalama, minimum ve maksimum Vs30 hesaplandı.
- Güven etiketi:
  - 1–3 piksel: düşük
  - 4–9 piksel: orta
  - 10+ piksel: yüksek
- Sınırlamalar: Veri model tabanlı bölgesel bir zemin proxy’sidir. Yerel mikrobölgeleme, sondaj, zemin etüdü veya bina bazlı mühendislik değerlendirmesi yerine geçmez.