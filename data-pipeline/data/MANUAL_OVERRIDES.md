# manual_overrides.json — elle düzeltme katmanı

`07_enrich_mahalle_features.py`, hesapladığı her mahalle kaydını yazmadan
hemen önce bu dosyadaki girdileri **üstüne** uygular. Otomatik pipeline
yanlış/eksik bir değer üretirse (ör. bir mahallenin fiyatı gerçekte proxy'den
çok farklıysa, ya da gerçek POI sayımı elde ettiyseniz) veriyi burada
düzeltin — script'i veya diğer ham verileri değiştirmenize gerek yok.

## Format

Anahtar, mahallenin `mahalle_osm_id` değeridir (aynı zamanda çıktıdaki
`mahalle_id` alanı — `istanbul_mahalleler.geojson` içindeki
`properties.mahalle_osm_id`'den gelir). Değer, çıktı kaydıyla aynı şekle
sahip **kısmi** bir obje olabilir — sadece düzeltmek istediğiniz alanları
yazın:

```json
{
  "9460396": {
    "scores": { "deprem_guvenlik": 61.5 },
    "raw": { "hastane_count": 2, "okul_count": 4 },
    "avg_m2_fiyat": 88000,
    "not": "AFAD saha ziyareti 2026-06 — bkz. SOURCES.md #7"
  }
}
```

Kurallar:
- `scores` içindeki her alan `backend/app/scoring/constants.py::CRITERIA`
  ile aynı adları kullanmalı (`deprem_guvenlik`, `saglik`, `egitim`,
  `ulasim`, `sosyal_yasam`, `yasam_kalitesi`) — `ulasim_hizli` de kabul edilir.
- `raw` içindeki alanlar sayaçlardır (`hastane_count`, `okul_count`,
  `cami_count`, `toplanma_count`, ...).
- `not` alanı zorunlu değil ama **şiddetle tavsiye edilir** — neden elle
  düzeltildiğini gelecekteki geliştiriciye anlatır.
- Üzerine yazılan her alan, çıktıdaki `data_quality` bloğunda
  `"manuel_duzeltme"` olarak işaretlenir, böylece hangi verinin elle
  girildiği her zaman izlenebilir kalır (CLAUDE.md ilke 3 ve 4).

## Otomasyon ile ilişkisi

Gerçek POI/ulaşım/fiyat pipeline'ları (Faz 1'in geri kalanı) tamamlandığında,
o pipeline'ların ürettiği veriler otomatik olarak `scores`/`raw` alanlarını
dolduracak ve bu override'lar gereksiz hale gelecek — o noktada ilgili
girdiyi bu dosyadan silin. Bu dosya kalıcı bir "gerçek veri" kaynağı değil,
otomatik pipeline tamamlanana kadar kullanılan bir **yama katmanıdır**.
