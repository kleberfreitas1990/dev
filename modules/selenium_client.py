"""
Cliente para consumir a API do Selenium no Render
"""

import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

# ============================================================
# FUNÇÕES PARA OBTER URL
# ============================================================
def obter_url_selenium() -> str:
    """
    Obtém a URL do servidor Selenium dos Secrets
    """
    try:
        url = st.secrets.get("SELENIUM_API_URL", "")
        if url:
            logger.info(f"URL do Selenium obtida dos Secrets: {url}")
            return url
        else:
            # Fallback para desenvolvimento
            logger.warning("SELENIUM_API_URL não encontrado nos Secrets, usando fallback")
            return "https://selenium-scraper-emnc.onrender.com"
    except Exception as e:
        logger.error(f"Erro ao obter URL: {e}")
        return "https://selenium-scraper-emnc.onrender.com"

# ============================================================
# FUNÇÕES DE STATUS
# ============================================================
def verificar_status_selenium() -> dict:
    """
    Verifica se o servidor Selenium está online
    """
    try:
        url = obter_url_selenium()
        response = requests.get(f"{url}/", timeout=10)
        
        if response.status_code == 200:
            return {
                "online": True, 
                "dados": response.json(), 
                "url": url
            }
        else:
            return {
                "online": False, 
                "status": response.status_code, 
                "url": url
            }
            
    except requests.exceptions.Timeout:
        return {
            "online": False, 
            "error": "Timeout - servidor pode estar dormindo (Render free tier)", 
            "url": url
        }
    except requests.exceptions.ConnectionError:
        return {
            "online": False, 
            "error": "Erro de conexão - servidor pode estar offline", 
            "url": url
        }
    except Exception as e:
        return {
            "online": False, 
            "error": str(e), 
            "url": url
        }

# ============================================================
# FUNÇÕES DE CAPTURA
# ============================================================
def capturar_buscas_selenium() -> list:
    """
    Captura buscas da Shopee via API Selenium
    """
    try:
        url = obter_url_selenium()
        logger.info(f"Chamando API Selenium em: {url}/tendencias")
        
        response = requests.get(
            f"{url}/tendencias",
            timeout=35  # Tempo extra para o Render acordar
        )
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("success"):
                termos = dados.get("tendencias", [])
                logger.info(f"✅ Capturados {len(termos)} termos via Selenium")
                return termos
            else:
                logger.error(f"Erro na API: {dados.get('error', 'Erro desconhecido')}")
                return []
        else:
            logger.error(f"Erro na API: Status {response.status_code}")
            return []
        
    except requests.exceptions.Timeout:
        logger.warning("⏰ Timeout na API Selenium (servidor pode estar dormindo)")
        return []
    except requests.exceptions.ConnectionError:
        logger.warning("🔌 Erro de conexão com o servidor Selenium")
        return []
    except Exception as e:
        logger.error(f"❌ Erro ao chamar API Selenium: {e}")
        return []

def capturar_tendencias_selenium() -> dict:
    """
    Captura tendências da Shopee via API Selenium
    """
    try:
        url = obter_url_selenium()
        response = requests.get(
            f"{url}/tendencias",
            timeout=35
        )
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("success"):
                return dados.get("data", {})
        
        return {}
        
    except Exception as e:
        logger.error(f"Erro ao capturar tendências: {e}")
        return {}

def buscar_produtos_selenium(termo: str, limite: int = 5) -> list:
    """
    Busca produtos para um termo via API Selenium
    """
    try:
        url = obter_url_selenium()
        response = requests.post(
            f"{url}/produtos",
            json={"termo": termo, "limite": limite},
            timeout=35
        )
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("success"):
                return dados.get("data", [])
        
        return []
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {e}")
        return []

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'obter_url_selenium',
    'verificar_status_selenium',
    'capturar_buscas_selenium',
    'capturar_tendencias_selenium',
    'buscar_produtos_selenium'
]
