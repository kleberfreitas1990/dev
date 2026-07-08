import logging
import time
import re
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def criar_driver():
    """Cria e configura o driver do Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def capturar_buscas_shopee() -> List[str]:
    """
    Captura buscas em alta da Shopee usando Selenium
    """
    driver = None
    termos = []
    
    try:
        driver = criar_driver()
        driver.get("https://shopee.com.br")
        
        # Espera a página carregar
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Rola a página
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        html = driver.page_source
        
        # Extrai termos de busca
        padroes = [
            r'/search\?keyword=([^"&\s]+)',
            r'keyword":"([^"]+)"',
            r'keyword=([^&"\s]+)'
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, html)
            for match in matches:
                termo = match.replace('+', ' ').replace('%20', ' ')
                if termo and len(termo) > 2 and termo not in termos:
                    termos.append(termo)
        
        return termos[:20]
        
    except Exception as e:
        logger.error(f"Erro no Selenium: {e}")
        return []
        
    finally:
        if driver:
            driver.quit()

def buscar_produtos_shopee(termo: str, limite: int = 5) -> List[Dict]:
    """
    Busca produtos na Shopee para um termo específico
    """
    driver = None
    produtos = []
    
    try:
        driver = criar_driver()
        url = f"https://shopee.com.br/search?keyword={termo.replace(' ', '%20')}"
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(3)
        html = driver.page_source
        
        # Extrai produtos
        nomes = re.findall(r'"name":"([^"]+)"', html)
        precos = re.findall(r'"price":(\d+)', html)
        
        for i, nome in enumerate(nomes[:limite]):
            preco = precos[i] if i < len(precos) else "0"
            try:
                preco_real = float(preco) / 100000
            except:
                preco_real = 0
            
            produtos.append({
                "nome": nome,
                "preco": f"R$ {preco_real:.2f}",
                "loja": "Shopee",
                "link": f"https://shopee.com.br/search?keyword={termo.replace(' ', '%20')}"
            })
        
        return produtos
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {e}")
        return []
        
    finally:
        if driver:
            driver.quit()

def capturar_tendencias_shopee() -> Dict:
    """
    Captura tendências completas da Shopee
    """
    driver = None
    
    try:
        driver = criar_driver()
        driver.get("https://shopee.com.br")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        html = driver.page_source
        
        # Extrai termos
        termos = []
        padroes = [
            r'/search\?keyword=([^"&\s]+)',
            r'keyword":"([^"]+)"'
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, html)
            for match in matches:
                termo = match.replace('+', ' ').replace('%20', ' ')
                if termo and len(termo) > 2 and termo not in termos:
                    termos.append(termo)
        
        # Extrai categorias populares
        categorias = re.findall(r'"categoryName":"([^"]+)"', html)
        categorias = list(set(categorias))[:5]
        
        return {
            "termos": termos[:20],
            "categorias": categorias,
            "total_termos": len(termos)
        }
        
    except Exception as e:
        logger.error(f"Erro ao capturar tendências: {e}")
        return {"termos": [], "categorias": [], "total_termos": 0}
        
    finally:
        if driver:
            driver.quit()
