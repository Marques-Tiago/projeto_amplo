import geopandas as gpd
import pandas as pd
import warnings
import os
import rasterio
import numpy as np
from rasterstats import zonal_stats

# --- 1. PARÂMETROS ---

# Construção de caminhos relativos
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, 'data')
DATA_GPKG = os.path.join(data_dir, 'Data.gpkg')
MDE_RASTER_PATH = os.path.join(data_dir, 'raster', 'modelo_digital_elevacao_inpe.tif')
USO_RASTER_PATH = os.path.join(data_dir, 'raster', 'uso_ocupacao_map_biomas.tif')

CRS_LOCAL = 'EPSG:4674'
CRS_PROJECTED = 'EPSG:5880'

warnings.filterwarnings('ignore', message='This version of GeoPackage')

# Camadas de ENTRADA
LAYER_NAMES = {
    'ae': 'AEs',
    'ada': 'ADAs',
    'gbif': 'gbif_occurrences',
    'uc': 'unidades_conservacao_sisema',
}

# Camadas que serão copiadas para o novo arquivo sem alterações
LAYERS_TO_KEEP_AS_IS = [
    'gbif_occurrences', 'limites_minas_gerais_sisema',
    'unidades_conservacao_sisema'
]

BUFFER_RADIUS_KM = 5

# --- FUNÇÃO AUXILIAR ---
def get_top_two_categories(counts_dict):
    if not counts_dict or not isinstance(counts_dict, dict):
        return np.nan, np.nan
    sorted_items = sorted(counts_dict.items(), key=lambda item: item[1], reverse=True)
    majority = sorted_items[0][0]
    second_majority = sorted_items[1][0] if len(sorted_items) > 1 else np.nan
    return majority, second_majority

def main():
    print("Iniciando Script 04: Cálculo de Indicadores")

    # --- 2. CARREGAMENTO DE DADOS ---
    print(f"Carregando dados de: {DATA_GPKG}")
    gdfs = {}
    try:
        for key, name in LAYER_NAMES.items():
            gdfs[key] = gpd.read_file(DATA_GPKG, layer=name)
        print("Camadas carregadas.")
    except Exception as e:
        print(f"Erro ao carregar dados: {e}"); return
    
    ucs_projected_unified = gdfs['uc'].to_crs(CRS_PROJECTED).union_all()

    # --- 3. CÁLCULO DE INDICADORES VETORIAIS ---
    print("\nCalculando indicadores vetoriais...")
    gdf_ada = gdfs['ada']; gdf_ae = gdfs['ae']
    for gdf, id_col, name in [(gdf_ada, 'adas_id', 'ADAs'), (gdf_ae, 'aes_id', 'AEs')]:
        gdf_projected = gdf.to_crs(CRS_PROJECTED)
        gdf['area_ha'] = gdf_projected.geometry.area / 10000
        
        # --- CORREÇÃO APLICADA AQUI ---
        # Prepara o dataframe do GBIF para o join, evitando conflito de colunas.
        # O conflito só ocorre quando id_col ('aes_id') já existe em gdfs['gbif'].
        gbif_to_join = gdfs['gbif']
        if id_col in gbif_to_join.columns:
            gbif_to_join = gbif_to_join.drop(columns=[id_col])

        sjoined_gbif = gpd.sjoin(gbif_to_join, gdf, how="inner", predicate="within")
        # --- FIM DA CORREÇÃO ---

        gbif_agg = sjoined_gbif.groupby(id_col).agg(riqueza_especies=('scientificName', 'nunique'), n_registros=('gbifID', 'count'), n_individuos=('n_individuals', 'sum')).reset_index()
        gdf = gdf.merge(gbif_agg, on=id_col, how='left')
        gdf['dist_uc_km'] = gdf_projected.geometry.distance(ucs_projected_unified) / 1000
        gdf_buffer = gdf_projected.copy(); gdf_buffer['geometry'] = gdf_buffer.geometry.buffer(BUFFER_RADIUS_KM * 1000)
        sjoined_ucs = gpd.sjoin(gdf_buffer[[id_col, 'geometry']], gdfs['uc'].to_crs(CRS_PROJECTED), how='left', predicate='intersects')
        uc_count = sjoined_ucs.groupby(id_col).size().reset_index(name='n_ucs_raio_5km')
        gdf = gdf.merge(uc_count, on=id_col, how='left')
        if name == 'ADAs': gdf_ada = gdf
        else: gdf_ae = gdf
    print("Indicadores vetoriais calculados.")

    # --- 4. CÁLCULO DE INDICADORES RASTER ---
    print("\nCalculando indicadores de rasters...")
    # 4.1 MDE
    if not os.path.exists(MDE_RASTER_PATH):
        print(f"Aviso: Raster MDE não encontrado.")
    else:
        with rasterio.open(MDE_RASTER_PATH) as src: raster_crs = src.crs
        print("Calculando estatísticas do MDE...")
        for gdf, name in [(gdf_ada, 'ADAs'), (gdf_ae, 'AEs')]:
            stats = zonal_stats(gdf.to_crs(raster_crs), MDE_RASTER_PATH, stats=['mean', 'min', 'max'])
            df_stats = pd.DataFrame(stats).rename(columns={'mean': 'elevacao_media', 'min': 'elevacao_min', 'max': 'elevacao_max'})
            gdf = gdf.join(df_stats)
            gdf['relevo_m'] = gdf['elevacao_max'] - gdf['elevacao_min']
            if name == 'ADAs': gdf_ada = gdf
            else: gdf_ae = gdf
        print("Indicadores de MDE calculados.")

    # 4.2 Uso do Solo
    if not os.path.exists(USO_RASTER_PATH):
        print(f"Aviso: Raster de Uso do Solo não encontrado.")
    else:
        with rasterio.open(USO_RASTER_PATH) as src: raster_crs = src.crs
        print("Calculando estatísticas de Uso do Solo...")
        for gdf, name in [(gdf_ada, 'ADAs'), (gdf_ae, 'AEs')]:
            stats = zonal_stats(gdf.to_crs(raster_crs), USO_RASTER_PATH, categorical=True)
            top_two = [get_top_two_categories(s) for s in stats]
            gdf['uso_solo_1'] = [item[0] for item in top_two]
            gdf['uso_solo_2'] = [item[1] for item in top_two]
            if name == 'ADAs': gdf_ada = gdf
            else: gdf_ae = gdf
        print("Indicadores de Uso do Solo calculados.")

    # --- 5. VALIDAÇÃO, FORMATAÇÃO E RECONSTRUÇÃO ---
    print("\nValidando e formatando resultados...")
    for gdf in [gdf_ae, gdf_ada]:
        if not gdf.is_valid.all():
            print(f"Aviso: Geometrias inválidas detectadas. Corrigindo...")
            gdf.geometry = gdf.buffer(0)
    
    # Os nomes de saída agora são os nomes originais, para substituição
    output_layer_ada = 'ADAs'
    output_layer_ae = 'AEs'
    temp_gpkg_path = DATA_GPKG.replace(".gpkg", "_temp.gpkg")
    print(f"\nReconstruindo GeoPackage...")
    
    try:
        int_cols = ['riqueza_especies', 'n_registros', 'n_individuos', 'n_ucs_raio_5km', 
                    'area_ha', 'dist_uc_km', 'elevacao_media', 'relevo_m',
                    'uso_solo_1', 'uso_solo_2']
        for col in int_cols:
            if col in gdf_ada.columns: gdf_ada[col] = gdf_ada[col].fillna(0).astype(int)
            if col in gdf_ae.columns: gdf_ae[col] = gdf_ae[col].fillna(0).astype(int)
        
        gdf_ada.drop(columns=['elevacao_min', 'elevacao_max'], inplace=True, errors='ignore')
        gdf_ae.drop(columns=['elevacao_min', 'elevacao_max'], inplace=True, errors='ignore')

        print(f"Salvando camadas enriquecidas...")
        gdf_ae.to_file(temp_gpkg_path, layer=output_layer_ae, driver='GPKG')
        gdf_ada.to_file(temp_gpkg_path, layer=output_layer_ada, driver='GPKG')
        
        print("Copiando camadas de base...")
        for layer_name in LAYERS_TO_KEEP_AS_IS:
            gdf_to_keep = gpd.read_file(DATA_GPKG, layer=layer_name)
            gdf_to_keep.to_file(temp_gpkg_path, layer=layer_name, driver='GPKG')
        
        os.remove(DATA_GPKG); os.rename(temp_gpkg_path, DATA_GPKG)
        print("GeoPackage reconstruído com sucesso.")
    except Exception as e:
        print(f"Erro durante a reconstrução: {e}")
        if os.path.exists(temp_gpkg_path): os.remove(temp_gpkg_path)
    print("\nScript 04 finalizado.")

if __name__ == '__main__':
    main()

