from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask_cors import CORS
from bs4 import BeautifulSoup
import os
import time
import logging
import re
import requests.utils

app = Flask(__name__)
CORS(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_driver():
    """Cria driver do Chrome/Chromium com configurações otimizadas"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Usar Chromium
    chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    options.binary_location = chrome_bin
    
    driver = webdriver.Chrome(
        options=options,
        service=webdriver.chrome.service.Service(
            os.environ.get("CHROME_DRIVER", "/usr/bin/chromedriver")
        )
    )
    return driver

@app.route("/")
def index():
    """Status do servidor"""
    return jsonify({
        "status": "online",
        "service": "Selenium Scraper",
        "version": "1.0.2",
        "chrome_bin": os.environ.get("CHROME_BIN", "chromium"),
        "endpoints": [
            "/",
            "/teste",
            "/produtos (POST)",
            "/tendencias",
            "/buscas"
        ]
    })

@app.route("/teste")
def testar_chrome():
    """Testa se o Chrome está funcionando"""
    driver = None
    try:
        driver = get_driver()
        driver.get("https://www.google.com")
        titulo = driver.title
        return jsonify({
            "status": "ok",
            "message": "Chrome funcionando perfeitamente",
            "title": titulo
        })
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        if driver:
            driver.quit()

@app.route("/produtos", methods=["POST"])
def buscar_produtos():
    """Busca produtos na Shopee"""
    dados = request.json
    termo = dados.get("termo", "")
    limite = dados.get("limite", 10)
    
    if not termo:
        return jsonify({"error": "Termo de busca não fornecido"}), 400
    
    driver = None
    try:
        driver = get_driver()
        url = f"https://shopee.com.br/search?keyword={termo.replace(" ", "%20")}"
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".shopee-search-item-result__item"))
        )
        
        produtos = []
        items = driver.find_elements(By.CSS_SELECTOR, ".shopee-search-item-result__item")[:limite]
        
        for item in items:
            try:
                nome = item.find_element(By.CSS_SELECTOR, ".name").text
                preco = item.find_element(By.CSS_SELECTOR, ".price").text
                loja = item.find_element(By.CSS_SELECTOR, ".shop-name").text
                
                try:
                    img = item.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                except:
                    img = ""
                
                produtos.append({
                    "nome": nome,
                    "preco": preco,
                    "loja": loja,
                    "imagem": img,
                    "url": url
                })
            except Exception as e:
                logger.warning(f"Erro ao extrair item: {e}")
                continue
        
        return jsonify({
            "produtos": produtos,
            "total": len(produtos),
            "termo": termo,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500
    finally:
        if driver:
            driver.quit()

@app.route("/tendencias")
def tendencias():
    """Captura tendências da Shopee (termos de busca populares e categorias)"""
    driver = None
    try:
        driver = get_driver()
        driver.get("https://shopee.com.br/")
        time.sleep(3) # Espera a página carregar completamente
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        tendencias_encontradas = []
        
        # Tenta capturar termos de busca populares (ex: do rodapé ou seções de "Mais Buscados")
        # Procurar por links que contenham 'keyword=' no href
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'keyword=' in href:
                match = re.search(r'keyword=([^&]+)', href)
                if match:
                    termo = requests.utils.unquote(match.group(1))
                    if termo and termo not in tendencias_encontradas:
                        tendencias_encontradas.append(termo)
            if len(tendencias_encontradas) >= 20: # Limita para não pegar demais
                break

        # Tenta capturar categorias em destaque (se houver um seletor específico)
        # Exemplo: elementos com a classe 'category-card' ou similar
        categorias_elementos = soup.find_all(class_=re.compile(r'category-card|home-category-list__category-card'))
        for elem in categorias_elementos:
            nome_categoria = elem.get_text(strip=True)
            if nome_categoria and nome_categoria not in tendencias_encontradas:
                tendencias_encontradas.append(nome_categoria)
            if len(tendencias_encontradas) >= 20: # Limita para não pegar demais
                break

        return jsonify({
            'tendencias': tendencias_encontradas if tendencias_encontradas else ['smartphone', 'notebook', 'fone bluetooth'],
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Erro ao buscar tendências: {e}")
        return jsonify({
            'tendencias': ['smartphone', 'notebook', 'fone bluetooth'], # Fallback
            'status': 'error',
            'message': str(e)
        })
    finally:
        if driver:
            driver.quit()

@app.route("/buscas")
def buscas_populares():
    """Retorna termos de busca populares (agora dinâmico via scraping da Shopee)"""
    driver = None
    try:
        driver = get_driver()
        driver.get("https://shopee.com.br/")
        time.sleep(3) # Espera a página carregar

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        termos_populares = []

        # Procurar por elementos que representam buscas populares
        # Exemplo: elementos com a classe 'shopee-searchbar__hot-search-item' ou links com 'keyword='
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'keyword=' in href:
                match = re.search(r'keyword=([^&]+)', href)
                if match:
                    termo = requests.utils.unquote(match.group(1))
                    if termo and termo not in termos_populares:
                        termos_populares.append(termo)
            if len(termos_populares) >= 20: # Limita para não pegar demais
                break

        # Tenta encontrar termos em seções específicas, se houver
        # Ex: divs com títulos de 
