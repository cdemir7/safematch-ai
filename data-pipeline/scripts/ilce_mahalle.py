import geopandas as gpd

def merge_mahalle_ilce():
    print("GeoJSON dosyaları yükleniyor...")
    
    # 1. Dosyaları GeoDataFrame olarak oku
    gdf_ilceler = gpd.read_file('ilce_geojson.json')
    gdf_mahalleler = gpd.read_file('mahalle_geojson.json')
    
    # Koordinat Sistemlerinin (CRS) aynı olduğundan emin ol
    if gdf_ilceler.crs != gdf_mahalleler.crs:
        gdf_mahalleler = gdf_mahalleler.to_crs(gdf_ilceler.crs)
        
    print("Mekansal birleştirme işlemi başlatılıyor...")
    
    # 2. Sınır hatalarını önlemek için mahallelerin merkez noktalarını (centroid) hesapla
    # Sadece geçici bir hesaplama DataFrame'i oluşturuyoruz
    mahalle_merkezleri = gdf_mahalleler.copy()
    
    # Uyarı almamak için projeksiyonu geçici olarak düzlemsel sisteme çevirip centroid alıyoruz
    mahalle_merkezleri['geometry'] = mahalle_merkezleri.geometry.to_crs('+proj=cea').centroid.to_crs(gdf_ilceler.crs)
    
    # 3. Spatial Join (sjoin)
    # Mahallenin merkez noktası, hangi ilçe poligonunun içindeyse ('within') onu eşleştirir
    birlesik_veri = gpd.sjoin(mahalle_merkezleri, gdf_ilceler, how="inner", predicate="within")
    
    # Birleştirilen tablodaki 'geometry' sütunu şu an merkez noktaları içeriyor. 
    # Orijinal mahalle poligonlarını geri getirmemiz lazım.
    birlesik_veri['geometry'] = gdf_mahalleler['geometry']
    
    # 4. Sonucu yeni bir GeoJSON olarak kaydet
    output_dosyasi = 'istanbul_mahalle_ilce_birlesik.geojson'
    birlesik_veri.to_file(output_dosyasi, driver="GeoJSON", encoding="utf-8")
    
    print(f"İşlem başarılı! Birleştirilmiş veri {output_dosyasi} olarak kaydedildi.")

if __name__ == "__main__":
    merge_mahalle_ilce()