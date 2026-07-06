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
            # Verifica se o cache é de hoje
            if dados_cache.get("data") == datetime.now().date().isoformat():
                return dados_cache.get("resultados", [])
    
    # Busca na API
    api_key = st.secrets.get("SERPER_API_KEY", "")
    if not api_key:
        st.warning("⚠️ Chave Serper.dev não configurada. Adicione SERPER_API_KEY no secrets.toml")
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
            
            # Extrai produtos do resultado
            for item in data.get("shopping", [])[:limite]:
                # Pega o preço
                preco_str = item.get("price", "R$ 0")
                try:
                    preco_num = float(preco_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
                except:
                    preco_num = 0
                
                resultados.append({
                    "nome": item.get("title", ""),
                    "preco": preco_str,
                    "preco_numero": preco_num,
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "imagem": item.get("imageUrl", ""),
                    "avaliacao": item.get("rating", None)
                })
            
            # Salva no cache
            if usar_cache:
                salvar_cache_serper(chave_cache, resultados)
            
            return resultados
        else:
            st.error(f"❌ Erro Serper.dev: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        st.error(f"❌ Erro na busca Serper.dev: {e}")
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

def limpar_cache_serper():
    """Limpa o cache do Serper.dev"""
    if os.path.exists(ARQUIVO_SERPER_CACHE):
        os.remove(ARQUIVO_SERPER_CACHE)
        return True
    return False

def buscar_total_resultados_serper(termo):
    """Busca o total de resultados para um termo"""
    produtos = buscar_produtos_serper(termo, 10)
    return len(produtos) * 10  # Estimativa

# ============================================================
# FUNÇÃO PARA BUSCAR TRENDS VIA SERPER
# ============================================================
def buscar_trends_serper():
    """Busca tendências atuais via Serper.dev"""
    
    api_key = st.secrets.get("SERPER_API_KEY", "")
    if not api_key:
        return []
    
    # Tenta buscar tendências de produtos
    termos_tendencia = [
        "produtos mais vendidos Brasil",
        "tendências de moda 2026",
        "eletrônicos mais procurados",
        "brinquedos populares"
    ]
    
    resultados = []
    for termo in termos_tendencia[:2]:
        produtos = buscar_produtos_serper(termo, 3)
        for p in produtos:
            nome = p.get("nome", "")
            if nome and len(nome) > 3:
                # Pega as primeiras palavras como termo de tendência
                palavras = nome.split()[:3]
                if palavras:
                    termo_sugerido = " ".join(palavras)
                    if termo_sugerido not in resultados:
                        resultados.append(termo_sugerido)
    
    return resultados[:10]

# ============================================================
# FUNÇÃO PARA BUSCAR PRODUTOS (ALIAS)
# ============================================================
def buscar_produtos(termo, limite=5):
    """Alias para buscar_produtos_serper - mantém compatibilidade"""
    return buscar_produtos_serper(termo, limite)

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'buscar_produtos_serper',
    'buscar_total_resultados_serper',
    'buscar_trends_serper',
    'buscar_produtos',
    'limpar_cache_serper'
]
