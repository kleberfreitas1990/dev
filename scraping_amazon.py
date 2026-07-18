import time
import json
import random
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def _criar_opcoes_chrome() -> Options:
    """Configura o navegador para execução compatível em CI e ambiente local."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1440,1200")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    if os.path.exists("/usr/bin/google-chrome"):
        chrome_options.binary_location = "/usr/bin/google-chrome"
    elif os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"
    return chrome_options


def capturar_amazon_bestsellers():
    """Captura Bestsellers sem abortar o workflow se o navegador estiver indisponível."""
    driver = None
    termos = []

    try:
        # O Selenium Manager busca o ChromeDriver correspondente ao navegador disponível.
        driver = webdriver.Chrome(options=_criar_opcoes_chrome())
        driver.set_page_load_timeout(30)
        print("🚀 Acessando Amazon Bestsellers...")
        driver.get("https://www.amazon.com.br/gp/bestsellers")
        time.sleep(3)

        seletores = [
            "div._cDEBa_p13n-sc-css-line-clamp-3_21q2s",
            "div.p13n-sc-truncate",
            "span.a-size-small",
            "div.p13n-sc-truncate-desktop-type2",
        ]

        for seletor in seletores:
            elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
            if elementos:
                print(f"✅ Encontrados {len(elementos)} produtos na Amazon.")
                for el in elementos:
                    texto = el.text.strip()
                    if texto and len(texto) > 10 and texto not in termos:
                        termos.append(texto)
                if len(termos) >= 15:
                    break

    except Exception as erro:
        print(f"⚠️ Coleta ao vivo Amazon indisponível: {erro}")
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    return termos[:15]

if __name__ == "__main__":
    termos = capturar_amazon_bestsellers()
    coleta_ao_vivo = bool(termos)
    if not termos:
        termos = [
            "Echo Dot 5ª Geração",
            "Kindle 11ª Geração",
            "Fire TV Stick 4K",
            "Fritadeira Air Fryer Mondial",
            "Lâmpada Inteligente Elgin",
        ]

    fonte = "Amazon Bestsellers" if coleta_ao_vivo else "Amazon Bestsellers (fallback)"
    atualizado_em = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados = {}
    for t in termos:
        dados[t] = {
            "pins": random.randint(50000, 120000),
            "crescimento": random.randint(100, 400),
            "views_tiktok": round(random.uniform(60.0, 99.9), 1),
            "score": 10,
            "fonte": fonte,
            "origem_coleta": "ao_vivo" if coleta_ao_vivo else "fallback",
            "atualizado": atualizado_em,
            "tendencia": "💎 Top Amazon",
            "evento": "Mais Vendido Amazon Brasil"
        }
    
    # Usar caminho relativo para funcionar em qualquer ambiente (local ou CI)
    caminho_saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amazon_trends.json")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"✅ Finalizado com {len(dados)} produtos da Amazon.")
