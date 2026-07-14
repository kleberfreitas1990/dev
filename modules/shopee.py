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
from modules.logger import registrar_busca
from modules.selenium_client import capturar_buscas_selenium, verificar_status_selenium

logger = logging.getLogger(__name__)

# ============================================================
# ARQUIVO DE CACHE (NA RAIZ)
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
    "Tapete",
    "100 Pacotes de Figurinhas da Copa",
    "iPhone 17",
    "R36S Game Console",
    "Lembrancinha Dia dos Pais",
    "Caixa Organizadora",
    "Teclado Mecânico",
    "Chopp Gelado",
    "Caixa Cacau Show Branca",
    "Controle PS4",
    "Moto Elétrica",
    "Vestido",
    "Air Fryer 16L",
    "Bicicleta Elétrica",
    "Lingerie",
    "Penteadeira",
    "Tablet",
    "Figurinha Legend",
    "Armário Multiuso Organizador",
    "Bicicleta Spinning Ergométrica",
    "Body Bebê Reborn",
    "Micro Motor",
    "Balcão de Pia de Cozinha 160 cm",
    "Bateria Zetta 70Ah",
    "Bicicleta Infantil Aro 20",
    "Cabo Sill",
    "Bicicleta Aro 29 GT Print",
    "Bicicleta Camaleão GTA",
    "Bicicleta Infantil Aro 29"
]

# ============================================================
# FUNÇÃO PARA CAPTURAR BUSCAS DA SHOPEE
# ============================================================
def capturar_buscas_shopee(max_tentativas: int = 3) -> List[str]:
    """
    Captura buscas em alta da Shopee com múltiplas estratégias
    Prioridade: Selenium Real -> Raspagem Direta -> API Sugestões -> Fallback
    """
    inicio = time.time()
    termos = []
    
    # ESTRATÉGIA 0: Selenium Real (Servidor Render)
    try:
        status = verificar_status_selenium()
        if status.get("online"):
            logger.info("📡 Usando Selenium Real para capturar buscas...")
            termos_selenium = capturar_buscas_selenium()
            if termos_selenium:
                termos = validar_lista_termos(termos_selenium)
                if len(termos) >= 5:
                    registrar_busca(
                        nivel="raspagem",
                        termo="shopee_selenium",
                        sucesso=True,
                        quantidade=len(termos),
                        detalhes=f"Capturados {len(termos)} termos via Selenium Real",
                        tempo_execucao=time.time() - inicio
                    )
                    return termos[:20]
    except Exception as e:
        logger.warning(f"Erro ao usar Selenium Real: {e}")

    # ESTRATÉGIA 1: Capturar do rodapé da página (Raspagem Direta)
    if len(termos) < 5:
        for tentativa in range(max_tentativas):
            try:
                user_agent = USER_AGENTS[tentativa % len(USER_AGENTS)]
                url = "https://shopee.com.br"
                headers = {"User-Agent": user_agent}
                
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
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
                        registrar_busca(
                            nivel="raspagem",
                            termo="shopee_footer",
                            sucesso=True,
                            quantidade=len(termos),
                            detalhes=f"Capturados {len(termos)} termos do rodapé",
                            tempo_execucao=time.time() - inicio
                        )
                        return termos[:20]
            except Exception as e:
                logger.warning(f"Erro na raspagem direta (tentativa {tentativa+1}): {e}")
                time.sleep(1)
    
    # ESTRATÉGIA 2: API de sugestões
    if len(termos) < 5:
        try:
            url = "https://shopee.com.br/api/v4/search/search_suggestions"
            params = {"search": ""}
            response = requests.get(url, params=params, headers={"User-Agent": USER_AGENTS[0]}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    for item in data["items"]:
                        termo = item.get("keyword", "")
                        termo_validado = validar_termo_busca(termo)
                        if termo_validado and termo_validado not in termos:
                            termos.append(termo_validado)
                
                if len(termos) > 0:
                    registrar_busca(
                        nivel="raspagem",
                        termo="shopee_api",
                        sucesso=True,
                        quantidade=len(termos),
                        detalhes=f"Capturados {len(termos)} termos via API",
                        tempo_execucao=time.time() - inicio
                    )
                    return termos[:20]
        except Exception as e:
            logger.error(f"Erro na API: {e}")
    
    # ESTRATÉGIA 3: FALLBACK (LISTA ESTÁTICA)
    if len(termos) < 5:
        logger.info("Usando fallback com termos reais da Shopee")
        termos_fallback = validar_lista_termos(TERMOS_REAIS_SHOPEE)
        for termo in termos_fallback:
            if termo not in termos:
                termos.append(termo)
        
        registrar_busca(
            nivel="raspagem",
            termo="shopee_fallback",
            sucesso=True if len(termos) > 0 else False,
            quantidade=len(termos),
            detalhes=f"Usando fallback - {len(termos)} termos",
            tempo_execucao=time.time() - inicio
        )
    
    # SE FALHOU TUDO
    if not termos:
        registrar_busca(
            nivel="raspagem",
            termo="shopee_trends",
            sucesso=False,
            quantidade=0,
            detalhes="Todas as estratégias falharam",
            tempo_execucao=time.time() - inicio,
            erro="Nenhum termo encontrado"
        )
    
    return termos[:20]

def capturar_buscas_shopee_com_cache(ignorar_cache: bool = False) -> List[str]:
    """
    Captura buscas com cache diário
    
    Args:
        ignorar_cache (bool): Se True, força nova busca
    """
    hoje = datetime.now().date().isoformat()
    
    if not ignorar_cache and os.path.exists(ARQUIVO_SHOPEE_CACHE):
        try:
            with open(ARQUIVO_SHOPEE_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if validar_cache_dados(dados, "termos"):
                    data_cache = dados.get("data")
                    if data_cache == hoje:
                        logger.info(f"Cache da Shopee usado (hoje)")
                        return dados.get("termos", [])
        except:
            pass
    
    logger.info("Buscando novos dados da Shopee...")
    termos = capturar_buscas_shopee()
    termos_validados = validar_lista_termos(termos)
    
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
        except:
            pass
    
    return termos_validados

def limpar_cache_shopee():
    if os.path.exists(ARQUIVO_SHOPEE_CACHE):
        try:
            os.remove(ARQUIVO_SHOPEE_CACHE)
            return True
        except:
            pass
    return False

def obter_stats_cache_shopee() -> dict:
    stats = {"existe": False, "data": None, "total_termos": 0, "tamanho_kb": 0, "valido": False}
    if os.path.exists(ARQUIVO_SHOPEE_CACHE):
        stats["existe"] = True
        try:
            with open(ARQUIVO_SHOPEE_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                stats["data"] = dados.get("data")
                stats["total_termos"] = len(dados.get("termos", []))
                stats["valido"] = validar_cache_dados(dados, "termos")
                stats["tamanho_kb"] = round(os.path.getsize(ARQUIVO_SHOPEE_CACHE) / 1024, 2)
        except:
            pass
    return stats

# ============================================================
# FUNÇÃO FALLBACK PARA SELENIUM (DESATIVADA)
# ============================================================
def capturar_buscas_shopee_com_selenium_fallback() -> List[str]:
    """
    Tenta capturar buscas usando Selenium - DESATIVADO
    Selenium não funciona no Streamlit Cloud
    """
    logger.warning("⚠️ Selenium desativado no Streamlit Cloud")
    return []

__all__ = [
    'capturar_buscas_shopee',
    'capturar_buscas_shopee_com_cache',
    'limpar_cache_shopee',
    'obter_stats_cache_shopee',
    'TERMOS_REAIS_SHOPEE',
    'capturar_buscas_shopee_com_selenium_fallback'
]
