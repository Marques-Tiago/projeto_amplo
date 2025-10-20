# Análise da Avifauna em Zonas de Influência Rodoviária Próximas a Unidades de Conservação em Minas Gerais

Este repositório contém o código e os dados para um projeto de análise ambiental, culminando em um **dashboard interativo (Web GIS)** construído com **Python** e **Dash**.

O projeto simula Áreas de Estudo (AEs) e Áreas Diretamente Afetadas (ADAs), obtém dados de ocorrências de espécies do GBIF, calcula indicadores ambientais (vetoriais e raster) e apresenta os resultados de forma interativa na web.

### Estrutura do Repositório
projeto_amplo/ │ ├── .gitignore # Ignora arquivos desnecessários (ambientes virtuais, cache) ├── README.md # Este arquivo ├── requirements.txt # Lista de dependências do Python │ ├── assets/ # Arquivos CSS e recursos do dashboard │ └── style.css │ ├── data/ # Dados brutos e processados │ └── Data.gpkg # GeoPackage central com todas as camadas │ └── raster/ # Raster do projeto (download abaixo) │ └── src/ # Código-fonte ├── 01_gerar_aes.py ├── 02_gerar_adas.py ├── 03_download_gbif.py ├── 04_calculate_indicators.py └── app.py


## Download dos Dados

O raster do projeto pode ser baixado neste link do Google Drive e deverá ser salvo na pasta "Data" com o nome "raster".

[Download Raster](https://drive.google.com/drive/folders/1PMvYD3S4GAeBGPcm4YG0z3nCJ_qUBcB2?usp=drive_link)

## Como Executar

Este projeto requer **Python 3.9 ou superior**.

### 1. Configuração do Ambiente

Clone o repositório e navegue até a pasta do projeto.

2. Execução do Pipeline de Dados
# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

### 2. Execução do Pipeline de Dados
Os scripts devem ser executados em ordem para gerar e processar os dados. Eles irão criar ou modificar o arquivo data/Data.gpkg.

python src/01_gerar_aes.py
python src/02_gerar_adas.py
python src/03_download_gbif.py
python src/04_calculate_indicators.py

### 3. Execução do Dashboard Web
Após executar o pipeline de dados, inicie a aplicação Dash.

python src/app.py
Acesse o dashboard no seu navegador em: http://127.0.0.1:8050/
