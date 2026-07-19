import json
import pandas as pd
import geopandas as gpd
import warnings

warnings.filterwarnings('ignore', 'GeoSeries.notna', UserWarning)

def match_neighborhoods_with_assembly_points():
    print("GeoJSON ve JSON dosyaları yükleniyor...")
    
    gdf_mahalle = gpd.read_file('istanbul_mahalle_ilce_birlesik.geojson')
    
    # --- ÇÖZÜM: 'index_right' sütununu kaldır veya yeniden adlandır ---
    if 'index_right' in gdf_mahalle.columns:
        gdf_mahalle = gdf_mahalle.drop(columns=['index_right'])

    with open('istanbul_toplanma_alanlari.json', 'r', encoding='utf-8') as f:
        osm_data = json.load(f)
            
    points_list = []
    for element in osm_data.get('elements', []):
        if 'lat' in element and 'lon' in element:
            tags = element.get('tags', {})
            points_list.append({
                'toplanma_id': element['id'],
                'toplanma_lat': element['lat'],
                'toplanma_lon': element['lon'],
                'toplanma_adi': tags.get('name', 'İsimsiz Toplanma Alanı')
            })
                
    df_points = pd.DataFrame(points_list)
    gdf_points = gpd.GeoDataFrame(
        df_points, 
        geometry=gpd.points_from_xy(df_points.toplanma_lon, df_points.toplanma_lat), 
        crs="EPSG:4326"
    )

    print("Metrik sisteme dönüşüm...")
    gdf_mahalle_metric = gdf_mahalle.to_crs(epsg=32635)
    gdf_points_metric = gdf_points.to_crs(epsg=32635)

    mahalle_centroids = gdf_mahalle_metric.copy()
    mahalle_centroids['geometry'] = mahalle_centroids.geometry.centroid

    print("Eşleştirme yapılıyor...")
    
    # sjoin_nearest ile eşleştirme
    eslesme = gpd.sjoin_nearest(
        mahalle_centroids, 
        gdf_points_metric, 
        how='left', 
        distance_col='dist_m' # Sütun ismini değiştirdik
    )
    
    eslesme = eslesme[~eslesme.index.duplicated(keep='first')]

    # Veriyi orijinal GeoDataFrame'e geri aktar
    gdf_mahalle['en_yakin_toplanma_adi'] = eslesme['toplanma_adi']
    gdf_mahalle['en_yakin_toplanma_lat'] = eslesme['toplanma_lat']
    gdf_mahalle['en_yakin_toplanma_lon'] = eslesme['toplanma_lon']
    gdf_mahalle['en_yakin_toplanma_mesafe_m'] = eslesme['dist_m'].round(2)

    output_file = "mahalle_toplanma_eslesme.geojson"
    gdf_mahalle.to_file(output_file, driver="GeoJSON", encoding="utf-8")
    print(f"İşlem tamamlandı! '{output_file}' dosyasına kaydedildi.")

if __name__ == "__main__":
    match_neighborhoods_with_assembly_points()