import streamlit as st
import requests
import json
import os
import logging
from datetime import datetime, date
from typing import List, Dict, Optional

from modules.validation import (
    validar_produtos_serper,
    validar_cache_dados,
    sanitizar_json
)

logger = logging.getLogger(__name__)

ARQUIVO_SERPER_CACHE = "serper_cache.json"
ARQUIVO_SERPER_CONTADOR = "serper_contador.json"

# ============================================================
# LIMITE DIÁRIO DE REQUISIÇÕES
# ============================================================
LIMITE_DIARIO_SERPER = 20  # Máximo de 20 requisições por dia

def obter_contador_serper() -> Dict:
    """
    Obtém o contador de requisições do dia
    """
    hoje = date.today().isoformat()
    
    if os.path.exists(ARQUIVO_SERPER_CONTADOR):
        try:
            with open(ARQUIVO_SERPER_CONTADOR, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if dados.get("data") == hoje:
                    return dados
        except:
            pass
    
    # Cria novo contador
    return {
        "data": hoje,
        "total": 0,
        "termos": []
    }

def salvar_contador_serper(contador: Dict) -> bool:
    """
    Salva o contador de requisições
    """
    try:
        with open(ARQUIVO_SERPER_CONTADOR, 'w', encoding='utf-8') as f:
            json.dump(contador, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar contador: {e}")
        return False

def pode_fazer_requisicao_serper(termo: str) -> bool:
    """
    Verifica se pode fazer uma nova requisição
    """
    contador = obter_contador_serper()
    
    # Verifica se já atingiu o limite
    if contador["total"] >= LIMITE_DIARIO_SERPER:
        logger.warning(f"Limite diário de {LIMITE_DIARIO_SERPER} requisições atingido!")
        return False
    
    # Verifica se o termo já foi buscado hoje
    if termo in contador["termos"]:
        logger.info(f"Termo '{termo}' já foi buscado hoje")
        return False
    
    return True

def registrar_requisicao_serper(termo: str) -> bool:
    """
    Registra uma requisição feita
    """
    contador = obter_contador_serper()
    
    contador["total"] += 1
    if termo not in contador["termos"]:
        contador["termos"].append(termo)
    
    return salvar_contador_serper(contador)

def obter_requisicoes_restantes() -> int:
    """
    Retorna quantas requisições restam hoje
    """
    contador = obter_contador_serper()
    return max(0, LIMITE_DIARIO_SERPER - contador["total"])

def buscar_produtos_serper(
    termo: str, 
    limite: int = 5, 
    usar_cache: bool = True
) -> List[Dict]:
    """
    Busca produtos no Google Shopping via Serper.dev com LIMITE DIÁRIO
    """
    
    if not termo or len(termo) < 2:
        return []
    
    # ============================================================
    # 1. VERIFICA CACHE PRIMEIRO (não gasta requisição)
    # ============================================================
    if usar_cache:
        cache = carregar_cache_serper()
        chave_cache = f"serper_{termo}_{limite}"
        if chave_cache in cache:
            dados_cache = cache[chave_cache]
            if validar_cache_dados(dados_cache, "resultados"):
                if dados_cache.get("data") == datetime.now().date().isoformat():
                    logger.info(f"Cache Serper usado para '{termo}'")
                    return dados_cache.get("resultados", [])
    
    # ============================================================
    # 2. VERIFICA LIMITE DE REQUISIÇÕES
    # ============================================================
    if not pode_fazer_requisicao_serper(termo):
        restantes = obter_requisicoes_restantes()
        logger.warning(f"Limite diário atingido. Restam {restantes} requisições.")
        return []
    
    # ============================================================
    # 3. FAZ A REQUISIÇÃO
    # ============================================================
    api_key = st.secrets.get("SERPER_API_KEY", "")
    if not api_key:
        logger.warning("Chave SERPER_API_KEY não configurada")
        return []
    
    try:
        url = "https://google.serper.dev/shopping"
        payload = {"q": termo, "gl": "br", "hl": "pt", "num": limite}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        
        logger.info(f"🔍 Buscando produtos para '{termo}' no Serper...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        # REGISTRA A REQUISIÇÃO (mesmo se falhar)
        registrar_requisicao_serper(termo)
        restantes = obter_requisicoes_restantes()
        logger.info(f"📊 Requisições restantes hoje: {restantes}")
        
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
            
            logger.info(f"✅ Encontrados {len(produtos_validados)} produtos para '{termo}'")
            return produtos_validados
        else:
            logger.error(f"❌ Erro Serper: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar '{termo}': {e}")
        return []

def obter_stats_serper() -> Dict:
    """
    Obtém estatísticas do Serper
    """
    contador = obter_contador_serper()
    
    return {
        "limite_diario": LIMITE_DIARIO_SERPER,
        "usadas_hoje": contador["total"],
        "restantes": max(0, LIMITE_DIARIO_SERPER - contador["total"]),
        "termos_buscados": contador["termos"],
        "data": contador["data"]
    }

def resetar_contador_serper() -> bool:
    """
    Reseta o contador manualmente
    """
    try:
        if os.path.exists(ARQUIVO_SERPER_CONTADOR):
            os.remove(ARQUIVO_SERPER_CONTADOR)
        return True
    except:
        return False

__all__ = [
    'buscar_produtos_serper',
    'obter_stats_serper',
    'resetar_contador_serper',
    'obter_requisicoes_restantes'
]
