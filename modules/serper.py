import streamlit as st
import requests
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

from modules.validation import (
    validar_produtos_serper,
    validar_cache_dados,
    sanitizar_json
)

logger = logging.getLogger(__name__)

ARQUIVO_SERPER_CACHE = "serper_cache.json"

def buscar_produtos_serper(termo: str, limite: int = 5, usar_cache: bool = True) -> List[Dict]:
    if not termo or len(termo) < 2:
        return []
    
    if usar_cache:
        cache = carregar_cache_serper()
        chave_cache = f"serper_{termo}_{limite}"
        if chave_cache in cache:
            dados_cache = cache[chave_cache]
            if validar_cache_dados(dados_cache, "resultados"):
                if dados_cache.get("data") == datetime.now().date().isoformat():
                    logger.info(f"Cache Serper usado para '{termo}'")
                    return dados_cache.get("resultados", [])
    
    api_key = st.secrets.get("SERPER_API_KEY", "")
    if not api_key:
        logger.warning("Chave SERPER_API_KEY não configurada")
        return []
    
    try:
        url = "https://google.serper.dev/shopping"
        payload = {"q": termo, "gl": "br", "hl": "pt", "num": limite}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        
        logger.info(f"Buscando produtos para '{termo}' no Serper...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            produtos_brutos = []
            for item in data.get("shopping", [])[:limite]:
                produtos_brutos.append({
                    "nome": item.get("title", ""),
                    "preco": item.get("price", "R$ 0"),
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "avaliacao": item.get("rating", None)
                })
            
            produtos_validados = validar_produtos_serper(produtos_brutos)
            if produtos_validados and usar_cache:
                salvar_cache_serper(chave_cache, produtos_validados)
            
            logger.info(f"Encontrados {len(produtos_validados)} produtos para '{termo}'")
            return produtos_validados
        else:
            logger.error(f"Erro Serper: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Erro ao buscar '{termo}': {e}")
        return []

def carregar_cache_serper() -> Dict:
    if os.path.exists(ARQUIVO_SERPER_CACHE):
        try:
            with open(ARQUIVO_SERPER_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_cache_serper(chave: str, resultados: List[Dict]) -> bool:
    if not resultados:
        return False
    try:
        cache = carregar_cache_serper()
        cache[chave] = {
            "data": datetime.now().date().isoformat(),
            "resultados": resultados,
            "timestamp": datetime.now().isoformat(),
            "total": len(resultados)
        }
        with open(ARQUIVO_SERPER_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def limpar_cache_serper() -> bool:
    if os.path.exists(ARQUIVO_SERPER_CACHE):
        try:
            os.remove(ARQUIVO_SERPER_CACHE)
            return True
        except:
            pass
    return False

def obter_stats_cache_serper() -> dict:
    stats = {"existe": False, "total_chaves": 0, "total_produtos": 0, "tamanho_kb": 0}
    if os.path.exists(ARQUIVO_SERPER_CACHE):
        stats["existe"] = True
        try:
            with open(ARQUIVO_SERPER_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                stats["total_chaves"] = len(dados)
                total_produtos = 0
                for chave, valor in dados.items():
                    if isinstance(valor, dict) and "resultados" in valor:
                        total_produtos += len(valor.get("resultados", []))
                stats["total_produtos"] = total_produtos
                stats["tamanho_kb"] = round(os.path.getsize(ARQUIVO_SERPER_CACHE) / 1024, 2)
        except:
            pass
    return stats

__all__ = [
    'buscar_produtos_serper',
    'limpar_cache_serper',
    'obter_stats_cache_serper'
]
