"""
Módulo de Scraping com Selenium
Captura dados de sites que usam JavaScript
"""

import time
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

# Tentar importar Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    from bs4 import BeautifulSoup
    import requests
    SELENIUM_DISPONIVEL = True
    logger.info("✅ Selenium disponível")
except ImportError:
    SELENIUM_DISPONIVEL = False
    logger.warning("⚠️ Selenium não instalado. Use: pip install selenium webdriver-manager beautifulsoup4")

from modules.validation import validar_termo_busca
from modules.logger import registrar_busca


def capturar_com_selenium(url: str, timeout: int = 15) -> str:
    """
    Captura o conteúdo de uma página usando Selenium
    """
    if not SELENIUM_DISPONIVEL:
        logger.warning("Selenium não disponível")
        return None
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Rola a página para carregar tudo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        html = driver.page_source
        
        logger.info(f"Selenium capturou {len(html)} caracteres de {url}")
        return html
        
    except Exception as e:
        logger.error(f"Erro no Selenium: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()


def capturar_buscas_shopee_selenium() -> List[str]:
    """
    Captura buscas da Shopee usando Selenium
    """
    if not SELENIUM_DISPONIVEL:
        return []
    
    inicio = time.time()
    
    try:
        html = capturar_com_selenium("https://shopee.com.br", timeout=15)
        
        if not html:
            registrar_busca(
                nivel="selenium",
                termo="shopee_trends",
                sucesso=False,
                quantidade=0,
                detalhes="Selenium não retornou HTML",
                tempo_execucao=time.time() - inicio,
                erro="HTML vazio"
            )
            return []
        
        termos = []
        
        # Busca padrões de keyword no HTML
        padroes = [
            r'/search\?keyword=([^"&\s]+)',
            r'keyword":"([^"]+)"',
            r'keyword=([^&"\s]+)'
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, html)
            for match in matches:
                termo = match.replace('+', ' ').replace('%20', ' ')
                termo_validado = validar_termo_busca(termo)
                if termo_validado and termo_validado not in termos:
                    termos.append(termo_validado)
        
        if len(termos) < 5:
            # Tenta extrair da estrutura da página
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if 'keyword' in href:
                    match = re.search(r'keyword=([^&]+)', href)
                    if match:
                        termo = requests.utils.unquote(match.group(1))
                        termo_validado = validar_termo_busca(termo)
                        if termo_validado and termo_validado not in termos:
                            termos.append(termo_validado)
        
        registrar_busca(
            nivel="selenium",
            termo="shopee_trends",
            sucesso=True if len(termos) > 0 else False,
            quantidade=len(termos),
            detalhes=f"Capturados {len(termos)} termos via Selenium",
            tempo_execucao=time.time() - inicio
        )
        
        return termos[:20]
        
    except Exception as e:
        registrar_busca(
            nivel="selenium",
            termo="shopee_trends",
            sucesso=False,
            quantidade=0,
            detalhes=f"Erro: {str(e)[:50]}",
            tempo_execucao=time.time() - inicio,
            erro=str(e)[:100]
        )
        logger.error(f"Erro ao capturar Shopee com Selenium: {e}")
        return []


def buscar_produtos_shopee_selenium(termo: str, limite: int = 5) -> List[Dict]:
    """
    Busca produtos específicos na Shopee usando Selenium
    """
    if not SELENIUM_DISPONIVEL:
        return []
    
    inicio = time.time()
    
    try:
        url = f"https://shopee.com.br/search?keyword={termo.replace(' ', '%20')}"
        html = capturar_com_selenium(url, timeout=15)
        
        if not html:
            return []
        
        produtos = []
        
        # Tenta extrair produtos do HTML
        # Padrões de produtos na Shopee
        nomes = re.findall(r'"name":"([^"]+)"', html)
        precos = re.findall(r'"price":(\d+)', html)
        lojas = re.findall(r'"shopname":"([^"]+)"', html)
        
        for i, nome in enumerate(nomes[:limite]):
            preco = precos[i] if i < len(precos) else "0"
            loja = lojas[i] if i < len(lojas) else "Shopee"
            try:
                preco_real = float(preco) / 100000
            except:
                preco_real = 0
            
            produtos.append({
                "nome": nome,
                "preco": f"R$ {preco_real:.2f}",
                "loja": loja,
                "link": f"https://shopee.com.br/search?keyword={termo.replace(' ', '%20')}"
            })
        
        registrar_busca(
            nivel="selenium",
            termo=termo,
            sucesso=True if len(produtos) > 0 else False,
            quantidade=len(produtos),
            detalhes=f"Encontrados {len(produtos)} produtos na Shopee",
            tempo_execucao=time.time() - inicio
        )
        
        return produtos
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos com Selenium: {e}")
        return []


__all__ = [
    'capturar_com_selenium',
    'capturar_buscas_shopee_selenium',
    'buscar_produtos_shopee_selenium',
    'SELENIUM_DISPONIVEL'
]
