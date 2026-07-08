# modules/selenium_client.py

import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def obter_url_selenium():
    """Obtém a URL do servidor Selenium dos Secrets"""
    try:
        url = st.secrets.get("SELENIUM_API_URL", "")
        if url:
            return url
        else:
            # Fallback para desenvolvimento
            return "https://selenium-scraper-emnc.onrender.com"
    except Exception as e:
        logger.error(f"Erro ao obter URL: {e}")
        return "https://selenium-scraper-emnc.onrender.com"

def verificar_status_selenium() -> dict:
    """Verifica se o servidor Selenium está online"""
    try:
        url = obter_url_selenium()
        response = requests.get(f"{url}/", timeout=10)
        
        if response.status_code == 200:
            return {"online": True, "dados": response.json(), "url": url}
        else:
            return {"online": False, "status": response.status_code, "url": url}
            
    except requests.exceptions.Timeout:
        return {"online": False, "error": "Timeout - servidor pode estar dormindo", "url": url}
    except Exception as e:
        return {"online": False, "error": str(e), "url": url}

def capturar_buscas_selenium() -> list:
    """Captura buscas da Shopee via API Selenium"""
    try:
        url = obter_url_selenium()
        response = requests.get(
            f"{url}/buscas",
            timeout=30
        )
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("success"):
                return dados.get("data", [])
        
        logger.error(f"Erro na API: {response.status_code}")
        return []
        
    except requests.exceptions.Timeout:
        logger.warning("Timeout na API Selenium (servidor pode estar dormindo)")
        return []
    except Exception as e:
        logger.error(f"Erro ao chamar API Selenium: {e}")
        return []
