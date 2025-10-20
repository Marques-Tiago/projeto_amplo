Projeto de Análise Ambiental e Web GIS

Este repositório contém o código e os dados para um projeto de análise ambiental, culminando em um dashboard interativo (Web GIS) construído com Python e Dash.

O projeto simula Áreas de Estudo (AEs) e Áreas Diretamente Afetadas (ADAs), busca dados de ocorrências de espécies do GBIF, calcula indicadores ambientais (vetoriais e raster) e apresenta os resultados em uma interface web.

Estrutura do Projeto

projeto_amplo/
│
├── .gitignore          # Ignora arquivos desnecessários (ambientes virtuais, cache)
├── README.md           # Este arquivo
├── requirements.txt    # Lista de dependências do Python para recriar o ambiente
│
├── assets/             # Arquivos CSS e outros para o dashboard Dash
│   └── style.css
│
├── data/               # Dados brutos e processados
│   └── Data.gpkg       # O GeoPackage central com todas as camadas
│
└── src/                # Código fonte do projeto
    ├── 01_gerar_aes.py
    ├── 02_gerar_adas.py
    ├── 03_download_gbif.py
    ├── 04_calculate_indicators.py
    └── app.py


Como Executar

Este projeto requer Python 3.9 ou superior.

1. Configuração do Ambiente

Clone o repositório e navegue até a pasta do projeto. Recomenda-se o uso de um ambiente virtual.

# 1. Crie um ambiente virtual
python -m venv venv

# 2. Ative o ambiente
# No Windows
.\venv\Scripts\activate
# No macOS/Linux
# source venv/bin/activate

# 3. Instale as dependências a partir da "lista de compras"
pip install -r requirements.txt


2. Execução do Pipeline de Dados

Os scripts devem ser executados em ordem para gerar e processar os dados. Eles irão criar e modificar o arquivo data/Data.gpkg.

# Execute um de cada vez, na ordem
python src/01_gerar_aes.py
python src/02_gerar_adas.py
python src/03_download_gbif.py
python src/04_calculate_indicators.py


3. Execução do Dashboard Web

Após a execução do pipeline de dados, inicie a aplicação Dash.

python src/app.py


Acesse o dashboard no seu navegador através do endereço http://127.0.0.1:8050/.