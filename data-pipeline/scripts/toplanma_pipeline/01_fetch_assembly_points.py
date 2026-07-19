import requests
import json

def fetch_assembly_points():
    # 1. Değişiklik: Endpoint'i HTTPS olarak güncelledik
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    query = """
    [out:json][timeout:180];
    area["name"="İstanbul"]["admin_level"="4"]->.searchArea;
    (
      nwr["emergency"="assembly_point"](area.searchArea);
    );
    out center;
    """
    
    # 2. Değişiklik: API'ye kim olduğumuzu ve JSON formatı kabul ettiğimizi belirten başlıklar (Headers) ekledik
    headers = {
        "User-Agent": "AIEngineer_IstanbulProject/1.0",
        "Accept": "application/json"
    }
    
    print("Overpass API'den veri çekiliyor, lütfen bekleyin...")
    
    # 3. Değişiklik: Veriyi doğrudan raw text (utf-8) olarak gönderiyoruz
    response = requests.post(overpass_url, data=query.encode('utf-8'), headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        with open("istanbul_toplanma_alanlari.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            
        points_count = len(data.get('elements', []))
        print(f"İşlem başarılı! {points_count} adet toplanma alanı JSON dosyasına kaydedildi.")
    else:
        print(f"Bir hata oluştu. HTTP Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    fetch_assembly_points()