import geopandas as gpd
import pandas as pd
from pygbif import occurrences as occ
import os

# 1. PARÂMETROS
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, 'data')
DATA_GPKG = os.path.join(data_dir, 'Data.gpkg')

# Camadas de Entrada e Saída
AE_LAYER = 'AEs'
OUTPUT_LAYER_NAME = 'gbif_occurrences'

# Padrões de CRS
CRS_LOCAL = 'EPSG:4674'
CRS_API = 'EPSG:4326'

# Parâmetros da consulta
CLASS_KEY_AVES = 212
LIMIT_PER_AE = 1000

# Colunas de interesse
GBIF_COLUMNS = [
    'key', 'scientificName', 'family', 'order', 'eventDate',
    'basisOfRecord', 'decimalLatitude', 'decimalLongitude',
    'stateProvince', 'datasetName', 'recordedBy'
]

def main():
    """
    Função principal para baixar ocorrências de aves do GBIF para cada AE.
    """
    print("Iniciando Script 03: Download de dados do GBIF")

    # 2. CARREGAR DADOS
    print(f"Carregando AEs de '{DATA_GPKG}'...")
    try:
        gdf_ae = gpd.read_file(DATA_GPKG, layer=AE_LAYER)
    except Exception as e:
        print(f"Erro: Não foi possível ler a camada '{AE_LAYER}'.")
        print(e)
        return

    gdf_ae = gdf_ae.set_crs(CRS_LOCAL, allow_override=True)
    print(f"{len(gdf_ae)} AEs carregadas.")

    # 3. CONSULTAR GBIF
    all_occurrences_dfs = []
    print("\nConsultando a API do GBIF...")

    for index, ae in gdf_ae.iterrows():
        # MUDANÇA CRÍTICA: Usa o nome de coluna correto 'aes_id'
        aes_id = ae['aes_id']
        geom_local = ae['geometry']
        
        print(f"Consultando para {aes_id}...", end=' ')

        try:
            geom_api = gpd.GeoSeries([geom_local], crs=CRS_LOCAL).to_crs(CRS_API).iloc[0]
            
            response = occ.search(
                classKey=CLASS_KEY_AVES,
                geometry=geom_api.wkt,
                limit=LIMIT_PER_AE,
                hasCoordinate=True
            )

            records = response['results']
            
            if records:
                print(f"Encontrados {len(records)} registros.")
                df = pd.DataFrame(records)
                # MUDANÇA CRÍTICA: Cria a coluna com o nome correto 'aes_id'
                df['aes_id'] = aes_id
                all_occurrences_dfs.append(df)
            else:
                print("Nenhum registro encontrado.")

        except Exception as e:
            print(f"Erro na consulta para {aes_id}: {e}")

    # 4. PROCESSAR E CONVERTER DADOS
    if not all_occurrences_dfs:
        print("\nNenhum registro baixado. Encerrando.")
        return

    print("\nProcessando registros baixados...")
    
    final_df = pd.concat(all_occurrences_dfs, ignore_index=True)

    cols_to_keep = [col for col in GBIF_COLUMNS if col in final_df.columns]
    # MUDANÇA CRÍTICA: Adiciona a coluna com o nome correto 'aes_id'
    cols_to_keep.append('aes_id')
    
    processed_df = final_df[cols_to_keep].copy()
    processed_df.rename(columns={'key': 'gbifID'}, inplace=True)
    processed_df['n_individuals'] = 1
    processed_df.dropna(subset=['decimalLongitude', 'decimalLatitude'], inplace=True)
    
    if processed_df.empty:
        print("Nenhum registro válido com coordenadas.")
        return

    gdf_occurrences_api_crs = gpd.GeoDataFrame(
        processed_df,
        geometry=gpd.points_from_xy(processed_df.decimalLongitude, processed_df.decimalLatitude),
        crs=CRS_API
    )

    # 5. SALVAR RESULTADOS
    print(f"Convertendo {len(gdf_occurrences_api_crs)} ocorrências para {CRS_LOCAL}...")
    gdf_occurrences_local_crs = gdf_occurrences_api_crs.to_crs(CRS_LOCAL)

    print(f"Salvando resultados na camada '{OUTPUT_LAYER_NAME}'...")
    try:
        gdf_occurrences_local_crs.to_file(DATA_GPKG, layer=OUTPUT_LAYER_NAME, driver='GPKG')
        print("Dados salvos com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        
    print("\nScript 03 finalizado.")

if __name__ == '__main__':
    main()