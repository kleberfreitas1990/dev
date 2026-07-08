"""
Módulo de Scraping com Selenium - DESATIVADO
Selenium não funciona no Streamlit Cloud sem configuração adicional
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Selenium desativado no Streamlit Cloud
SELENIUM_DISPONIVEL = False

def capturar_com_selenium(url: str, timeout: int = 15) -> str:
    """Selenium desativado"""
    logger.warning("Selenium desativado no Streamlit Cloud")
    return None

def capturar_buscas_shopee_selenium() -> List[str]:
    """Selenium desativado"""
    logger.warning("Selenium desativado no Streamlit Cloud")
    return []

def buscar_produtos_shopee_selenium(termo: str, limite: int = 5) -> List[Dict]:
    """Selenium desativado"""
    logger.warning("Selenium desativado no Streamlit Cloud")
    return []

__all__ = [
    'capturar_com_selenium',
    'capturar_buscas_shopee_selenium',
    'buscar_produtos_shopee_selenium',
    'SELENIUM_DISPONIVEL'
]
