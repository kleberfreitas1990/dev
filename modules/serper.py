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

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
ARQUIVO_SERPER_CACHE = "serper_cache.json"

# ============================================================
# FUNÇÃO PARA BUSCAR PRODUTOS VIA SERPER.DEV
# ============================================================
def buscar_produtos_serper(
    termo: str, 
    limite: int = 5, 
    usar_cache: bool = True
) -> List[Dict]:
    """
    Busca produtos no Google Shopping via Serper.dev com validação
    
    Args:
        termo (str): Termo de busca
        limite (int): Número de resultados
        usar_cache (bool): Usar cache para reduzir custos
    
    Returns:
        List[Dict]: Lista de produtos validados
    """
    
    # Valida o termo de busca
    if not termo or len(termo) < 2:
        logger.warning(f"Termo de busca inválido: {termo}")
        return []
    
    # Verifica cache
    if usar_cache:
        cache = carregar_cache_serper()
        chave_cache = f"serper_{termo}_{limite}"
        if chave_cache in cache:
            dados_cache = cache[chave_cache]
            if validar_cache_dados(dados_cache, "resultados"):
                # Verifica se é do mesmo dia
                if dados_cache.get("data") == datetime.now().date().isoformat():
                    logger.info(f"Cache Serper usado para '{termo}'")
                    return dados_cache.get("resultados", [])
    
    # Busca na API
    api_key = st.secrets.get("SERPER_API_KEY", "")
    if not api_key:
        logger.warning("Chave SERPER_API_KEY não configurada")
        return []
    
    try:
        url = "https://google.serper.dev/shopping"
        payload = {
            "q": termo,
            "gl": "br",
            "hl": "pt",
            "num": limite
        }
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
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
            
            # Valida os produtos
            produtos_validados = validar_produtos_serper(produtos_brutos)
            
            if produtos_validados and usar_cache:
                salvar_cache_serper(chave_cache, produtos_validados)
            
            logger.info(f"Encontrados {len(produtos_validados)} produtos para '{termo}'")
            return produtos_validados
        else:
            logger.error(f"Erro Serper: {response.status_code} - {response.text[:200]}")
            return []
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout ao buscar '{termo}' no Serper")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede ao buscar '{termo}': {e}")
        return []
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar '{termo}': {e}")
        return []

# ============================================================
# FUNÇÕES DE CACHE
# ============================================================
def carregar_cache_serper() -> Dict:
    """Carrega o cache do Serper.dev com validação"""
    if os.path.exists(ARQUIVO_SERPER_CACHE):
        try:
            with open(ARQUIVO_SERPER_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Erro ao ler cache Serper: {e}")
            return {}
    return {}

def salvar_cache_serper(chave: str, resultados: List[Dict]) -> bool:
    """Salva resultados no cache com validação"""
    if not resultados:
        logger.warning(f"Tentativa de salvar cache vazio para '{chave}'")
        return False
    
    try:
        cache = carregar_cache_serper()
        
        # Sanitiza os dados antes de salvar
        resultados_sanitizados = [sanitizar_json(p) for p in resultados]
        
        cache[chave] = {
            "data": datetime.now().date().isoformat(),
            "resultados": resultados_sanitizados,
            "timestamp": datetime.now().isoformat(),
            "total": len(resultados_sanitizados)
        }
        
        with open(ARQUIVO_SERPER_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cache Serper salvo para '{chave}' ({len(resultados)} produtos)")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar cache Serper: {e}")
        return False

def limpar_cache_serper() -> bool:
    """Limpa o cache do Serper"""
    if os.path.exists(ARQUIVO_SERPER_CACHE):
        try:
            os.remove(ARQUIVO_SERPER_CACHE)
            logger.info("Cache Serper removido")
            return True
        except IOError as e:
            logger.error(f"Erro ao remover cache Serper: {e}")
            return False
    return True

def buscar_total_resultados_serper(termo: str) -> int:
    """
    Busca o total de resultados para um termo
    
    Args:
        termo (str): Termo de busca
        
    Returns:
        int: Número total de resultados
    """
    produtos = buscar_produtos_serper(termo, 10, usar_cache=True)
    return len(produtos) * 10  # Estimativa

def obter_stats_cache_serper() -> dict:
    """
    Obtém estatísticas do cache do Serper
    
    Returns:
        dict: Estatísticas do cache
    """
    stats = {
        "existe": False,
        "total_chaves": 0,
        "total_produtos": 0,
        "tamanho_kb": 0
    }
    
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
        except Exception as e:
            logger.error(f"Erro ao ler estatísticas Serper: {e}")
    
    return stats

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'buscar_produtos_serper',
    'buscar_total_resultados_serper',
    'limpar_cache_serper',
    'obter_stats_cache_serper'
]
