# 🛡️ SafeMatch AI

## 🎯 Proje Amacı
İstanbul'da yaşayacağı bölgeyi seçmek isteyen bireylere, **deprem güvenliğini karar sürecinin merkezine koyarak** kişiselleştirilmiş mahalle önerileri sunan yapay zekâ destekli bir karar destek platformu sunmaktır.

## 📝 Proje Özeti
Kullanıcılar platformu ziyaret ederek bütçe, iş yeri, çocuk, araç, deprem önceliği, sosyal yaşam gibi kriterleri içeren çok adımlı bir profil formu doldurur. Sistem arka planda bu verileri işler ve süreci uçtan uca yürütür:
1. **Veri Toplama ve Hazırlama:** İstanbul'daki tüm mahallelerin idari sınırları, İBB deprem kayıp verileri, ulaşım, POI (hastane, okul vb.) ve toplanma alanı verileri eşleştirilerek skorlanır.
2. **Kişiselleştirilmiş Skorlama:** Kullanıcının formdaki tercihlerine göre yapay zeka (AI) destekli bir ağırlıklandırma algoritması çalıştırılarak en uygun mahalleler belirlenir.
3. **Görselleştirme ve Sonuç:** Seçilen ilk 5 mahalle, uygunluk, deprem, yaşam ve ulaşım skorları ile birlikte harita üzerinde sunulur ve yapay zeka tarafından kullanıcının profiline özel Türkçe açıklama oluşturulur.

## ✨ Ürün Özellikleri
- Yaşam kalitesi analizi
- Deprem riski analizi
- AI açıklamalı öneri sistemi
- Kişiselleştirilmiş bölge uygunluk skoru
- Çok adımlı profil formu (wizard)
- Harita (MapLibre) destekli görselleştirme ve mahalle kıyaslaması

## 👥 Hedef Kitle
- Bireysel Kullanıcılar
- Yatırımcılar
- Gayrimenkul sektöründeki şirketler
- Deprem riski konusunda bilinçli kullanıcılar

## 💻 Kullanılan Teknolojiler
**Frontend:**
- Next.js
- TailwindCSS

**Backend & Veritabanı:**
- Python
- PostgreSQL + PostGIS (Supabase)
- Docker (docker-compose)

**AI & Haritalama:**
- Gemini-2.5 Flash
- MapLibre (Harita entegrasyonu)
- GeoJSON & OSM Overpass (Veri setleri)

## 🧑‍💻 Takım Üyeleri (Takım 46)

| İsim | Rol |
| :--- | :--- |
| Muhammed Taha Alpbalta | Product Owner |
| Cihan Demir | Scrum Master |
| Azra Gül | Developer |
| Süeda Ünal | Developer |


---

# 📋 Sprint 1

**Sprint Hedefi:** İstanbul mahallelerinin deprem, ulaşım ve yaşam kalitesi verilerini toplayarak veri boru hattını (data pipeline) kurmak, projenin veritabanı altyapısını ayağa kaldırmak ve kullanıcı profili formunun frontend iskeletini tasarlayarak uçtan uca çalışır bir temel sistem oluşturmak.

### 🎯 Sprint Görevleri ve Puan Dağılımı

**Kurulum & Altyapı (30 Puan):**
- Repo + klasör iskeleti, `.gitignore`, `.env.example` oluşturuldu.
- `docker-compose.yml` dosyası oluşturuldu.
- Frontend ve backend "hello world" iskeletleri çalıştırıldı. 

**Veri Toplama & Hazırlama (Data Pipeline) (40 Puan):**
- İstanbul mahalle/ilçe GeoJSON verileri indirildi.
- İBB ilçe kayıp tahminleri, zemin sınıfı verileri derlendi.
- Metro/İETT durakları ve OSM Overpass ile POI (hastane/okul) verileri çekildi.
- Tüm bu veriler mahallere eşleştirildi ve tek bir dosya haline getirildi.

**Frontend (30 Puan):**
- Çok adımlı profil formu mimarisi kurgulandı (bütçe, iş yeri, vb.).
- Kullanıcı analiz bileşenleri (Bento Box, hap butonlar) kodlandı.
- Sonuç ekranı konseptinin (5 mahalle kartı, skorlar, ortalama fiyat, AI açıklaması) temelleri atıldı.

### 📝 Sprint Notları

**Tamamlananlar:**
- Proje iskeleti ve GitHub reposu başarıyla kuruldu.
- Docker compose dosyası oluşturuldu.
- İstanbul mahalle/ilçe idari sınırları belirlendi, İBB deprem analizleri, ulaşım, hastane, okul ve toplanma alanı verileri çekilip tek bir mahalle özellik dosyasına (`mahalle_features.geojson`) indirgendi.
- Frontend tarafında kullanıcının kendini özel hissetmesini sağlayacak çok adımlı onboarding (wizard) arayüzü tasarlandı. 
- Next.js ve TailwindCSS ile frontend iskeleti oluşturuldu.

**Karşılaşılan Zorluklar ve Çözümler:**
- Projenin ilk başta Türkiye geneli olması planlanırken veri yetersizliği nedeniyle projenin öncelikle İstanbul odaklı olmasına karar verildi.

### 🔄 Daily Scrum & Proje Yönetimi
Proje yönetimi ClickUp üzerinden yürütülmektedir. Aktif biten taskların ekran görüntüsü:

### 📊 Sprint Review
**Alınan Kararlar:**
- Ham değerlerin 0-100 arasında normalize edilmesi (Bir sonraki aşamanın hazırlığı).
- Profilden ağırlık türeten kural tabanlı fonksiyon oluşturulması kararlaştırıldı.
- Oluşturulan profilin AI ile yorumlanması planlandı.
- Kullanıcı analizi tamamladıktan sonra isteğe bağlı olarak bir üyeliğe yönlendirilmesi planlandı.

### 💡 Sprint Retrospective
- **Ne İyi Gitti:** Projenin temel taşları (veri toplama, altyapı ve arayüz iskeleti) detaylıca atıldı.
- **İyileştirilmesi Gerekenler:**
  - Takım içindeki görev dağılımıyla ilgili düzenleme yapılması kararı alınmıştır.
  - Kullanıcı analizi tamamladıktan sonra yapılacak yönlendirmeler netleştirilmelidir.
  
### 💯 Sprint Sonu Tamamlanan Puan
**86/100**: Veri toplama ve hazırlama bölümünde her İstanbul mahallesi için ham özelliklerin bulunduğu tek dosya hazırlanmaya devam etmektedir. Onun dışında hedeflenilen tüm görevler tamamlanmıştır.
