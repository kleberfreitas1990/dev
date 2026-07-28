import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ARQUIVO_PINTEREST_CACHE = "pinterest_trends_cache.json"

def obter_tendencias_pinterest():
    """
    Retorna as tendências reais do Pinterest Brasil filtradas por Moda Feminina (25-49 anos).
    Dados extraídos em 28/07/2026.
    """
    raw_data = {
        "Moda Estádio": {
            "termo": "Roupa para estádio",
            "score": 9.9,
            "evento": "Tendência Explosiva: +10.000% de buscas (Brasil)",
            "categoria": "Moda Feminina",
            "palavra_chave": "look para estádio de futebol feminino inspiração",
            "hashtags": ["#modafutebol", "#lookestadio", "#feminino", "#estilofutebol"]
        },
        "Unhas Elegantes": {
            "termo": "Uñas elegantes y sencillas",
            "score": 9.7,
            "evento": "Alta Demanda: Público 25-49 anos",
            "categoria": "Beleza/Moda",
            "palavra_chave": "unhas elegantes e simples tendências 2026",
            "hashtags": ["#unhas", "#nailart", "#elegancia", "#belezafeminina"]
        },
        "Penteados Tendência": {
            "termo": "Peinados (Penteados)",
            "score": 9.5,
            "evento": "Top Volume: Tendência em crescimento (Brasil)",
            "categoria": "Beleza/Moda",
            "palavra_chave": "penteados femininos modernos 2026",
            "hashtags": ["#penteados", "#cabelos", "#tendenciascabelo", "#hairinspo"]
        },
        "Design de Unhas": {
            "termo": "Diseños de uñas",
            "score": 9.3,
            "evento": "Alta Busca: Categoria Moda Feminina",
            "categoria": "Beleza/Moda",
            "palavra_chave": "design de unhas decoradas modernas",
            "hashtags": ["#naildesign", "#unhasdecoradas", "#beleza", "#moda"]
        },
        "Unhas Amendoadas": {
            "termo": "Uñas almendradas",
            "score": 9.1,
            "evento": "Tendência Específica: Formato em alta no Brasil",
            "categoria": "Beleza/Moda",
            "palavra_chave": "unhas amendoadas decoradas inspiração",
            "hashtags": ["#unhasamendoadas", "#almondnails", "#estilo", "#beleza"]
        },
        "Kylian Dictator": {
            "termo": "Kylian Dictator (Cultura Pop)",
            "score": 8.9,
            "evento": "Viral: +10.000% (Influência no Estilo)",
            "categoria": "Entretenimento/Moda",
            "palavra_chave": "mbappe meme style cultura pop 2026",
            "hashtags": ["#mbappe", "#culturapop", "#tendenciaviral", "#estilo"]
        }
    }
    
    # Adiciona a flag de fonte para o agregador
    tendencias = {}
    for nome, dados in raw_data.items():
        tendencias[nome] = dados
        tendencias[nome]["fonte"] = "Pinterest Trends (Moda Feminina)"
    return tendencias

def salvar_cache_pinterest(dados):
    cache = {
        "timestamp": datetime.now().isoformat(),
        "data": datetime.now().strftime("%Y-%m-%d"),
        "dados": dados
    }
    with open(ARQUIVO_PINTEREST_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def obter_pinterest_trends_cache():
    if os.path.exists(ARQUIVO_PINTEREST_CACHE):
        try:
            with open(ARQUIVO_PINTEREST_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                return cache.get("dados", {})
        except Exception as e:
            logger.error(f"Erro ao ler cache do Pinterest: {e}")
    return {}
