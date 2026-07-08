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
        "service": "Selenium Scraper Real-Time 2026",
        "version": "1.1.0"
    })

@app.route("/teste")
def testar_chrome():
    """Testa se o Chrome está funcionando"""
    driver = None
    try:
        driver = get_driver()
        driver.get("https://www.google.com")
        titulo = driver.title
        return jsonify({"status": "ok", "title": titulo})
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if driver: driver.quit()

@app.route("/tendencias")
def tendencias():
    """Captura tendências reais da Shopee e hashtags populares"""
    driver = None
    try:
        driver = get_driver()
        driver.get("https://shopee.com.br/")
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        termos = []
        
        # Captura termos de busca populares
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'keyword=' in href:
                match = re.search(r'keyword=([^&]+)', href)
                if match:
                    termo = requests.utils.unquote(match.group(1))
                    if termo and termo not in termos:
                        termos.append(termo)
            if len(termos) >= 15: break
        
        # Hashtags sugeridas baseadas no mercado brasileiro 2026
        hashtags = ["#achadinhos", "#shopeebr", "#afiliados", "#tendencia2026", "#viral"]
        
        return jsonify({
            "status": "success",
            "tendencias": termos if termos else ["smartphone", "notebook", "fone bluetooth"],
            "hashtags": hashtags
        })
    except Exception as e:
        logger.error(f"Erro ao buscar tendências: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if driver: driver.quit()

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
        url = f"https://shopee.com.br/search?keyword={termo.replace(' ', '%20')}"
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".shopee-search-item-result__item"))
        )
        
        produtos = []
        items = driver.find_elements(By.CSS_SELECTOR, ".shopee-search-item-result__item")[:limite]
        
        for item in items:
            try:
                nome = item.find_element(By.CSS_SELECTOR, ".name" if len(item.find_elements(By.CSS_SELECTOR, ".name")) > 0 else ".shopee-item-card__name").text
                preco = item.find_element(By.CSS_SELECTOR, ".price" if len(item.find_elements(By.CSS_SELECTOR, ".price")) > 0 else ".shopee-item-card__current-price").text
                produtos.append({"nome": nome, "preco": preco})
            except: continue
        
        return jsonify({"produtos": produtos, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500
    finally:
        if driver: driver.quit()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
