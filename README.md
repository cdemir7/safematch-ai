# 🛡️ SafeMatch AI

**Backlog & Proje Yönetim URL:** [ClickUp Board](https://app.clickup.com/9018979959/v/s/901811680269)

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

| İsim | Rol | GitHub | LinkedIn |
| :--- | :--- | :--- | :--- |
| Muhammed Taha Alpbalta | Product Owner | [GitHub](https://github.com/tahalpbalta) | [LinkedIn](https://www.linkedin.com/in/tahalpbalta/) |
| Cihan Demir | Scrum Master | [GitHub](https://github.com/cdemir7) | [LinkedIn](https://www.linkedin.com/in/demircihan/) |
| Azra Gül | Developer | [GitHub](https://github.com/azraagull) | [LinkedIn](https://www.linkedin.com/in/azragul1l/) |
| Süeda Ünal | Developer | [GitHub](https://github.com/suedaunal) | [LinkedIn](https://www.linkedin.com/in/suedaaunal/) |


---

# 📋 Sprint 1

**Sprint Hedefi:** İstanbul mahallelerinin deprem, ulaşım ve yaşam kalitesi verilerini toplayarak veri boru hattını (data pipeline) kurmak, projenin veritabanı altyapısını ayağa kaldırmak ve kullanıcı profili formunun frontend iskeletini tasarlayarak uçtan uca çalışır bir temel sistem oluşturmak.

### 🎯 Sprint Görevleri ve Puan Dağılımı (Toplam: 100 Puan)

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

### 📝 Sprint Notları & Ürün Geliştirme Durumu

**Tamamlananlar:**
- Proje iskeleti ve GitHub reposu başarıyla kuruldu.
- Docker compose dosyası oluşturuldu.
- İstanbul mahalle/ilçe idari sınırları belirlendi, İBB deprem analizleri, ulaşım, hastane, okul ve toplanma alanı verileri çekilip tek bir mahalle özellik dosyasına (`mahalle_features.geojson`) indirgendi.
- Frontend tarafında kullanıcının kendini özel hissetmesini sağlayacak çok adımlı onboarding (wizard) arayüzü tasarlandı. 
- Next.js ve TailwindCSS ile frontend iskeleti oluşturuldu.

**Ürün Geliştirme Durumu (Arayüz Tasarımlarımız):**
Aşağıda kullanıcının veri girdiği form alanları ve landing page tasarımlarımızın güncel ekran görüntüleri yer almaktadır.

<img width="1666" height="865" alt="safematch-ai landing page" src="https://github.com/user-attachments/assets/e7cb95a5-a731-4057-a01c-3cf7415efe22" />

<img width="1692" height="868" alt="safematch-ai form" src="https://github.com/user-attachments/assets/4bbd47e4-9a1e-4593-beca-7b8ed4f2a8de" />


**Karşılaşılan Zorluklar ve Çözümler:**
- Projenin ilk başta Türkiye geneli olması planlanırken veri yetersizliği nedeniyle projenin öncelikle İstanbul odaklı olmasına karar verildi.

### 🔄 Proje Yönetimi & Daily Scrum 
**Proje Yönetimi:**
Görev dağılımı ve proje yönetimi (Product Backlog) ClickUp üzerinden yürütülmektedir. Ana görevler (Task) ve alt görevler (Subtask) detaylı açıklamaları ve kabul kriterleri ile birlikte oluşturulmuş; önceliklendirme (priority) ve bitiş tarihleri (due date) atanarak görev kontrolü ve proje takibi sistemli bir şekilde sağlanmıştır.

<img width="1916" height="826" alt="Clickup task screeansot" src="https://github.com/user-attachments/assets/22caae43-5fb0-49d0-8faa-a9c953613e11" />

**Daily Scrum:**
Daily Scrum toplantılarımızı iki günde bir, 16:00 - 18:00 saatleri arasında Google Meet üzerinden gerçekleştirdik. Ekstra yoğun olduğumuz günlerde ise iletişimimizi ve süreç takibimizi WhatsApp üzerinden mesajlaşarak sürdürdük. Toplantılarımızda özellikle *"Ne planlanmıştı? Neredeyiz? Nasıl ilerleyeceğiz?"* soruları üzerinde durarak sürecin kontrolünü ve bir sonraki adımların planlamasını sağladık. Toplantılarımızdan kareler:

<img width="1918" height="866" alt="meet screenshot 1" src="https://github.com/user-attachments/assets/80f1f507-6e21-41e2-9136-3d8596f1422f" />

<img width="1918" height="797" alt="meet screenshot 2" src="https://github.com/user-attachments/assets/1654f414-93e8-4e9b-896b-5c4a63f9f675" />

<img width="1918" height="866" alt="meet screenshot 3" src="https://github.com/user-attachments/assets/c8aa86ec-d38b-4e97-a8e5-00cf9aea866c" />


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

### 💯 Sprint Sonu Puan Değerlendirmesi

Sprint 1 kapsamında belirlenen 100 puanlık hedefin görev bazlı tamamlanma oranları ve alınan puanlar aşağıdaki tabloda özetlenmiştir:

| Görev Kategorisi | Hedeflenen Puan | Tamamlanan Puan | Durum |
| :--- | :---: | :---: | :--- |
| 🏗️ **Kurulum & Altyapı** | 30 | 30 | Tamamlandı |
| 🎨 **Frontend** | 30 | 26 | 4 Puan Kırıldı |
| 📊 **Veri Toplama & Hazırlama** | 40 | 30 | 10 Puan Kırıldı |
| **🏆 TOPLAM** | **100** | **86** | 🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜ **%86** |

> **Puan Kırılan Noktalar & Kalan Görevler:** 
> - **Veri Toplama (-10 Puan):** Her İstanbul mahallesi için ham özelliklerin bulunduğu tek dosyanın nihai hale getirilmesi ve eşleştirilmesi işlemine devam edilmektedir.
> - **Frontend (-4 Puan):** Çok adımlı profil formundaki UI/UX eksiklikleri ve son rötüşlar bir sonraki sprinte sarkmıştır.
> 
> **Sonuç:** Kalan veri hazırlama ve frontend adımları dışında, planlanan tüm altyapı görevleri Sprint 1 kapsamında başarıyla tamamlanmıştır.



