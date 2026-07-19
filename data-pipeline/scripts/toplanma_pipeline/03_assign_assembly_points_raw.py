import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import os

def process_assembly_points():
    print("Veriler yükleniyor...")
    
    # 1. OSM'den Çektiğin Toplanma Alanlarını Yükle
    with open('istanbul_toplanma_alanlari.json', 'r', encoding='utf-8') as f:
        osm_data = json.load(f)
    
    # Noktaları (lat, lon) ve özellikleri ayrıştırıp DataFrame oluştur
    points_list = []
    for element in osm_data.get('elements', []):
        if 'lat' in element and 'lon' in element:
            tags = element.get('tags', {})
            points_list.append({
                'id': element['id'],
                'lat': element['lat'],
                'lon': element['lon'],
                'name': tags.get('name', 'İsimsiz Toplanma Alanı')
            })
            
    df = pd.DataFrame(points_list)
    print(f"Toplam {len(df)} toplanma alanı noktası bulundu.")

    # DataFrame'i GeoDataFrame'e dönüştür (Koordinat Sistemi EPSG:4326 - WGS84)
    # Geopandas 'geometry' sütununa ihtiyaç duyar (boylam, enlem sırası önemlidir)
    gdf_points = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.lon, df.lat),
        crs="EPSG:4326"
    )

    # 2. İstanbul Mahalle Sınırları Poligonlarını Yükle
    # DİKKAT: Bu dosyayı daha önceden indirmiş olmalısın
    geojson_path = 'istanbul_mahalleler.geojson'
    
    if not os.path.exists(geojson_path):
         print(f"HATA: '{geojson_path}' dosyası bulunamadı. Spatial Join için mahalle sınırları gereklidir.")
         return

    gdf_mahalleler = gpd.read_file(geojson_path)
    
    # Her iki verinin de aynı koordinat sisteminde (CRS) olduğundan emin ol
    if gdf_mahalleler.crs != "EPSG:4326":
        gdf_mahalleler = gdf_mahalleler.to_crs("EPSG:4326")

    print("Mekansal birleştirme (Spatial Join) yapılıyor...")
    
    # 3. Spatial Join (sjoin): Noktalar hangi poligonun içindeyse eşleştir
    # 'how="inner"': Sadece bir mahalleye düşen toplanma alanlarını al
    # 'predicate="intersects"': Nokta, poligonun içindeyse veya sınırına değiyorsa
    joined_gdf = gpd.sjoin(gdf_points, gdf_mahalleler, how="inner", predicate="intersects")

    print(f"Eşleştirilen toplanma alanı sayısı: {len(joined_gdf)}")

    # 4. Mahallelere Göre JSON Olarak Kaydetme
    # GeoJSON dosyasında mahalle adının bulunduğu sütunu belirtmen gerekir.
    # Çoğu GeoJSON'da bu 'name', 'MahalleAd', 'MAHALLE' vs. olabilir. 
    # Buradaki 'name_right', sjoin sonrası poligon dosyasından gelen isim sütunudur (genellikle 'name_right' veya 'MahalleAd' olur).
    # Kendi geojson dosyandaki sütun ismine göre burayı güncellemelisin (Örn: mahalle_sutunu = 'Mahalle_Adi')
    mahalle_sutunu = 'name_right' # Kendi geojson'una göre burayı kontrol et!
    
    # Kayıt için bir klasör oluştur
    output_folder = "mahalle_toplanma_alanlari"
    os.makedirs(output_folder, exist_ok=True)
    
    # Her bir mahalle için döngü
    grouped = joined_gdf.groupby(mahalle_sutunu)
    
    for mahalle_adi, group in grouped:
        # Geçersiz dosya isimlerini (örn: boşluk veya özel karakterler) temizle
        safe_name = str(mahalle_adi).replace("/", "_").replace("\\", "_").strip()
        file_name = f"{output_folder}/{safe_name}.json"
        
        # O mahalleye ait verileri sözlük yapısına çevir (geometri nesnesi hariç)
        records = group[['id', 'lat', 'lon', 'name']].to_dict(orient='records')
        
        # Mahalle verisini kaydet
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=4)
            
    print(f"İşlem tamamlandı! Veriler '{output_folder}' klasörüne {len(grouped)} farklı mahalle dosyası olarak kaydedildi.")

if __name__ == "__main__":
    process_assembly_points()