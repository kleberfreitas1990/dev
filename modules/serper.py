import streamlit as st
import requests
import json
import os
import logging
import time
from datetime import datetime, date
from typing import List, Dict, Optional

from modules.validation import (
    validar_produtos_serper,
    validar_cache_dados,
    sanitizar_json
)
from modules.logger import registrar_busca

logger = logging.getLogger(__name__)

ARQUIVO_SERPER_CACHE = "serper_cache.json"
ARQUIVO_SERPER_CONTADOR = "serper_contador.json"

# ============================================================
# LIMITE DIÁRIO DE REQUISIÇÕES
# ============================================================
LIMITE_DIARIO_SERPER = 20

# ============================================================
# FUNÇÕES DE CONTADOR
# ============================================================
def obter_contador_serper() -> Dict:
    """Obtém o contador de requisições do dia"""
    hoje = date.today().isoformat()
    
    if os.path.exists(ARQUIVO_SERPER_CONTADOR):
        try:
            with open(ARQUIVO_SERPER_CONTADOR, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if dados.get("data") == hoje:
                    return dados
        except:
            pass
    
    return {"data": hoje, "total": 0, "termos": []}

def salvar_contador_serper(contador: Dict) -> bool:
    """Salva o contador de requisições"""
    try:
        with open(ARQUIVO_SERPER_CONTADOR, 'w', encoding='utf-8') as f:
            json.dump(contador, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar contador: {e}")
        return False

def pode_fazer_requisicao_serper(termo: str) -> bool:
    """Verifica se pode fazer uma nova requisição"""
    contador = obter_contador_serper()
    
    if contador["total"] >= LIMITE_DIARIO_SERPER:
        logger.warning(f"Limite diário de {LIMITE_DIARIO_SERPER} requisições atingido!")
        return False
    
    if termo in contador["termos"]:
        logger.info(f"Termo '{termo}' já foi buscado hoje")
        return False
    
    return True

def registrar_requisicao_serper(termo: str) -> bool:
    """Registra uma requisição feita"""
    contador = obter_contador_serper()
    contador["total"] += 1
    if termo not in contador["termos"]:
        contador["termos"].append(termo)
    return salvar_contador_serper(contador)

def obter_requisicoes_restantes() -> int:
    """Retorna quantas requisições restam hoje"""
    contador = obter_contador_serper()
    return max(0, LIMITE_DIARIO_SERPER - contador["total"])

def obter_stats_serper() -> Dict:
    """Obtém estatísticas do Serper"""
    contador = obter_contador_serper()
    return {
        "limite_diario": LIMITE_DIARIO_SERPER,
        "usadas_hoje": contador["total"],
        "restantes": max(0, LIMITE_DIARIO_SERPER - contador["total"]),
        "termos_buscados": contador["termos"],
        "data": contador["data"]
    }

def resetar_contador_serper() -> bool:
    """Reseta o contador manualmente"""
    try:
        if os.path.exists(ARQUIVO_SERPER_CONTADOR):
            os.remove(ARQUIVO_SERPER_CONTADOR)
            logger.info("Contador Serper resetado manualmente")
        return True
    except Exception as e:
        logger.error(f"Erro ao resetar contador: {e}")
        return False

# ============================================================
# FUNÇÃO PARA OBTER CHAVE DA API
# ============================================================
def obter_chave_serper() -> str:
    """
    Obtém a chave da API Serper dos secrets
    """
    try:
        # Tenta diferentes formas de acessar
        if hasattr(st, 'secrets'):
            chave = st.secrets.get("SERPER_API_KEY", "")
            if chave:
                return chave
        
        # Fallback: tenta variável de ambiente
        import os
        chave = os.environ.get("SERPER_API_KEY", "")
        if chave:
            return chave
            
        logger.warning("Chave SERPER_API_KEY não encontrada nos secrets")
        return ""
    except Exception as e:
        logger.error(f"Erro ao obter chave Serper: {e}")
        return ""

# ============================================================
# FUNÇÃO PRINCIPAL DE BUSCA
# ============================================================
def buscar_produtos_serper(termo: str, limite: int = 5, usar_cache: bool = True) -> List[Dict]:
    """Busca produtos no Google Shopping via Serper.dev com LIMITE DIÁRIO"""
    
    inicio = time.time()
    
    if not termo or len(termo) < 2:
        return []
    
    # 1. VERIFICA CACHE
    if usar_cache:
        cache = carregar_cache_serper()
        chave_cache = f"serper_{termo}_{limite}"
        if chave_cache in cache:
            dados_cache = cache[chave_cache]
            if validar_cache_dados(dados_cache, "resultados"):
                if dados_cache.get("data") == datetime.now().date().isoformat():
                    logger.info(f"Cache Serper usado para '{termo}'")
                    resultados = dados_cache.get("resultados", [])
                    registrar_busca(
                        nivel="cache",
                        termo=termo,
                        sucesso=True,
                        quantidade=len(resultados),
                        detalhes=f"Cache Serper usado para '{termo}'",
                        tempo_execucao=time.time() - inicio
                    )
                    return resultados
    
    # 2. OBTÉM A CHAVE
    api_key = obter_chave_serper()
    if not api_key:
        logger.error("❌ Chave SERPER_API_KEY não configurada!")
        registrar_busca(
            nivel="api",
            termo=termo,
            sucesso=False,
            quantidade=0,
            detalhes="Chave Serper não configurada",
            tempo_execucao=time.time() - inicio,
            erro="SERPER_API_KEY não encontrada"
        )
        return []
    
    # 3. VERIFICA LIMITE
    if not pode_fazer_requisicao_serper(termo):
        restantes = obter_requisicoes_restantes()
        logger.warning(f"Limite diário atingido. Restam {restantes} requisições.")
        registrar_busca(
            nivel="api",
            termo=termo,
            sucesso=False,
            quantidade=0,
            detalhes=f"Limite diário atingido. Restam {restantes}",
            tempo_execucao=time.time() - inicio,
            erro="Limite diário atingido"
        )
        return []
    
    # 4. FAZ A REQUISIÇÃO
    try:
        url = "https://google.serper.dev/shopping"
        payload = {"q": termo, "gl": "br", "hl": "pt", "num": limite}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        
        logger.info(f"🔍 Buscando produtos para '{termo}' no Serper...")
        logger.info(f"   Chave: {api_key[:10]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
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
            
            registrar_busca(
                nivel="api",
                termo=termo,
                sucesso=True,
                quantidade=len(produtos_validados),
                detalhes=f"Encontrados {len(produtos_validados)} produtos",
                tempo_execucao=time.time() - inicio
            )
            
            logger.info(f"✅ Encontrados {len(produtos_validados)} produtos para '{termo}'")
            return produtos_validados
        else:
            registrar_busca(
                nivel="api",
                termo=termo,
                sucesso=False,
                quantidade=0,
                detalhes=f"Erro {response.status_code} - {response.text[:100]}",
                tempo_execucao=time.time() - inicio,
                erro=f"HTTP {response.status_code}"
            )
            logger.error(f"❌ Erro Serper: {response.status_code} - {response.text[:100]}")
            return []
            
    except requests.exceptions.Timeout:
        registrar_busca(
            nivel="api",
            termo=termo,
            sucesso=False,
            quantidade=0,
            detalhes="Timeout na requisição",
            tempo_execucao=time.time() - inicio,
            erro="Timeout"
        )
        logger.error(f"❌ Timeout ao buscar '{termo}'")
        return []
    except Exception as e:
        registrar_busca(
            nivel="api",
            termo=termo,
            sucesso=False,
            quantidade=0,
            detalhes=f"Erro ao buscar '{termo}'",
            tempo_execucao=time.time() - inicio,
            erro=str(e)[:100]
        )
        logger.error(f"❌ Erro ao buscar '{termo}': {e}")
        return []

# ============================================================
# FUNÇÕES DE CACHE
# ============================================================
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

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'buscar_produtos_serper',
    'limpar_cache_serper',
    'obter_stats_cache_serper',
    'obter_stats_serper',
    'obter_requisicoes_restantes',
    'resetar_contador_serper',
    'LIMITE_DIARIO_SERPER',
    'obter_chave_serper'
]
def capturar_buscas_shopee_com_selenium_fallback() -> List[str]:
    """
    Tenta capturar buscas usando Selenium (fallback)
    """
    try:
        from modules.selenium_scraper import capturar_buscas_shopee_selenium, SELENIUM_DISPONIVEL
        
        if not SELENIUM_DISPONIVEL:
            logger.warning("Selenium não disponível")
            return []
        
        logger.info("🌐 Tentando capturar com Selenium...")
        termos = capturar_buscas_shopee_selenium()
        
        if termos:
            logger.info(f"✅ Selenium capturou {len(termos)} termos")
            return termos
        
        return []
        
    except ImportError:
        logger.warning("⚠️ Selenium não instalado. Use: pip install selenium webdriver-manager")
        return []
    except Exception as e:
        logger.error(f"❌ Erro no Selenium: {e}")
        return []
