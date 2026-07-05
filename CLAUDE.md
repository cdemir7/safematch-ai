# CLAUDE.md — SafeMatch AI

> Bu dosya, projeyi geliştiren Claude Code (ve insan katkı sağlayanlar) için
> **tek referans noktasıdır**. Yeni bir göreve başlamadan önce bu dosyayı oku.
> Kararların, veri kaynaklarının ve mimari kuralların "doğru kaynağı" burasıdır.

---

## 1. Proje Nedir?

**SafeMatch AI**, İstanbul'da yaşayacağı bölgeyi seçen bireylere,
**deprem güvenliğini karar sürecinin merkezine koyarak** kişiselleştirilmiş
mahalle önerileri sunan yapay zekâ destekli bir karar destek platformudur.

**Akış:** Kullanıcı bir form doldurur → AI kullanıcının önceliklerini belirler
→ İstanbul mahalleleri deprem + yaşam kriterlerine göre puanlanır →
en uygun **ilk 5 mahalle**, her biri için **açıklanabilir gerekçelerle** sunulur.

**Slogan:** _"Benim için İstanbul'da nerede yaşamak en doğru karar?"_

**Odak:** Bölge / mahalle seçimi. (Bina, ilan veya tapu değil.)

### 1.1. Bu Proje NE DEĞİLDİR (Kapsam Dışı — Kesinlikle Uygulanmayacak)

- ❌ Emlak ilanı yayınlama / konut satışı / tapu işlemleri
- ❌ Yapısal / mühendislik analizi (bina taşıyıcı sistem değerlendirmesi)
- ❌ Gerçek zamanlı deprem uyarı / erken uyarı sistemi

> ⚠️ **KRİTİK KURAL — Sorumluluk Reddi (Disclaimer):**
> Uygulama **bina bazında** güvenlik garantisi VERMEZ. Tüm çıktılar
> **bölgesel/istatistiksel risk göstergeleridir** ve mühendislik raporu,
> zemin etüdü veya resmi değerlendirme yerine geçmez.
> Bu uyarı, her sonuç ekranında ve mahalle detayında **görünür şekilde**
> gösterilmelidir. Kaynak verilerin kendisi de (İBB ilçe kitapçıkları) bunu
> açıkça belirtir: mahalle ölçeğinde belirsizlik yüksektir, tekil bina
> performansı hakkında bilgi içermez.

---

## 2. Temel İlkeler (Guiding Principles)

Kod yazarken her kararı bu ilkelerle sına:

1. **Deprem güvenliği her zaman ağırlıklı bir kriterdir.** Kullanıcı deprem
   önceliğine düşük değer verse bile, skorlamada **minimum bir taban ağırlık**
   uygulanır (bkz. Bölüm 6). Deprem kriteri asla 0 ağırlık alamaz.
2. **Açıklanabilirlik (Explainable AI) zorunludur.** Her öneri, "neden bu
   mahalle?" sorusuna somut skor kırılımı + doğal dil açıklamasıyla yanıt verir.
   "Kara kutu" bir skor asla tek başına gösterilmez.
3. **Veri kaynağı şeffaftır.** Her skorun hangi veri setinden türetildiği
   izlenebilir olmalı (traceability). UI'da "kaynak" bilgisi gösterilebilir olmalı.
4. **Belirsizliği gizleme, göster.** Veri eksik veya düşük güvenilirlikteyse
   bunu skorla birlikte belirt (örn. güven aralığı / "veri sınırlı" etiketi).
5. **Kullanıcı yerine karar verme, kullanıcıya karar verdir.** Sistem sıralar ve
   açıklar; nihai kararı kullanıcı verir.

---

## 3. Teknoloji Yığını (Tech Stack)

Proje iki servisten oluşur: **veri/skor servisi (Python)** ve **web arayüzü (Next.js)**.
Geo-veri işleme ağırlıklı olduğu için veri katmanı Python'dır.

### 3.1. Önerilen Yığın (Primary)

| Katman | Teknoloji | Neden |
|---|---|---|
| Frontend | **Next.js 14+ (App Router) + React + TypeScript** | Modern, SSR, harita entegrasyonu kolay |
| Stil | **Tailwind CSS + shadcn/ui** | Hızlı, tutarlı, erişilebilir bileşenler |
| Harita | **MapLibre GL JS** (veya Leaflet) | Açık kaynak, token gerektirmez, polygon boyama |
| Backend / API | **FastAPI (Python 3.11+)** | Skorlama + AI + geo-veri aynı dilde |
| Veri işleme | **pandas, geopandas, shapely, requests** | Mahalle verilerini birleştirme/normalize etme |
| Veritabanı | **PostgreSQL + PostGIS** | Mekânsal sorgular (mahalle içinde nokta sayma vb.) |
| ORM | **SQLAlchemy** (+ GeoAlchemy2) | Python tarafı veri erişimi |
| AI / LLM | **Google Gemini 2.5 Flash**  | Ağırlıklandırma + doğal dil açıklama |
| Cache (ops.) | **Redis** | AI yanıtlarını ve skorları önbelleğe alma |
| Konteyner | **Docker + docker-compose** | PostGIS + servisleri tek komutla ayağa kaldırma |

---

## 4. Kullanılacak Veriler (Data Sources)

Tüm veriler **mahalle (veya en azından ilçe) seviyesine** indirgenip tek bir
"özellik tablosu"nda (`mahalle_features`) birleştirilir. Kaynakların çoğu resmî
kurumlardan gelir; bazıları manuel derleme gerektirir.

### 4.1. İdari Sınırlar (Temel Katman)
- **İstanbul ilçe/mahalle GeoJSON:** `github.com/sahircansurmeli/istanbul-geojson`
  (hazır poligon sınırları — haritanın temel katmanı).
- **TurkiyeAPI** (il/ilçe/mahalle REST API): idari kod eşleştirme, isim doğrulama.

### 4.2. Deprem Güvenliği Verileri (Projenin Kalbi)
- **İBB "Olası Deprem Kayıp Tahminleri" İlçe Kitapçıkları (Mw 7.5 senaryosu):**
  `depremzemin.ibb.istanbul` → 39 ilçe için üstyapı/altyapı hasarı, can kaybı/
  yaralı tahmini, yol kapanma, geçici barınma. **İlçe bazında** güvenilir.
  ⚠️ Mahalle ölçeğinde belirsizlik artar, tekil bina bilgisi içermez.
- **AFAD TDTH (Türkiye Deprem Tehlike Haritaları):** adres bazlı **PGA 475**
  (475 yılda bir depremde yer ivmesi, `g` cinsinden) değerleri. e-Devlet girişi
  gerektirir → programatik erişim sınırlı; ilçe/temsili nokta bazında derlenir.
- **İBB Mikrobölgeleme:** zemin sınıfı (ZA=kaya … ZE/ZF=alüvyon/dolgu),
  zemin büyütmesi (amplifikasyon), sıvılaşma potansiyeli.
- **DASK İnteraktif Deprem Haritası:** ilçe/mahalle risk grubu.
- **MTA Diri Fay Haritası:** en yakın aktif fay segmentine uzaklık.

> **Zemin mantığı (skorlamada kullan):** Kaya zeminler deprem dalgalarını daha az
> büyütür; yumuşak/dolgu/alüvyon zeminler dalgaları büyütür ve sıvılaşabilir →
> daha yüksek risk. Bu yüzden aynı fay uzaklığında bile mahalleler farklı skorlar alır.

### 4.3. Ulaşım
- **İBB Açık Veri Portalı** (`data.ibb.gov.tr`, API mevcut): İETT hat/durak
  (GTFS), metro/raylı sistem istasyonları, trafik yoğunluk indeksi.

### 4.4. Toplanma Alanları (Afet Sonrası)
- **e-Devlet AFAD acil toplanma alanı sorgulama.**
- Derlenmiş açık veri: `github.com/RKursatV/afad-toplanma-alani-acik-veri` (JSON,
  mahalle bazında toplanma noktaları).

### 4.5. Sağlık ve Eğitim (Erişim Skorları)
- **OpenStreetMap / Overpass API:** hastane, sağlık ocağı, okul POI'leri
  (koordinatlarıyla → mahalle içi/yakını sayımı).
- **İBB Açık Veri / Sağlık Bakanlığı / MEB açık verileri** (tamamlayıcı).

### 4.6. Demografi ve Yaşam Kalitesi
- **TÜİK:** mahalle/ilçe nüfusu, yaş dağılımı.
- **İBB Açık Veri:** yeşil alan, gürültü haritası, sosyal donatı verileri.

### 4.7. Konut Fiyatları
- Doğrudan açık kaynak sınırlıdır; konut fiyatları için ilan sitelerinden
  **web scraping yapılacak**. Buna ek olarak TÜİK konut fiyat endeksi + ilçe
  ortalama proxy değerleri (manuel derlenmiş bir CSV) "ortalama konut fiyatı"
  göstergesi olarak kullanılabilir.

> ⚠️ **Veri kaynağı kuralı:** Konut fiyatları için emlak ilan sitelerinden web
> scraping yapılabilir. Her veri seti için `data/SOURCES.md`
> dosyasına: kaynak URL, indirilme tarihi, lisans, kapsam (ilçe mi mahalle mi) yaz.

---

## 5. Mimari ve Klasör Yapısı

```
safematch-ai/
├── CLAUDE.md                     # bu dosya
├── docker-compose.yml            # PostGIS + servisler
│
├── data-pipeline/                # Python — veriyi indir, temizle, birleştir
│   ├── sources/                  # ham indirilen veriler (git'e alınmaz, .gitignore)
│   ├── scripts/
│   │   ├── 01_fetch_boundaries.py
│   │   ├── 02_fetch_earthquake.py
│   │   ├── 03_fetch_transit.py
│   │   ├── 04_fetch_poi.py        # hastane/okul (OSM)
│   │   ├── 05_normalize_scores.py # 0-100 normalizasyon
│   │   └── 06_build_features.py   # tek mahalle_features tablosu üret
│   ├── output/
│   │   └── mahalle_features.geojson
│   └── SOURCES.md                 # her verinin kaynağı/lisansı/tarihi
│
├── backend/                       # FastAPI — skorlama + AI + API
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                   # endpoint'ler
│   │   ├── scoring/               # ⭐ saf skorlama motoru (LLM'siz, test edilir)
│   │   │   ├── weights.py         # profil → kriter ağırlıkları
│   │   │   ├── scorer.py          # ağırlıklı toplam + bütçe filtresi
│   │   │   └── constants.py       # taban ağırlıklar, sınırlar
│   │   ├── ai/                    # Claude entegrasyonu
│   │   │   ├── weighting.py       # doğal profil → ağırlık (structured output)
│   │   │   └── explain.py         # skor → doğal dil açıklama
│   │   ├── models/                # Pydantic + SQLAlchemy
│   │   └── db/
│   └── tests/                     # skorlama motoru testleri
│
└── frontend/                      # Next.js
    ├── app/
    │   ├── page.tsx               # giriş
    │   ├── profil/                # çok adımlı form
    │   └── sonuclar/              # sonuç + harita
    ├── components/
    │   ├── ProfileForm/
    │   ├── ResultCard/            # mahalle kartı + skorlar
    │   ├── ScoreBreakdown/        # açıklanabilirlik görselleştirmesi
    │   └── Map/                    # MapLibre — renk kodlu poligonlar
    └── lib/
        └── api.ts
```

**Altın kural:** `scoring/` modülü **hiçbir LLM veya HTTP çağrısı içermez**.
Girdi (profil + mahalle özellikleri) → çıktı (sıralı skorlu liste) saf fonksiyonlardır.
Böylece deterministik, test edilebilir ve hızlıdır. AI yalnızca (a) profili ağırlığa
çevirirken ve (b) sonucu açıklarken devreye girer.

---

## 6. Skorlama Mantığı (Scoring Logic) — MCDA

Bu bir **Çok Kriterli Karar Analizi (Multi-Criteria Decision Analysis)** problemidir:
ağırlıklı toplam modeli.

### 6.1. Mahalle Özellikleri (Boyutlar)
Her mahalle için 0-100 arası normalize skorlar:

| Boyut | Kaynak | Not |
|---|---|---|
| `deprem_guvenlik` | İBB kayıp tahmini + AFAD PGA + zemin sınıfı + fay uzaklığı | Yüksek = güvenli |
| `dogal_afet` | Sel/heyelan/sıvılaşma katmanları | Yüksek = düşük risk |
| `ulasim` | Metro/İETT durak yoğunluğu + trafik | Araç sahipliğine göre yorumlanır |
| `saglik` | Hastane yakınlığı/yoğunluğu (OSM) | — |
| `egitim` | Okul yakınlığı/yoğunluğu (OSM) | Çocuklu ailede ağırlık artar |
| `sosyal_yasam` | POI çeşitliliği, yeşil alan | — |
| `yasam_kalitesi` | Gürültü, yoğunluk, donatı (birleşik) | — |
| `fiyat` | Ortalama konut fiyatı | Skor değil, **filtre + gösterge** |

### 6.2. Adım Adım Skorlama
```
1. BÜTÇE FİLTRESİ (hard filter):
   Kullanıcı bütçesinin belirgin şekilde üzerindeki mahalleleri ele.
   (Örn. ortalama fiyat > bütçe * 1.15 → listeden çıkar.)

2. AĞIRLIKLARI BELİRLE (profil → w_i):
   - Deprem önceliği yüksek → w_deprem yüksek.
   - Çocuk var → w_egitim + w_saglik artar.
   - Yaşlı birey → w_saglik + w_ulasim artar.
   - Araç yok → w_ulasim artar.
   - Sosyal yaşam beklentisi yüksek → w_sosyal artar.
   → Ağırlıklar normalize edilir (toplam = 1).

3. TABAN AĞIRLIK KURALI (Bölüm 2.1):
   w_deprem = max(w_deprem, DEPREM_MIN_AGIRLIK)   # örn. 0.20
   (kullanıcı umursamasa bile deprem her zaman anlamlı ağırlık taşır)

4. NİHAİ SKOR:
   uygunluk_skoru(mahalle) = Σ ( w_i * skor_i(mahalle) )

5. SIRALA ve ilk 5'i seç. Ayrıca ~3 "alternatif" (6-8. sıralar) döndür.
```

### 6.3. Normalizasyon
Ham değerler (PGA `g`, durak sayısı, mesafe km) farklı ölçeklerdedir. Hepsini
0-100'e min-max veya yüzdelik (percentile) ile ölçekle. **Yön önemli:** düşük PGA =
yüksek güvenlik skoru (ters çevir). Normalizasyon parametrelerini `constants.py`'de tut.

---

## 7. AI Katmanı (Explainable AI)

Claude iki yerde kullanılır. **Skorlama matematiği AI'da DEĞİL**, `scoring/`
modülündedir. AI, insan-dostu girdi/çıktı katmanıdır.

### 7.1. Ağırlıklandırma (`ai/weighting.py`)
- **Girdi:** Kullanıcı form yanıtları (+ varsa serbest metin: "sessiz, yeşil bir
  yer isterim ama işe metroyla gitmeliyim").
- **Görev:** Claude'a **yalnızca JSON** döndürmesini söyle: her boyut için
  ağırlık (0-1). Structured output; başka metin, markdown veya açıklama yok.
- Dönen ağırlıklar `scoring/` motoruna verilir. (Taban ağırlık kuralı kod tarafında
  tekrar uygulanır — AI'ya güvenip atlanmaz.)

### 7.2. Açıklama (`ai/explain.py`)
- **Girdi:** Seçilen mahalle + skor kırılımı + kullanıcı profili.
- **Görev:** Türkçe, kısa, somut bir gerekçe üret: "Bu mahalle sizin için önerildi
  çünkü deprem güvenlik skoru yüksek (zemin sınıfı kaya), metroya 400 m ve
  bütçenize uygun. Tek zayıf yönü hastane yoğunluğunun ortalama olması."
- **Kural:** Açıklama, gerçek skorlarla **tutarlı** olmalı (halüsinasyon yok).
  Skorda olmayan bir iddiayı üretme. Prompt'a skorları ve disclaimer'ı dahil et.

### 7.3. Prompt Kuralları
- Sistem prompt'unda **sorumluluk reddini** hatırlat: "bina bazında garanti verme,
  bölgesel istatistik olduğunu vurgula."
- Her zaman **deterministik yapı** iste (özellikle ağırlıkta: sadece JSON).
- Prompt'ları `ai/prompts/` altında versiyonla; kod içinde string gömme.

---

## 8. Geliştirme Fazları (Adım Adım Yol Haritası)

Her faz **çalışan, gösterilebilir** bir çıktı üretmeli. Sırayla ilerle; bir fazı
bitirmeden diğerine geçme. Deprem verisi ve skorlama motoru **en kritik** fazlardır.

### 🔧 Faz 0 — Kurulum & Altyapı
- [ ] Repo + klasör iskeleti (Bölüm 5), `.gitignore`, `.env.example`.
- [ ] `ANTHROPIC_API_KEY` ortam değişkeni + gizli anahtar yönetimi (asla commit etme).
- [ ] `docker-compose.yml` ile PostgreSQL + PostGIS ayağa kalksın (3.1 yolundaysan).
- [ ] Frontend ve backend "hello world" iskeletleri çalışsın.
- ✅ **Çıktı:** `docker-compose up` çalışıyor, boş sayfa açılıyor.

### 📥 Faz 1 — Veri Toplama & Hazırlama (Data Pipeline)
- [ ] İdari sınırlar: İstanbul mahalle/ilçe GeoJSON'u indir (4.1).
- [ ] Deprem: İBB ilçe kayıp tahminleri + zemin sınıfı + (mümkünse) PGA'yı derle (4.2).
- [ ] Ulaşım: metro/İETT durakları (4.3).
- [ ] POI: OSM Overpass ile hastane/okul (4.5).
- [ ] Toplanma alanları (4.4), demografi (4.6), fiyat proxy (4.7).
- [ ] `06_build_features.py`: hepsini mahalleye eşleştirip **tek** `mahalle_features.geojson` üret.
- [ ] `SOURCES.md`: her verinin kaynağı, tarihi, lisansı, kapsamı.
- ✅ **Çıktı:** Her İstanbul mahallesi için ham özelliklerin bulunduğu tek dosya.

### 🧮 Faz 2 — Skorlama Motoru (Scoring Engine) ⭐
- [ ] `normalize`: ham değerleri 0-100'e çevir (yönleri doğru ayarla — 6.3).
- [ ] `scorer.py`: bütçe filtresi + ağırlıklı toplam (6.2).
- [ ] `weights.py`: profilden ağırlık türeten kural tabanlı taban fonksiyon.
- [ ] `constants.py`: `DEPREM_MIN_AGIRLIK` ve normalizasyon parametreleri.
- [ ] **Birim testleri:** sabit girdiyle beklenen sıralama; taban ağırlık kuralı;
      bütçe filtresi sınır durumları.
- ✅ **Çıktı:** Örnek profille terminalden ilk 5 mahalle + skor kırılımı üretiliyor (AI yok).

### 🤖 Faz 3 — AI Katmanı (Ağırlık + Açıklama)
- [ ] `ai/weighting.py`: profil → Claude → **sadece JSON ağırlık**. Parse + doğrula.
- [ ] Taban ağırlık kuralını AI çıktısı üstünde tekrar uygula.
- [ ] `ai/explain.py`: skor + profil → Türkçe açıklama (skorla tutarlı).
- [ ] Prompt'ları `ai/prompts/`'ta versiyonla; hata/timeout durumunda kural tabanlı
      ağırlığa geri düş (graceful fallback).
- ✅ **Çıktı:** Doğal profil → AI ağırlığı → sıralı sonuç → doğal dil açıklaması.

### 🌐 Faz 4 — Backend API
- [ ] `POST /api/recommend` — gövde: profil; yanıt: ilk 5 + alternatifler + skorlar + açıklama.
- [ ] `GET /api/mahalle/{id}` — tek mahalle detay skorları.
- [ ] `GET /api/mahalleler` — harita için tüm poligonlar + temel skor (renklendirme).
- [ ] CORS, hata yönetimi, (opsiyonel) Redis cache.
- ✅ **Çıktı:** API'ye profil POST'la, tam sonuç JSON'u dönüyor.

### 🖥️ Faz 5 — Frontend & Harita
- [ ] Çok adımlı **profil formu** (bütçe, iş yeri, çocuk, araç, deprem önceliği,
      hastane/okul, ulaşım, sosyal yaşam).
- [ ] **Sonuç ekranı:** 5 mahalle kartı — uygunluk, deprem, yaşam, ulaşım skorları
      + ortalama fiyat + AI açıklaması.
- [ ] **Harita (MapLibre):** mahalle poligonları, deprem güvenliğine göre renk kodu,
      seçili mahalleye zoom, tıklayınca detay.
- [ ] **Disclaimer** her sonuç ekranında görünür (Bölüm 2.1).
- ✅ **Çıktı:** Uçtan uca akış tarayıcıda çalışıyor.

### ✨ Faz 6 — Açıklanabilirlik Görselleştirme & Cila
- [ ] **Skor kırılımı görseli** ("neden bu mahalle?" — her boyutun katkısı, bar/radar).
- [ ] Mahalle **karşılaştırma** görünümü.
- [ ] **Alternatif öneriler** bölümü (kayan liste).
- [ ] Loading state'leri, responsive tasarım, erişilebilirlik (a11y), boş/hata durumları.
- [ ] (Opsiyonel) toplanma alanlarını haritada göster.
- ✅ **Çıktı:** Sunuma/demoya hazır, cilalı ürün.

---

## 9. Komutlar (Commands)

> Kurulum ilerledikçe bu bölümü gerçek komutlarla güncelle.

```bash
# Altyapı
docker-compose up -d              # PostGIS + servisler

# Veri hazırlama (data-pipeline/)
python scripts/06_build_features.py

# Backend (backend/)
pip install -r requirements.txt
pip install <paket> --break-system-packages   # bu ortamda pip için
uvicorn app.main:app --reload
pytest                            # skorlama testleri

# Frontend (frontend/)
npm install
npm run dev
npm run build && npm run start
npm run lint
```

---

## 10. Kod Standartları (Conventions)

- **Diller:** Backend/pipeline Python 3.11+, tip ipuçları (type hints) zorunlu.
  Frontend TypeScript, `any` kaçın.
- **Adlandırma:** Alan adları Türkçe kalabilir (`deprem_guvenlik`), fonksiyon/değişken
  adları İngilizce (`compute_score`). Tutarlı ol.
- **Skorlama saf tutulur:** `scoring/` içinde HTTP/LLM/DB çağrısı yok.
- **AI çıktısı doğrulanır:** LLM'den gelen JSON her zaman parse + şema doğrulaması
  (Pydantic) ile kontrol edilir; hatada fallback.
- **Gizli anahtarlar:** API key'ler yalnızca `.env`; koda gömme, log'lama.
- **Veri izlenebilirliği:** Her skorun kaynağı `SOURCES.md`'de belgeli.
- **Testler:** Skorlama motoru için birim test şart (deterministik olduğu için kolay).
- **Küçük commit'ler:** Faz bazında ilerle, her fazda çalışır durumda bırak.

---

## 11. Başarı Kriterleri (Hatırlatma)

Kod bu hedeflere hizmet etmeli:
- AI, kullanıcı öncelikleriyle **uyumlu**, anlamlı kişiselleştirilmiş öneri üretiyor.
- Risk + yaşam analizleri **tek platformda** birleşiyor.
- Çıktılar **açıklanabilir ve güvenilir** (skorla tutarlı, kaynağı belli).
- Deprem güvenliği kararın **merkezinde** (taban ağırlık kuralı her zaman geçerli).

---

## 12. AI Asistan İçin Notlar (Claude Code'a)

- Yeni bir görevde **önce bu dosyayı ve `SOURCES.md`'yi** oku.
- Bir veri kaynağı belirsizse **uydurma** — `SOURCES.md`'ye "eksik/doğrulanmalı"
  notu düş ve kullanıcıya sor.
- Skorlama motorunu değiştirdiğinde **ilgili testleri** güncelle/ekle.
- Disclaimer'ı hiçbir sonuç ekranından **kaldırma**.
- Konut fiyatları için emlak ilan sitelerinden **web scraping yap**.
- Şüphe halinde: deprem güvenliğini koru, açıklanabilirliği koru, kaynağı belgele.
