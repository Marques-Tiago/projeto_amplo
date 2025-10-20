import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box
import os

# --- 1. PARÂMETROS ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, 'data')
DATA_GPKG = os.path.join(data_dir, 'Data.gpkg')

# Camadas de Entrada do Geopackage
MG_BOUNDARY_LAYER = 'limites_minas_gerais_sisema'
UC_LAYER = 'unidades_conservacao_sisema' 
ROADS_LAYER = 'rodovias_minas_gerais_sisema'

# Camada de SAÍDA
OUTPUT_LAYER_NAME = 'AEs'

# Padrões de CRS
CRS_GEOGRAPHIC = 'EPSG:4674'
CRS_PROJECTED = 'EPSG:5880'

# Parâmetros da Simulação
NUM_AE_TO_GENERATE = 15
AE_WIDTH_KM = 20
AE_HEIGHT_KM = 15
BUFFER_DISTANCE_KM = 5
MAX_ATTEMPTS = 30000

def main():
    """
    Função principal para gerar as Áreas de Estudo (AEs).
    """
    print("Iniciando Script 01: Geração de AEs")
    np.random.seed(42)
    
    # --- 2. DADOS DE ENTRADA / GEOMETRIA ---
    print(f"Carregando dados de: {DATA_GPKG}")

    # Carregar limite de Minas Gerais
    mg_boundary_gdf = gpd.read_file(DATA_GPKG, layer=MG_BOUNDARY_LAYER)
    mg_boundary_projected_geom = mg_boundary_gdf.to_crs(CRS_PROJECTED).union_all()
    print("Limite de MG carregado.")

    print(f"Carregando UCs: '{UC_LAYER}'")
    all_ucs = gpd.read_file(DATA_GPKG, layer=UC_LAYER)
    ucs_unified_projected_geom = all_ucs.to_crs(CRS_PROJECTED).union_all()
    print(f"{len(all_ucs)} UCs carregadas.")

    # Unificar Rodovias
    gdf_roads = gpd.read_file(DATA_GPKG, layer=ROADS_LAYER)
    roads_unified_projected_geom = gdf_roads.to_crs(CRS_PROJECTED).union_all()
    print("Rodovias carregadas.")

    #3. GERANDO ÁREAS DE ESTUDO SEGUNDO REGRAS
    print(f"\nGerando {NUM_AE_TO_GENERATE} retângulos...")

    generated_polygons = []
    minx, miny, maxx, maxy = mg_boundary_projected_geom.bounds
    width_m = AE_WIDTH_KM * 1000
    height_m = AE_HEIGHT_KM * 1000
    max_distance_m = BUFFER_DISTANCE_KM * 1000
    attempts = 0

    while len(generated_polygons) < NUM_AE_TO_GENERATE and attempts < MAX_ATTEMPTS:
        attempts += 1
        
        rand_x = np.random.uniform(minx, maxx)
        rand_y = np.random.uniform(miny, maxy)
        
        candidate_rectangle = box(rand_x - width_m/2, rand_y - height_m/2, 
                                  rand_x + width_m/2, rand_y + height_m/2)

        if not candidate_rectangle.within(mg_boundary_projected_geom):
            continue
        
        if candidate_rectangle.within(ucs_unified_projected_geom):
            continue

        if candidate_rectangle.distance(ucs_unified_projected_geom) > max_distance_m:
            continue

        if not candidate_rectangle.intersects(roads_unified_projected_geom):
            continue
            
        if any(candidate_rectangle.intersects(p) for p in generated_polygons):
            continue

        generated_polygons.append(candidate_rectangle)
        print(f"AE {len(generated_polygons)}/{NUM_AE_TO_GENERATE} gerada. (Tentativa {attempts})")

    if len(generated_polygons) < NUM_AE_TO_GENERATE:
        print(f"\nAviso: Apenas {len(generated_polygons)} de {NUM_AE_TO_GENERATE} AEs foram geradas.")
    else:
        print(f"\n{len(generated_polygons)} AEs geradas com sucesso.")

    # 4. SALVAR RESULTADOS
    print("\nSalvando resultados...")
    if generated_polygons:
        gdf_ae = gpd.GeoDataFrame(geometry=generated_polygons, crs=CRS_PROJECTED)
        gdf_ae['aes_id'] = [f'Área de Estudo {i + 1}' for i in range(len(gdf_ae))]
        gdf_ae = gdf_ae[['aes_id', 'geometry']]
        gdf_ae_geographic = gdf_ae.to_crs(CRS_GEOGRAPHIC)
        gdf_ae_geographic.to_file(DATA_GPKG, layer=OUTPUT_LAYER_NAME, driver='GPKG')
        print(f"Camada '{OUTPUT_LAYER_NAME}' salva em '{DATA_GPKG}'.")
    else:
        print("Nenhuma AE foi gerada.")
    
    print("\nScript 01 finalizado.")

if __name__ == '__main__':
    main()

