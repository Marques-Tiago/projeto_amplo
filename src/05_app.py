import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.graph_objects as go
import geopandas as gpd
import pandas as pd
import json
import os

# --- 1. CONFIGURAÇÃO GERAL ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, 'data')
DATA_GPKG = os.path.join(data_dir, 'Data.gpkg')

CRS_LOCAL = 'EPSG:4674'
CRS_MAP = 'EPSG:4326'

LAYER_NAMES = {
    'ae': 'AEs',
    'ada': 'ADAs',
    'gbif': 'gbif_occurrences',
    'mg_limits': 'limites_minas_gerais_sisema',
    'ucs': 'unidades_conservacao_sisema',
}

# --- 2. PAINEL DE CONTROLE DE ESTILOS E APELIDOS ---
STYLE_CONFIG = {
    'mg_limits': {'color': '#333333', 'width': 2.5, 'name': 'Limite de Minas Gerais'},
    'ucs': {'color': 'rgba(0, 128, 0, 0.3)', 'name': 'UCs'},
    'ae': {'color': 'rgba(0, 0, 0, 0)', 'line_color': 'red', 'line_width': 2, 'name': 'Área de Estudo'},
    'ada': {'color': 'rgba(0, 0, 0, 0)', 'line_color': 'black', 'line_width': 2, 'name': 'Áreas diretamente Afetadas'},
    'gbif': {'color': 'orange', 'size': 6, 'opacity': 0.8, 'name': 'Avifauna - GBIF'}
}

COLUMN_ALIASES = {
    'aes_id': 'Área de Estudo',
    'adas_id': 'Área Diretamente Afetada',
    'area_ha': 'Área (ha)',
    'riqueza_especies': 'Riqueza de Espécies',
    'n_registros': 'Nº de Registros',
    'n_individuos': 'Nº de Indivíduos',
    'dist_uc_km': 'Distância até UC (km)',
    'n_ucs_raio_5km': 'Nº de UCs no Raio de 5km',
    'elevacao_media': 'Elevação Média (m)',
    'relevo_m': 'Relevo Local (m)',
    'uso_solo_1': 'Uso do Solo Primário',
    'uso_solo_2': 'Uso do Solo Secundário'
}

# Legenda completa baseada na Coleção 10 do MapBiomas
USO_SOLO_MAP = {
    3: 'Formação Florestal',
    4: 'Formação Savânica',
    5: 'Mangue',
    6: 'Floresta Alagável',
    49: 'Restinga Arbórea',
    11: 'Campo Alagado e Área Pantanosa',
    12: 'Formação Campestre',
    32: 'Apicum',
    29: 'Afloramento Rochoso',
    50: 'Restinga Herbácea',
    15: 'Pastagem',
    19: 'Lavoura Temporária',
    39: 'Soja',
    20: 'Cana',
    40: 'Arroz',
    62: 'Algodão (beta)',
    41: 'Outras Lavouras Temporárias',
    36: 'Lavoura Perene',
    46: 'Café',
    47: 'Citrus',
    35: 'Dendê',
    48: 'Outras Lavouras Perenes',
    9: 'Silvicultura',
    21: 'Mosaico de Usos',
    23: 'Praia, Duna e Areal',
    24: 'Área Urbanizada',
    30: 'Mineração',
    75: 'Usina Fotovoltaica (beta)',
    25: 'Outras Áreas não Vegetadas',
    33: 'Rio, Lago e Oceano',
    31: 'Aquicultura',
    27: 'Não observado',
    1: 'Floresta',
    10: 'Vegetação Herbácea e Arbustiva',
    14: 'Agropecuária',
    18: 'Agricultura',
    22: 'Área não Vegetada',
    26: 'Corpo D\'água',
}

# --- 3. CARREGAMENTO DE DADOS ---
DATA_ERROR_MESSAGE = ""
gdfs = {}
try:
    for key, name in LAYER_NAMES.items():
        gdfs[key] = gpd.read_file(DATA_GPKG, layer=name)
    
    for key in gdfs:
        gdfs[key] = gdfs[key].to_crs(CRS_MAP)
    print("-> Carregamento de dados concluído.")
except Exception as e:
    DATA_ERROR_MESSAGE = f"ERRO AO CARREGAR DADOS: {e}"

# --- 4. INICIALIZAÇÃO E LAYOUT DO APP ---
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Análise da Avifauna em Zonas de Influência Rodoviária próximas a Unidades de Conservação em Minas Gerais'),
    html.Div(children=[html.P(DATA_ERROR_MESSAGE, style={'color': 'red', 'fontWeight': 'bold'})]),
    
    html.Div(
        style={'display': 'flex'},
        children=[
            html.Div(
                dcc.Graph(id='mapa-principal', style={'height': '80vh'}),
                style={'width': '50%', 'padding': '10px'}
            ),
            html.Div(
                children=[
                    html.H3(id='titulo-selecao', children='Selecione uma Área de Estudo ou ADA diretamente no mapa'),
                    html.Div(
                        id='indicator-grid',
                        className='indicator-grid',
                        children=[
                            html.Div(id='indicator-card-1', className='indicator-card'),
                            html.Div(id='indicator-card-2', className='indicator-card'),
                            html.Div(id='indicator-card-3', className='indicator-card'),
                            html.Div(id='indicator-card-4', className='indicator-card'),
                            html.Div(id='indicator-card-5', className='indicator-card'),
                            html.Div(id='indicator-card-6', className='indicator-card'),
                            html.Div(id='indicator-card-7', className='indicator-card'),
                            html.Div(id='indicator-card-8', className='indicator-card'),
                            html.Div(id='indicator-card-9', className='indicator-card'),
                            html.Div(id='indicator-card-10', className='indicator-card'),
                        ]
                    ),
                    html.Hr(),
                    dcc.Graph(id='grafico-comparativo-1'),
                    dcc.Graph(id='grafico-comparativo-2')
                ],
                style={
                    'width': '50%', 
                    'padding': '10px',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'justifyContent': 'flex-start' 
                }
            )
        ]
    )
])

# --- 5. CRIAÇÃO DA FIGURA DO MAPA ---
fig = go.Figure()

if not DATA_ERROR_MESSAGE:
    gdf_mg = gdfs['mg_limits']
    center_lat, center_lon = gdf_mg.geometry.union_all().centroid.y, gdf_mg.geometry.union_all().centroid.x
    zoom_level = 6

    s = STYLE_CONFIG['mg_limits']; mg_boundary = gdf_mg.geometry.union_all().boundary
    fig.add_trace(go.Scattermap(lat=[p[1] for p in mg_boundary.coords], lon=[p[0] for p in mg_boundary.coords], mode='lines', line=dict(width=s['width'], color=s['color']), name=s['name']))

    s = STYLE_CONFIG['ucs']; fig.add_trace(go.Choroplethmap(
        geojson=gdfs['ucs'].geometry.__geo_interface__, 
        locations=gdfs['ucs'].index, 
        z=[1]*len(gdfs['ucs']), 
        colorscale=[[0, s['color']], [1, s['color']]], 
        showscale=False, 
        name=s['name'],
        hovertext=gdfs['ucs']['nome_uc'],
        hovertemplate='<b>%{hovertext}</b><extra></extra>'
    ))  
      
    s = STYLE_CONFIG['ae']; gdf_ae_indexed = gdfs['ae'].set_index('aes_id'); geojson_ae = json.loads(gdf_ae_indexed.to_json())
    fig.add_trace(go.Choroplethmap(geojson=geojson_ae, locations=gdf_ae_indexed.index, featureidkey="id", z=[1]*len(gdf_ae_indexed), customdata=gdf_ae_indexed.index, colorscale=[[0, s['color']], [1, s['color']]], showscale=False, marker_line_width=s['line_width'], marker_line_color=s['line_color'], name=s['name']))

    s = STYLE_CONFIG['ada']; gdf_ada_indexed = gdfs['ada'].set_index('adas_id'); geojson_ada = json.loads(gdf_ada_indexed.to_json())
    fig.add_trace(go.Choroplethmap(geojson=geojson_ada, locations=gdf_ada_indexed.index, featureidkey="id", z=[1]*len(gdf_ada_indexed), customdata=gdf_ada_indexed.index, colorscale=[[0, s['color']], [1, s['color']]], showscale=False, marker_line_width=s['line_width'], marker_line_color=s['line_color'], name=s['name']))

    s = STYLE_CONFIG['gbif']; fig.add_trace(go.Scattermap(lat=gdfs['gbif'].geometry.y, lon=gdfs['gbif'].geometry.x, mode='markers', marker=dict(size=s['size'], color=s['color'], opacity=s['opacity']), name=s['name'], hovertext=gdfs['gbif']['scientificName']))

    fig.update_layout(
        mapbox_style="open-street-map", mapbox_zoom=zoom_level,
        mapbox_center={"lat": center_lon, "lon": center_lon},
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

app.layout.children[2].children[0].children.figure = fig

# --- 6. CALLBACK
@app.callback(
    [
        Output('titulo-selecao', 'children'),
        Output('indicator-card-1', 'children'),
        Output('indicator-card-2', 'children'),
        Output('indicator-card-3', 'children'),
        Output('indicator-card-4', 'children'),
        Output('indicator-card-5', 'children'),
        Output('indicator-card-6', 'children'),
        Output('indicator-card-7', 'children'),
        Output('indicator-card-8', 'children'),
        Output('indicator-card-9', 'children'),
        Output('indicator-card-10', 'children'),
        Output('grafico-comparativo-1', 'figure'),
        Output('grafico-comparativo-2', 'figure')
    ],
    [Input('mapa-principal', 'clickData')]
)
def update_on_click(clickData):
    if not clickData:
        empty_cards = [""] * 10
        empty_figs = [go.Figure(), go.Figure()]
        return ["Selecione uma Área de Estudo ou ADA diretamente no mapa"] + empty_cards + empty_figs

    curve_index = clickData['points'][0]['curveNumber']
    clicked_id = clickData['points'][0]['customdata']

    indicator_order = [
        'area_ha', 'riqueza_especies', 'n_registros', 'n_individuos', 'dist_uc_km',
        'n_ucs_raio_5km', 'elevacao_media', 'relevo_m', 'uso_solo_1', 'uso_solo_2'
    ]
    
    fig1 = go.Figure()
    fig2 = go.Figure()

    if curve_index == 2: # AE clicada
        all_aes = gpd.read_file(DATA_GPKG, layer=LAYER_NAMES['ae'])
        dff = all_aes[all_aes['aes_id'] == clicked_id]
        other_aes_mean = all_aes[all_aes['aes_id'] != clicked_id][indicator_order].mean(numeric_only=True)
        
        fig1.add_trace(go.Bar(name='AE Selecionada', x=['Riqueza de Espécies'], y=dff['riqueza_especies']))
        fig1.add_trace(go.Bar(name='Média das Outras AEs', x=['Riqueza de Espécies'], y=other_aes_mean[['riqueza_especies']]))
        fig1.update_layout(title_text='Riqueza de Espécies: Área de Estudo selecionada vs Média das outras Áreas de Estudo')

        fig2.add_trace(go.Bar(name='AE Selecionada', x=['Nº de UCs no raio'], y=dff['n_ucs_raio_5km']))
        fig2.add_trace(go.Bar(name='Média das Outras AEs', x=['Nº de UCs no raio'], y=other_aes_mean[['n_ucs_raio_5km']]))
        fig2.update_layout(title_text='Nº de UCs no raio de 5km: Área de Estudo selecionada vs Média das outras Áreas de Estudo')
        
        title_prefix = "AE"

    elif curve_index == 3: # ADA clicada
        all_adas = gpd.read_file(DATA_GPKG, layer=LAYER_NAMES['ada'])
        dff = all_adas[all_adas['adas_id'] == clicked_id]
        parent_ae_id = dff['aes_id'].iloc[0]
        all_aes = gpd.read_file(DATA_GPKG, layer=LAYER_NAMES['ae'])
        parent_ae_df = all_aes[all_aes['aes_id'] == parent_ae_id]
        
        fig1.add_trace(go.Bar(name='ADA Selecionada', x=['Riqueza de Espécies'], y=dff['riqueza_especies']))
        fig1.add_trace(go.Bar(name='AE Pai', x=['Riqueza de Espécies'], y=parent_ae_df['riqueza_especies']))
        fig1.update_layout(title_text='Riqueza de Espécies: Área Diretamente Afetada vs Área de Estudo pertencente')

        fig2.add_trace(go.Bar(name='ADA Selecionada', x=['Nº de UCs no Raio'], y=dff['n_ucs_raio_5km']))
        fig2.add_trace(go.Bar(name='AE Pai', x=['Nº de UCs no Raio'], y=parent_ae_df['n_ucs_raio_5km']))
        fig2.update_layout(title_text='Nº de UCs no Raio de 5km: Área Diretamente Afetada vs Área de Estudo pertencente')

        title_prefix = "ADA"
        
    else:
        empty_cards = [""] * 10
        empty_figs = [go.Figure(), go.Figure()]
        return ["Selecione uma Área de Estudo ou ADA diretamente no mapa"] + empty_cards + empty_figs
        
    def create_card(column_id):
        value = dff[column_id].iloc[0]
        if column_id in ['uso_solo_1', 'uso_solo_2']:
            value = USO_SOLO_MAP.get(value, 'Desconhecido')
        return html.Div([html.H5(COLUMN_ALIASES.get(column_id, column_id)), html.P(value)])
    
    outputs = [create_card(col) for col in indicator_order]

    final_return = [f"Atributos para a {title_prefix}: {clicked_id}"] + outputs + [fig1, fig2]
    
    return tuple(final_return)

#7. EXECUTAR O SERVIDOR
if __name__ == '__main__':
    app.run(debug=True)

