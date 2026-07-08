from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def criar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Selenium Scraper API",
        "endpoints": {
            "/buscas": "GET - Retorna termos de busca da Shopee",
            "/tendencias": "GET - Retorna tendências completas",
            "/produtos": "POST - Busca produtos por termo",
            "/teste": "GET - Testa se o Chrome está funcionando"
        }
    })

@app.route('/teste', methods=['GET'])
def teste():
    """Endpoint para testar se o Chrome está funcionando"""
    driver = None
    try:
        driver = criar_driver()
        driver.get("https://www.google.com")
        titulo = driver.title
        return jsonify({
            "success": True,
            "mensagem": "Chrome funcionando!",
            "titulo": titulo
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if driver:
            driver.quit()

@app.route('/buscas', methods=['GET'])
def get_buscas():
    """Captura os termos de busca em alta da Shopee"""
    driver = None
    termos = []
    
    try:
        logger.info("Iniciando captura de buscas da Shopee...")
        driver = criar_driver()
        driver.get("https://shopee.com.br")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
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
                    if len(termos) >= 20:
                        break
            if len(termos) >= 20:
                break
        
        logger.info(f"Capturados {len(termos)} termos")
        
        return jsonify({
            "success": True,
            "data": termos,
            "total": len(termos),
            "fonte": "selenium"
        })
        
    except Exception as e:
        logger.error(f"Erro na captura: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
    finally:
        if driver:
            driver.quit()

@app.route('/tendencias', methods=['GET'])
def get_tendencias():
    """Captura tendências completas da Shopee"""
    driver = None
    
    try:
        logger.info("Capturando tendências da Shopee...")
        driver = criar_driver()
        driver.get("https://shopee.com.br")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        html = driver.page_source
        
        termos = []
        matches = re.findall(r'/search\?keyword=([^"&\s]+)', html)
        for match in matches:
            termo = match.replace('+', ' ').replace('%20', ' ')
            if termo and len(termo) > 2 and termo not in termos:
                termos.append(termo)
        
        categorias = re.findall(r'"categoryName":"([^"]+)"', html)
        categorias = list(set(categorias))[:5]
        
        return jsonify({
            "success": True,
            "data": {
                "termos": termos[:20],
                "categorias": categorias,
                "total_termos": len(termos)
            },
            "fonte": "selenium"
        })
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
    finally:
        if driver:
            driver.quit()

@app.route('/produtos', methods=['POST'])
def get_produtos():
    """Busca produtos para um termo específico"""
    driver = None
    
    try:
        data = request.get_json()
        termo = data.get('termo', '')
        limite = data.get('limite', 5)
        
        if not termo:
            return jsonify({
                "success": False,
                "error": "Termo não informado"
            }), 400
        
        logger.info(f"Buscando produtos para '{termo}'...")
        driver = criar_driver()
        
        url = f"https://shopee.com.br/search?keyword={termo.replace(' ', '%20')}"
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(3)
        html = driver.page_source
        
        produtos = []
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
        
        return jsonify({
            "success": True,
            "data": produtos,
            "total": len(produtos),
            "termo": termo,
            "fonte": "selenium"
        })
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
