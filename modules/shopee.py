import streamlit as st
import requests
import re
import json
import os
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Optional

# Importa validação
from modules.validation import (
    validar_termo_busca,
    validar_lista_termos,
    validar_cache_dados,
    sanitizar_json
)

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================
logger = logging.getLogger(__name__)

# ============================================================
# ARQUIVO DE CACHE
# ============================================================
ARQUIVO_SHOPEE_CACHE = "shopee_trends_cache.json"

# ============================================================
# USER AGENTS ROTATIVOS
# ============================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
]

# ============================================================
# TERMOS REAIS DA SHOPEE (FALLBACK)
# ============================================================
TERMOS_REAIS_SHOPEE = [
    "controle pc", "sapateira", "lixeira cozinha", 
    "ar condicionado portátil", "garrafa térmica", 
    "sacola personalizada", "caixa organizadora", 
    "camisa brasil", "tênis", "chopeira", 
    "relógio", "tablet", "organizador", "lingerie", 
    "espelho", "vestido", "roupas feminina", 
    "figurinha legend", "joia cobre", 
    "kenner feminina", "moto infantil", "kit cadeira",
    "ar condicionado elgin", "kit loreal"
]

# ============================================================
# FUNÇÃO PARA CAPTURAR BUSCAS DA SHOPEE (OTIMIZADA)
# ============================================================
def capturar_buscas_shopee(max_tentativas: int = 3) -> List[str]:
    """
    Captura buscas em alta da Shopee com múltiplas estratégias e validação
    
    Args:
        max_tentativas (int): Número máximo de tentativas
        
    Returns:
        List[str]: Lista de termos válidos
    """
    termos = []
    
    # ESTRATÉGIA 1: Capturar do rodapé da página
    for tentativa in range(max_tentativas):
        try:
            user_agent = USER_AGENTS[tentativa % len(USER_AGENTS)]
            
            url = "https://shopee.com.br"
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
            
            # Timeout progressivo
            timeout = 10 + (tentativa * 2)
            
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Busca em links com keyword
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/search?keyword=' in href:
                        match = re.search(r'keyword=([^&]+)', href)
                        if match:
                            termo = requests.utils.unquote(match.group(1))
                            termo_validado = validar_termo_busca(termo)
                            if termo_validado and termo_validado not in termos:
                                termos.append(termo_validado)
                
                if len(termos) >= 10:
                    logger.info(f"Capturados {len(termos)} termos via rodapé (tentativa {tentativa+1})")
                    return termos[:20]
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na tentativa {tentativa+1}")
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro na tentativa {tentativa+1}: {e}")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            time.sleep(1)
    
    # ESTRATÉGIA 2: API de sugestões
    if len(termos) < 5:
        try:
            url = "https://shopee.com.br/api/v4/search/search_suggestions"
            params = {"search": ""}
            headers = {
                "User-Agent": USER_AGENTS[0],
                "Referer": "https://shopee.com.br/"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "items" in data:
                    for item in data["items"]:
                        termo = item.get("keyword", "")
                        termo_validado = validar_termo_busca(termo)
                        if termo_validado and termo_validado not in termos:
                            termos.append(termo_validado)
                
                logger.info(f"Capturados {len(termos)} termos via API")
                return termos[:20]
        except Exception as e:
            logger.error(f"Erro na API: {e}")
    
    # ESTRATÉGIA 3: FALLBACK - Termos reais do rodapé
    if len(termos) < 5:
        logger.info("Usando fallback com termos reais da Shopee")
        termos_fallback = validar_lista_termos(TERMOS_REAIS_SHOPEE)
        for termo in termos_fallback:
            if termo not in termos:
                termos.append(termo)
    
    return termos[:20]

def capturar_buscas_shopee_com_cache(ignorar_cache: bool = False) -> List[str]:
    """
    Captura buscas com cache diário e validação
    
    Args:
        ignorar_cache (bool): Se True, força nova busca
        
    Returns:
        List[str]: Lista de termos válidos
    """
    
    hoje = datetime.now().date().isoformat()
    
    # Tenta carregar do cache (se não for ignorado)
    if not ignorar_cache and os.path.exists(ARQUIVO_SHOPEE_CACHE):
        try:
            with open(ARQUIVO_SHOPEE_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
                # Valida dados do cache
                if validar_cache_dados(dados, "termos"):
                    data_cache = dados.get("data")
                    if data_cache == hoje:
                        logger.info(f"Cache da Shopee usado (hoje): {len(dados.get('termos', []))} termos")
                        return dados.get("termos", [])
                    else:
                        logger.info(f"Cache da Shopee de {data_cache} (diferente de hoje)")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Erro ao ler cache: {e}")
    
    # Se não tem cache válido, busca novos dados
    logger.info("Buscando novos dados da Shopee...")
    termos = capturar_buscas_shopee()
    
    # Valida os termos capturados
    termos_validados = validar_lista_termos(termos)
    
    # Salva no cache (apenas se tiver termos válidos)
    if termos_validados:
        try:
            with open(ARQUIVO_SHOPEE_CACHE, 'w', encoding='utf-8') as f:
                json.dump({
                    "data": hoje,
                    "termos": termos_validados,
                    "timestamp": datetime.now().isoformat(),
                    "total": len(termos_validados)
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Cache da Shopee atualizado com {len(termos_validados)} termos")
        except IOError as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    return termos_validados

def limpar_cache_shopee():
    """Limpa o cache da Shopee"""
    if os.path.exists(ARQUIVO_SHOPEE_CACHE):
        try:
            os.remove(ARQUIVO_SHOPEE_CACHE)
            logger.info("Cache da Shopee removido")
            return True
        except IOError as e:
            logger.error(f"Erro ao remover cache: {e}")
            return False
    return True

def obter_stats_cache_shopee() -> dict:
    """
    Obtém estatísticas do cache da Shopee
    
    Returns:
        dict: Estatísticas do cache
    """
    stats = {
        "existe": False,
        "data": None,
        "total_termos": 0,
        "tamanho_kb": 0,
        "valido": False
    }
    
    if os.path.exists(ARQUIVO_SHOPEE_CACHE):
        stats["existe"] = True
        try:
            with open(ARQUIVO_SHOPEE_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                stats["data"] = dados.get("data")
                stats["total_termos"] = len(dados.get("termos", []))
                stats["valido"] = validar_cache_dados(dados, "termos")
                
                # Tamanho do arquivo
                stats["tamanho_kb"] = round(os.path.getsize(ARQUIVO_SHOPEE_CACHE) / 1024, 2)
        except Exception as e:
            logger.error(f"Erro ao ler estatísticas: {e}")
    
    return stats

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'capturar_buscas_shopee',
    'capturar_buscas_shopee_com_cache',
    'limpar_cache_shopee',
    'obter_stats_cache_shopee',
    'TERMOS_REAIS_SHOPEE'
]
