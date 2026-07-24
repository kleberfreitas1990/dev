
import json
import os
from datetime import datetime, timedelta

ARQUIVO_PINTEREST_CACHE = "pinterest_trends_cache.json"

def obter_tendencias_pinterest_moda():
    """
    Retorna tendências de moda antecipadas (projeção Agosto 2026)
    Baseado em dados históricos do Pinterest (Julho/Agosto 2025)
    """
    # Dados extraídos da análise do Pinterest Fall/Summer Report 2025
    # Projetando para Agosto 2026 (Transição Inverno -> Primavera no BR)
    raw_data = {
        "Moda Boho Anos 2000": {
            "termo": "Moda Boho Anos 2000",
            "score": 9.8,
            "evento": "Tendência Antecipada: +1.039% de buscas (Pinterest)",
            "categoria": "Moda Feminina",
            "palavra_chave": "look boho chic feminino crochê renda",
            "hashtags": ["#bohochic", "#y2kfashion", "#crochê", "#modafeminina"]
        },
        "Estilo Preppy Vintage": {
            "termo": "Estilo Preppy Vintage",
            "score": 9.5,
            "evento": "Tendência Antecipada: +1.872% de buscas (Pinterest)",
            "categoria": "Moda Geral",
            "palavra_chave": "look preppy vintage listras marinho",
            "hashtags": ["#preppy", "#vintageprep", "#oldmoney", "#modabrasil"]
        },
        "Cores Terrosas (Verde Endro)": {
            "termo": "Roupas Verde Endro",
            "score": 9.2,
            "evento": "Cor do Ano Pinterest 2025/26 (+1.627%)",
            "categoria": "Moda Geral",
            "palavra_chave": "calça de linho verde endro masculino feminino",
            "hashtags": ["#greentrend", "#verdeendro", "#modasustentavel"]
        },
        "Grunge Glam 90s": {
            "termo": "Moda Grunge Glam 90s",
            "score": 8.9,
            "evento": "Tendência Antecipada: +652% de buscas (Pinterest)",
            "categoria": "Beleza/Moda",
            "palavra_chave": "look grunge suave feminino maquiagem 90s",
            "hashtags": ["#grungeglam", "#90saesthetic", "#softgrunge"]
        },
        "Acessórios Vintage (Relógios)": {
            "termo": "Relógio Vintage Digital/Analógico",
            "score": 8.7,
            "evento": "Alta com Homens Gen Z (+82%)",
            "categoria": "Acessórios",
            "palavra_chave": "relógio vintage digital masculino luxo",
            "hashtags": ["#vintagewatch", "#acessoriosmasculinos", "#relogio"]
        },
        "Babydoll Glamour 60s": {
            "termo": "Vestido Babydoll 60s",
            "score": 8.5,
            "evento": "Tendência Antecipada: +2.514% de buscas",
            "categoria": "Moda Feminina",
            "palavra_chave": "vestido babydoll 60s festa vintage",
            "hashtags": ["#60sfashion", "#babydoll", "#vintagefashion"]
        }
    }
    
    # Adiciona a flag de fonte para o agregador
    tendencias = {}
    for nome, dados in raw_data.items():
        tendencias[nome] = dados
        tendencias[nome]["fonte"] = "Pinterest Trends"
        
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
        with open(ARQUIVO_PINTEREST_CACHE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            return cache.get("dados", {})
    return {}
