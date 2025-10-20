import geopandas as gpd
import pandas as pd
import os

# --- 1. PARÂMETROS ---

# Caminhos
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, 'data')
DATA_GPKG = os.path.join(data_dir, 'Data.gpkg')

# Camadas de Entrada
AE_LAYER = 'AEs'
UC_LAYER = 'unidades_conservacao_sisema'
ROADS_LAYER = 'rodovias_minas_gerais_sisema'

# Camada de Saída
OUTPUT_LAYER_NAME = 'ADAs'

# Padrões de CRS
CRS_GEOGRAPHIC = 'EPSG:4674'
CRS_PROJECTED = 'EPSG:5880'

# Parâmetros da Simulação
BUFFER_RADIUS_METERS = 500

def main():
    """
    Função principal para gerar as Áreas Diretamente Afetadas (ADAs)
    a partir de um buffer das rodovias contidas em cada AE.
    """
    print("Iniciando Script 02: Geração de ADAs")

    # 2. CARREGAR DADOS
    print(f"Carregando dados de: {DATA_GPKG}")

    gdf_ae_projected = gpd.read_file(DATA_GPKG, layer=AE_LAYER).to_crs(CRS_PROJECTED)
    print("AEs carregadas.")

    all_ucs = gpd.read_file(DATA_GPKG, layer=UC_LAYER)
    ucs_unified_geom = all_ucs.to_crs(CRS_PROJECTED).union_all()
    print("UCs carregadas.")

    gdf_roads_projected = gpd.read_file(DATA_GPKG, layer=ROADS_LAYER).to_crs(CRS_PROJECTED)
    print("Rodovias carregadas.")

    # 3. GERAR ADAs
    print("\nGerando ADAs...")
    all_generated_adas = []

    for index, ae in gdf_ae_projected.iterrows():
        aes_id = ae['aes_id']
        ae_geom = ae['geometry']
        print(f"Processando {aes_id}...")
        
        roads_in_ae = gpd.clip(gdf_roads_projected, ae_geom)
        
        if roads_in_ae.empty:
            print(f"Aviso: Nenhuma rodovia encontrada em {aes_id}.")
            continue
        
        roads_to_buffer = roads_in_ae.union_all()
        ada_candidate = roads_to_buffer.buffer(BUFFER_RADIUS_METERS)
        
        ada_clipped_to_ae = ada_candidate.intersection(ae_geom)
        
        final_ada_geom = ada_clipped_to_ae.difference(ucs_unified_geom)
        
        if final_ada_geom.is_empty:
            print(f"Aviso: ADA vazia para {aes_id} após remoção de UCs.")
            continue
            
        all_generated_adas.append({'geometry': final_ada_geom, 'aes_id': aes_id})
        print(f"ADA para {aes_id} gerada.")

    # 4. SALVAR RESULTADOS
    print("\nSalvando resultados...")
    if all_generated_adas:
        gdf_ada = gpd.GeoDataFrame(all_generated_adas, crs=CRS_PROJECTED)
        
        gdf_ada['adas_id'] = [f'Área Diretamente Afetada {i + 1}' for i in range(len(gdf_ada))]
        
        gdf_ada = gdf_ada[['adas_id', 'aes_id', 'geometry']]
        
        gdf_ada_geographic = gdf_ada.to_crs(CRS_GEOGRAPHIC)
        gdf_ada_geographic.to_file(DATA_GPKG, layer=OUTPUT_LAYER_NAME, driver='GPKG')
        print(f"{len(gdf_ada_geographic)} ADAs salvas.")
    else:
        print("Nenhuma ADA foi gerada.")

    print("\nScript 02 finalizado.")

if __name__ == '__main__':
    main()
