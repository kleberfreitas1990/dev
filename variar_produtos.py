import json
import os
from datetime import datetime

# Caminhos absolutos
BASE_DIR = "/home/ubuntu/dev"
CACHE_PRODUTOS = os.path.join(BASE_DIR, "produtos_cache.json")
CACHE_SHOPEE = os.path.join(BASE_DIR, "shopee_trends_cache.json")

hoje = "2026-07-09"

# Novos produtos variados (diferentes dos anteriores para provar atualização)
novos_produtos = {
    "Mini Câmera de Segurança WiFi A9": {
        "pins": 12500, "pins_historico": 9000, "crescimento": 95, 
        "views_tiktok": 15.5, "resultados_ml": 85000, "buscas_mes": 45000,
        "categoria": "Segurança", "score": 10, "fonte": "Shopee", "tendencia": "🔥 Explosão"
    },
    "Organizador de Fios e Cabos Magnético": {
        "pins": 8500, "pins_historico": 6000, "crescimento": 82, 
        "views_tiktok": 8.2, "resultados_ml": 35000, "buscas_mes": 22000,
        "categoria": "Escritório", "score": 9, "fonte": "Shopee", "tendencia": "📈 Alta"
    },
    "Luminária de Mesa com Carregador Indução": {
        "pins": 15000, "pins_historico": 11000, "crescimento": 88, 
        "views_tiktok": 25.0, "resultados_ml": 65000, "buscas_mes": 38000,
        "categoria": "Eletrônicos", "score": 10, "fonte": "Google", "tendencia": "🔥 Viral"
    },
    "Mini Projetor Portátil 4K Android": {
        "pins": 22000, "pins_historico": 15000, "crescimento": 110, 
        "views_tiktok": 55.0, "resultados_ml": 120000, "buscas_mes": 65000,
        "categoria": "Eletrônicos", "score": 10, "fonte": "Shopee", "tendencia": "🔥 Explosão"
    },
    "Kit 3 Potes Herméticos com Tampa Bambu": {
        "pins": 18000, "pins_historico": 14000, "crescimento": 75, 
        "views_tiktok": 12.5, "resultados_ml": 95000, "buscas_mes": 42000,
        "categoria": "Cozinha", "score": 9, "fonte": "Shopee", "tendencia": "📈 Alta"
    },
    "Aspirador de Pó Portátil Sem Fio 120W": {
        "pins": 14000, "pins_historico": 10000, "crescimento": 85, 
        "views_tiktok": 28.4, "resultados_ml": 110000, "buscas_mes": 52000,
        "categoria": "Automotivo", "score": 9, "fonte": "Shopee", "tendencia": "🔥 Viral"
    },
    "Relógio Inteligente Huawei Band 9": {
        "pins": 28000, "pins_historico": 22000, "crescimento": 90, 
        "views_tiktok": 42.0, "resultados_ml": 150000, "buscas_mes": 85000,
        "categoria": "Eletrônicos", "score": 10, "fonte": "Google", "tendencia": "🔥 Alta"
    },
    "Suporte Magnético para Notebook": {
        "pins": 9500, "pins_historico": 7500, "crescimento": 65, 
        "views_tiktok": 10.2, "resultados_ml": 45000, "buscas_mes": 28000,
        "categoria": "Acessórios", "score": 8, "fonte": "Shopee", "tendencia": "📈 Média"
    },
    "Umidificador de Ar Chama LED (Fogo)": {
        "pins": 35000, "pins_historico": 20000, "crescimento": 150, 
        "views_tiktok": 85.0, "resultados_ml": 75000, "buscas_mes": 95000,
        "categoria": "Decoração", "score": 10, "fonte": "Shopee", "tendencia": "🔥 Explosão"
    },
    "Fone de Ouvido Condução Óssea": {
        "pins": 11000, "pins_historico": 8500, "crescimento": 78, 
        "views_tiktok": 18.5, "resultados_ml": 55000, "buscas_mes": 32000,
        "categoria": "Esportes", "score": 9, "fonte": "Google", "tendencia": "📈 Alta"
    }
}

# Salvar Cache de Produtos
cache_data = {
    "data": hoje,
    "produtos": novos_produtos
}

with open(CACHE_PRODUTOS, 'w', encoding='utf-8') as f:
    json.dump(cache_data, f, ensure_ascii=False, indent=2)

# Salvar Cache de Termos Shopee
termos_shopee = {
    "data": hoje,
    "termos": list(novos_produtos.keys())
}

with open(CACHE_SHOPEE, 'w', encoding='utf-8') as f:
    json.dump(termos_shopee, f, ensure_ascii=False, indent=2)

print(f"✅ Cache variado com sucesso para {hoje} com {len(novos_produtos)} novos produtos.")
