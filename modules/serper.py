import streamlit as st
import requests
import json
import os
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================
ARQUIVO_SERPER_CACHE = "serper_cache.json"

# ============================================================
# FUNÇÃO PARA BUSCAR PRODUTOS VIA SERPER.DEV
# ============================================================
def buscar_produtos_serper(termo, limite=5, usar_cache=True):
    """
    Busca produtos no Google Shopping via Serper.dev
    
    Args:
        termo (str): Termo de busca
        limite (int): Número de resultados
        usar_cache (bool): Usar cache para reduzir custos
    
    Returns:
        list: Lista de produtos encontrados
    """
    
    # Verifica cache
    if usar_cache:
        cache = carregar_cache_serper()
        chave_cache = f"serper_{termo}_{limite}"
        if chave_cache in cache:
            dados_cache = cache[chave_cache]
            if dados_cache.get("data") == datetime.now().date().isoformat():
                return dados_cache.get("resultados", [])
    
    # Busca na API
    api_key = st.secrets.get("SERPER_API_KEY", "")
    if not api_key:
        return []
    
    try:
        url = "https://google.serper.dev/shopping"
        payload = {
            "q": termo,
            "gl": "br",
            "hl": "pt"
        }
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            resultados = []
            
            for item in data.get("shopping", [])[:limite]:
                resultados.append({
                    "nome": item.get("title", ""),
                    "preco": item.get("price", "R$ 0"),
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "avaliacao": item.get("rating", None)
                })
            
            if usar_cache:
                salvar_cache_serper(chave_cache, resultados)
            
            return resultados
        else:
            return []
            
    except Exception as e:
        return []

# ============================================================
# FUNÇÕES DE CACHE
# ============================================================
def carregar_cache_serper():
    """Carrega o cache do Serper.dev"""
    if os.path.exists(ARQUIVO_SERPER_CACHE):
        try:
            with open(ARQUIVO_SERPER_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_cache_serper(chave, resultados):
    """Salva resultados no cache"""
    cache = carregar_cache_serper()
    cache[chave] = {
        "data": datetime.now().date().isoformat(),
        "resultados": resultados
    }
    with open(ARQUIVO_SERPER_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def buscar_total_resultados_serper(termo):
    """Busca o total de resultados para um termo"""
    produtos = buscar_produtos_serper(termo, 10)
    return len(produtos) * 10

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'buscar_produtos_serper',
    'buscar_total_resultados_serper'
]
