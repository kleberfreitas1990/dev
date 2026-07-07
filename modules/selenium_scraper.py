"""
Módulo de Scraping com Selenium
Captura dados de sites que usam JavaScript
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def capturar_com_selenium(url: str, timeout: int = 10) -> str:
    """
    Captura o conteúdo de uma página usando Selenium
    
    Args:
        url (str): URL da página
        timeout (int): Tempo máximo de espera
    
    Returns:
        str: HTML da página ou None se falhar
    """
    driver = None
    try:
        # Configuração do Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Roda sem interface gráfica
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Inicia o driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Acessa a URL
        driver.get(url)
        
        # Espera a página carregar
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Pega o HTML
        html = driver.page_source
        
        logger.info(f"Selenium capturou {len(html)} caracteres de {url}")
        return html
        
    except Exception as e:
        logger.error(f"Erro no Selenium: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

def capturar_buscas_shopee_selenium() -> list:
    """
    Captura buscas da Shopee usando Selenium
    """
    try:
        html = capturar_com_selenium("https://shopee.com.br", timeout=15)
        
        if not html:
            return []
        
        # Extrai os termos do HTML
        import re
        from modules.validation import validar_termo_busca
        
        termos = []
        padrao = r'/search\?keyword=([^"&\s]+)'
        matches = re.findall(padrao, html)
        
        for match in matches[:20]:
            termo = match.replace('+', ' ').replace('%20', ' ')
            termo_validado = validar_termo_busca(termo)
            if termo_validado and termo_validado not in termos:
                termos.append(termo_validado)
        
        return termos[:20]
        
    except Exception as e:
        logger.error(f"Erro ao capturar Shopee com Selenium: {e}")
        return []

__all__ = [
    'capturar_com_selenium',
    'capturar_buscas_shopee_selenium'
]
