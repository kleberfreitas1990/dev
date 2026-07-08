"""
Cliente para consumir a API do Selenium no Render
"""

import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

# URL do seu servidor no Render (SUBSTITUA PELA SUA URL)
# Exemplo: https://selenium-scraper.onrender.com
SELENIUM_API_URL = st.secrets.get("SELENIUM_API_URL", "https://seu-servidor.onrender.com")

def capturar_buscas_selenium() -> list:
    """
    Captura buscas da Shopee via API Selenium
    """
    try:
        response = requests.get(
            f"{SELENIUM_API_URL}/buscas",
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

def capturar_tendencias_selenium() -> dict:
    """
    Captura tendências da Shopee via API Selenium
    """
    try:
        response = requests.get(
            f"{SELENIUM_API_URL}/tendencias",
            timeout=30
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
        response = requests.post(
            f"{SELENIUM_API_URL}/produtos",
            json={"termo": termo, "limite": limite},
            timeout=30
        )
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("success"):
                return dados.get("data", [])
        
        return []
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {e}")
        return []

def verificar_status_selenium() -> dict:
    """
    Verifica se o servidor Selenium está online
    """
    try:
        response = requests.get(
            f"{SELENIUM_API_URL}/",
            timeout=10
        )
        
        if response.status_code == 200:
            return {"online": True, "dados": response.json()}
        
        return {"online": False, "status": response.status_code}
        
    except Exception as e:
        return {"online": False, "error": str(e)}
