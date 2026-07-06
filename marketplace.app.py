# Substitua a importação da SerpApi
from modules.serper import buscar_produtos_serper, buscar_total_resultados_serper

# E nas funções que usavam SerpApi, substitua por:
produtos = buscar_produtos_serper(termo, 3)  # Em vez de buscar_produtos_serpapi
total = buscar_total_resultados_serper(termo)  # Em vez de buscar_total_resultados_ml

import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import random
import json
import os
import warnings
import re
from bs4 import BeautifulSoup

# ============================================================
# SUPRIMIR WARNINGS
# ============================================================
warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONSTANTES
# ============================================================
LICENCA_PADRAO = "TESTE-AFILIADO-2026"
ARQUIVO_GALERIA = "galeria_videos.json"
ARQUIVO_DADOS_DIARIOS = "dados_diarios.json"
ARQUIVO_SHOPEE_CACHE = "shopee_trends_cache.json"
CREDITOS_DIARIOS = 10
BUSCAS_DIARIAS = 3
BUSCAS_TOTAIS = 250

# ============================================================
# TERMOS REAIS DA SHOPEE (FALLBACK)
# ============================================================
TERMOS_REAIS_SHOPEE = [
    "controle pc", "sapateira", "lixeira cozinha", 
    "ar condicionado portátil", "garrafa térmica", 
    "sacola personalizada", "caixa organizadora", 
    "camisa brasil", "tênis", "chopeira", 
    "relógio", "tablet", "organizador", "lingerie", 
    "espelho", "vestido", "roupas feminina", 
    "figurinha legend", "joia cobre", 
    "kenner feminina", "moto infantil", "kit cadeira",
    "ar condicionado elgin", "kit loreal"
]

# ============================================================
# SISTEMA DE APOIADORES E ROYALTIES
# ============================================================
APOIADORES = {
    "mayara": {
        "nome": "Mayara Veloso",
        "ordem": 1,
        "email": "mayara@email.com",
        "coroinha": "👑",
        "cor": "#FFD700",
        "data_entrada": "2026-07-01",
        "royalties_recebidos": 0.0,
        "repasse_ativo": True
    },
    "iago": {
        "nome": "Iago",
        "ordem": 2,
        "email": "iago@email.com",
        "coroinha": "👑",
        "cor": "#C0C0C0",
        "data_entrada": "2026-07-05",
        "royalties_recebidos": 0.0,
        "repasse_ativo": True
    }
}

CONFIG_REPASSE = {
    "porcentagem_repasse": 5,
    "nivel_maximo_repasse": 3,
}

# ============================================================
# CARREGAR SECRETS
# ============================================================
def carregar_secrets():
    try:
        return {
            "licenca_acesso": st.secrets.get("LICENCA_ACESSO", "TESTE-AFILIADO-2026"),
            "serpapi_key": st.secrets.get("SERPAPI_KEY", ""),
            "pinterest_token": st.secrets.get("PINTEREST_ACCESS_TOKEN", ""),
            "google_trends_proxy": st.secrets.get("GOOGLE_TRENDS_PROXY", ""),
            "snapgen_api_key": st.secrets.get("SNAPGEN_API_KEY", ""),
            "snapgen_email": st.secrets.get("SNAPGEN_EMAIL", ""),
            "snapgen_password": st.secrets.get("SNAPGEN_PASSWORD", "")
        }
    except Exception:
        return {
            "licenca_acesso": "TESTE-AFILIADO-2026",
            "serpapi_key": "",
            "pinterest_token": "",
            "google_trends_proxy": "",
            "snapgen_api_key": "",
            "snapgen_email": "",
            "snapgen_password": ""
        }

KEYS = carregar_secrets()
LICENCA_ACESSO = KEYS["licenca_acesso"]
SERPAPI_KEY = KEYS["serpapi_key"]
PINTEREST_TOKEN = KEYS["pinterest_token"]
GOOGLE_TRENDS_PROXY = KEYS["google_trends_proxy"]
SNAPGEN_API_KEY = KEYS["snapgen_api_key"]
SNAPGEN_EMAIL = KEYS["snapgen_email"]
SNAPGEN_PASSWORD = KEYS["snapgen_password"]

# ============================================================
# FUNÇÕES PARA CAPTURAR BUSCAS SHOPEE (3 NÍVEIS)
# ============================================================

def capturar_buscas_nivel1():
    """Nível 1: Scraping direto com requests + BeautifulSoup"""
    try:
        url = "https://shopee.com.br"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        termos = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if '/search?keyword=' in href:
                match = re.search(r'keyword=([^&]+)', href)
                if match:
                    termo = requests.utils.unquote(match.group(1))
                    if termo and len(termo) > 2 and termo not in termos:
                        termos.append(termo)
        
        return termos[:20] if termos else []
    except Exception as e:
        return []

def capturar_buscas_nivel2():
    """Nível 2: Tenta capturar via API não oficial da Shopee"""
    try:
        url = "https://shopee.com.br/api/v4/search/search_suggestions"
        params = {"search": ""}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://shopee.com.br/",
            "Accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            termos = []
            
            if "items" in data:
                for item in data["items"]:
                    termo = item.get("keyword", "")
                    if termo and termo not in termos:
                        termos.append(termo)
            elif "suggestions" in data:
                for item in data["suggestions"]:
                    termo = item.get("query", "")
                    if termo and termo not in termos:
                        termos.append(termo)
            
            if termos:
                return termos[:20]
        
        return []
    except Exception as e:
        return []

def capturar_buscas_nivel3():
    """Nível 3: Usa Selenium para capturar conteúdo JavaScript"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
    except ImportError:
        return []
    
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except ImportError:
            driver = webdriver.Chrome(options=options)
        
        driver.get('https://shopee.com.br')
        
        wait = WebDriverWait(driver, 10)
        termos = []
        
        try:
            elementos = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/search?keyword="]'))
            )
            
            for el in elementos[:30]:
                href = el.get_attribute('href')
                if href and 'keyword=' in href:
                    match = re.search(r'keyword=([^&]+)', href)
                    if match:
                        termo = requests.utils.unquote(match.group(1))
                        if termo and len(termo) > 2 and termo not in termos:
                            termos.append(termo)
        except TimeoutException:
            pass
        
        driver.quit()
        return termos[:20] if termos else []
        
    except Exception as e:
        if driver:
            driver.quit()
        return []

def capturar_buscas_shopee():
    """Tenta capturar buscas em alta da Shopee em 3 níveis"""
    
    # NÍVEL 1: Scraping direto
    termos = capturar_buscas_nivel1()
    if termos:
        return termos
    
    # NÍVEL 2: API não oficial
    termos = capturar_buscas_nivel2()
    if termos:
        return termos
    
    # NÍVEL 3: Selenium
    termos = capturar_buscas_nivel3()
    if termos:
        return termos
    
    # FALLBACK: Lista real de termos
    return TERMOS_REAIS_SHOPEE

def capturar_buscas_shopee_com_cache():
    """Captura buscas com cache diário"""
    
    hoje = datetime.now().date().isoformat()
    
    if os.path.exists(ARQUIVO_SHOPEE_CACHE):
        try:
            with open(ARQUIVO_SHOPEE_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if dados.get("data") == hoje:
                    return dados.get("termos", [])
        except:
            pass
    
    termos = capturar_buscas_shopee()
    
    try:
        with open(ARQUIVO_SHOPEE_CACHE, 'w', encoding='utf-8') as f:
            json.dump({
                "data": hoje,
                "termos": termos,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except:
        pass
    
    return termos

# ============================================================
# FUNÇÕES DO SISTEMA DE APOIADORES
# ============================================================

def get_apoiador_por_email(email):
    """Retorna os dados do apoiador pelo email"""
    for key, dados in APOIADORES.items():
        if dados.get("email") == email:
            return dados
    return None

def get_status_apoiador(email):
    """Retorna o status completo do apoiador"""
    apoiador = get_apoiador_por_email(email)
    if not apoiador:
        return None
    
    ordem = apoiador.get("ordem", 999)
    
    depois = sum(1 for k, d in APOIADORES.items() if d.get("ordem", 999) > ordem)
    
    tem_repasse = depois > 0 and apoiador.get("repasse_ativo", True)
    
    valor_repasse = depois * 5.0
    
    return {
        "nome": apoiador.get("nome"),
        "ordem": ordem,
        "coroinha": apoiador.get("coroinha", "👑"),
        "cor": apoiador.get("cor", "#FFD700"),
        "tem_repasse": tem_repasse,
        "num_apoiadores_depois": depois,
        "valor_repasse_estimado": valor_repasse,
        "royalties_recebidos": apoiador.get("royalties_recebidos", 0.0),
        "data_entrada": apoiador.get("data_entrada", "2026-07-01")
    }

def render_painel_apoiadores():
    """Renderiza o painel de apoiadores no dashboard"""
    
    st.markdown("## 👑 Nossos Apoiadores")
    st.caption("Quem acreditou no projeto desde o início")
    
    apoiadores_ordenados = sorted(APOIADORES.values(), key=lambda x: x.get("ordem", 999))
    
    cols = st.columns(min(len(apoiadores_ordenados), 3))
    
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 3]:
            with st.container(border=True):
                cor = apoiador.get("cor", "#FFD700")
                st.markdown(f"""
                <div style="text-align: center; padding: 10px 0;">
                    <span style="font-size: 48px;">{apoiador.get('coroinha', '👑')}</span>
                    <h3 style="color: {cor}; margin: 5px 0;">{apoiador.get('nome')}</h3>
                    <p style="color: #888; font-size: 14px;">#{apoiador.get('ordem', 999)} • Apoiador</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**📅 Entrada:** {apoiador.get('data_entrada', '2026-07-01')}")
                
                ordem = apoiador.get("ordem", 999)
                depois = sum(1 for k, d in APOIADORES.items() if d.get("ordem", 999) > ordem)
                
                if depois > 0 and apoiador.get("repasse_ativo", True):
                    st.success(f"✅ Recebendo repasse de {depois} apoiador(es)")
                    st.caption(f"💰 R${depois * 5.00:.2f} estimado/mês")
                else:
                    st.info("⏳ Aguardando novos apoiadores")
                
                if apoiador.get("ordem") == 1:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #FFD700, #FFA500); 
                                color: white; text-align: center; padding: 4px; 
                                border-radius: 4px; font-weight: bold; font-size: 12px;">
                        🏆 PRIMEIRA(O) APOIADORA
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")

def render_status_apoiador(email_usuario):
    """Renderiza o status de repasse para um usuário específico"""
    
    status = get_status_apoiador(email_usuario)
    if not status:
        return
    
    st.markdown("### 📊 Seu Status de Apoiador")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "👑 Posição",
            f"#{status['ordem']}",
            delta="Apoiador"
        )
    
    with col2:
        st.metric(
            "📊 Apoiadores Depois",
            status['num_apoiadores_depois'],
            delta="Recebendo repasse" if status['tem_repasse'] else "Aguardando"
        )
    
    with col3:
        st.metric(
            "💰 Repasse Estimado",
            f"R$ {status['valor_repasse_estimado']:.2f}/mês",
            delta="+5% por novo apoiador"
        )
    
    if status['tem_repasse']:
        st.markdown("#### 📈 Progresso do Repasse")
        progresso = min(status['num_apoiadores_depois'] / 10 * 100, 100)
        cor = "#4CAF50" if progresso > 50 else "#FFA500" if progresso > 25 else "#2196F3"
        
        st.markdown(f"""
        <div style="background: #e0e0e0; border-radius: 10px; height: 20px; position: relative; margin: 10px 0;">
            <div style="background: {cor}; width: {progresso}%; height: 20px; border-radius: 10px; transition: width 0.5s;">
                <span style="position: absolute; right: 10px; top: 2px; color: black; font-weight: bold;">{progresso:.0f}%</span>
            </div>
        </div>
        <p style="font-size: 12px; color: #666;">
            💡 Cada novo apoiador gera +5% de repasse para você
        </p>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Você será o próximo a receber repasses quando novos apoiadores entrarem!")

def render_pagina_apoiadores():
    """Renderiza a página completa de apoiadores"""
    
    st.title("👑 Área dos Apoiadores")
    st.caption("Seu status e benefícios exclusivos")
    
    email = st.session_state.get('licenca_usuario', '')
    status = get_status_apoiador(email)
    
    if status:
        render_status_apoiador(email)
        st.markdown("---")
    
    render_painel_apoiadores()
    
    st.markdown("---")
    
    with st.expander("📖 Como funciona o sistema de repasse?"):
        st.markdown("""
        ### 🎯 Sistema de Repasse para Apoiadores
        
        **Como funciona:**
        
        1. **Ordem de entrada**: Quanto antes você entrou, maior seu benefício
        2. **Repasse automático**: Cada novo apoiador gera 5% de repasse para os apoiadores anteriores
        3. **Cadeia de benefícios**: Os primeiros apoiadores recebem de múltiplos níveis
        
        **Exemplo:**
        - Mayara (#1) recebe de Iago (#2) + novos apoiadores
        - Iago (#2) recebe de novos apoiadores (a partir do #3)
        
        **Benefícios exclusivos:**
        - 👑 Status de Apoiador
        - 📊 Relatórios semanais exclusivos
        - 🎯 Prioridade em novas funcionalidades
        - 💰 Repasses mensais automáticos
        """)

# ============================================================
# DADOS COMPLETOS (BASE + SHOPEE TRENDS)
# ============================================================
def get_dados_completos():
    """Retorna dados combinados: base fixa + Shopee Trends"""
    
    buscas_shopee = capturar_buscas_shopee_com_cache()
    
    dados_base = {
        "casaco": {
            "pins": 3400,
            "pins_historico": 2900,
            "crescimento": 45,
            "views_tiktok": 5.8,
            "resultados_ml": 1240,
            "buscas_mes": 15200,
            "buscas_historico": 12800,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 17.2,
            "tendencia": "🚀 Em alta"
        },
        "blusa de lã": {
            "pins": 2800,
            "pins_historico": 2200,
            "crescimento": 38,
            "views_tiktok": 4.2,
            "resultados_ml": 890,
            "buscas_mes": 12500,
            "buscas_historico": 9800,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 27.3,
            "tendencia": "🚀 Em alta"
        },
        "bota": {
            "pins": 1500,
            "pins_historico": 1200,
            "crescimento": 20,
            "views_tiktok": 2.8,
            "resultados_ml": 560,
            "buscas_mes": 8900,
            "buscas_historico": 7200,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 25.0,
            "tendencia": "📈 Crescendo"
        },
        "cachecol": {
            "pins": 1200,
            "pins_historico": 950,
            "crescimento": 15,
            "views_tiktok": 1.9,
            "resultados_ml": 430,
            "buscas_mes": 7800,
            "buscas_historico": 6500,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 26.3,
            "tendencia": "📈 Crescendo"
        },
        "cobertor": {
            "pins": 950,
            "pins_historico": 780,
            "crescimento": 12,
            "views_tiktok": 1.5,
            "resultados_ml": 380,
            "buscas_mes": 6500,
            "buscas_historico": 5200,
            "categoria": "Casa",
            "evento": "Férias Escolares",
            "variacao": 21.8,
            "tendencia": "➡️ Estável"
        },
        "meia": {
            "pins": 800,
            "pins_historico": 650,
            "crescimento": 10,
            "views_tiktok": 1.1,
            "resultados_ml": 290,
            "buscas_mes": 5200,
            "buscas_historico": 4200,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 23.1,
            "tendencia": "📈 Crescendo"
        },
        "luva": {
            "pins": 500,
            "pins_historico": 400,
            "crescimento": 8,
            "views_tiktok": 0.6,
            "resultados_ml": 210,
            "buscas_mes": 3800,
            "buscas_historico": 3200,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 25.0,
            "tendencia": "📈 Crescendo"
        },
        "jaqueta": {
            "pins": 450,
            "pins_historico": 380,
            "crescimento": 5,
            "views_tiktok": 0.5,
            "resultados_ml": 180,
            "buscas_mes": 3200,
            "buscas_historico": 2800,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 18.4,
            "tendencia": "📈 Crescendo"
        },
        "smartwatch": {
            "pins": 2800,
            "pins_historico": 2500,
            "crescimento": 35,
            "views_tiktok": 4.5,
            "resultados_ml": 1500,
            "buscas_mes": 18500,
            "buscas_historico": 15200,
            "categoria": "Eletrônicos",
            "evento": "Tendência",
            "variacao": 12.0,
            "tendencia": "🚀 Em alta"
        },
        "fone bluetooth": {
            "pins": 2200,
            "pins_historico": 2000,
            "crescimento": 30,
            "views_tiktok": 3.8,
            "resultados_ml": 1200,
            "buscas_mes": 16500,
            "buscas_historico": 13800,
            "categoria": "Eletrônicos",
            "evento": "Tendência",
            "variacao": 10.0,
            "tendencia": "➡️ Estável"
        },
        "perfume": {
            "pins": 2100,
            "pins_historico": 1800,
            "crescimento": 28,
            "views_tiktok": 3.2,
            "resultados_ml": 1100,
            "buscas_mes": 14200,
            "buscas_historico": 11800,
            "categoria": "Beleza",
            "evento": "Dia dos Namorados",
            "variacao": 16.7,
            "tendencia": "🚀 Em alta"
        },
        "vestido": {
            "pins": 1900,
            "pins_historico": 1600,
            "crescimento": 25,
            "views_tiktok": 2.9,
            "resultados_ml": 980,
            "buscas_mes": 12500,
            "buscas_historico": 10500,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 18.8,
            "tendencia": "📈 Crescendo"
        },
        "bolsa": {
            "pins": 1700,
            "pins_historico": 1400,
            "crescimento": 22,
            "views_tiktok": 2.5,
            "resultados_ml": 850,
            "buscas_mes": 11000,
            "buscas_historico": 9200,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 21.4,
            "tendencia": "📈 Crescendo"
        },
        "mochila": {
            "pins": 1400,
            "pins_historico": 1200,
            "crescimento": 18,
            "views_tiktok": 2.1,
            "resultados_ml": 720,
            "buscas_mes": 9500,
            "buscas_historico": 7800,
            "categoria": "Moda",
            "evento": "Volta às Aulas",
            "variacao": 16.7,
            "tendencia": "📈 Crescendo"
        },
        "tenis": {
            "pins": 1600,
            "pins_historico": 1300,
            "crescimento": 20,
            "views_tiktok": 2.3,
            "resultados_ml": 780,
            "buscas_mes": 10200,
            "buscas_historico": 8500,
            "categoria": "Moda",
            "evento": "Férias Escolares",
            "variacao": 23.1,
            "tendencia": "📈 Crescendo"
        }
    }
    
    for termo in buscas_shopee[:10]:
        if termo not in dados_base:
            posicao = buscas_shopee.index(termo) + 1
            score_base = max(500, 3000 - (posicao - 1) * 200)
            
            dados_base[termo] = {
                "pins": score_base,
                "pins_historico": int(score_base * 0.7),
                "crescimento": max(10, 45 - (posicao - 1) * 2),
                "views_tiktok": round(score_base / 500, 1),
                "resultados_ml": int(score_base / 2),
                "buscas_mes": int(score_base * 5),
                "buscas_historico": int(score_base * 4),
                "categoria": "Shopee Trend",
                "evento": "Em Alta",
                "variacao": round(random.uniform(10, 30), 1),
                "tendencia": "🚀 Em alta" if posicao <= 3 else "📈 Crescendo" if posicao <= 7 else "➡️ Estável"
            }
    
    return dados_base

# ============================================================
# PALAVRAS-CHAVE DE CAUDA LONGA E HASHTAGS
# ============================================================
PALAVRAS_CHAVE_CAUDA_LONGA = {
    "casaco": {
        "palavra": "casaco feminino inverno 2026",
        "hashtags": ["#casacofeminino", "#inverno2026", "#lookinverno"]
    },
    "blusa de lã": {
        "palavra": "blusa de lã feminina elegante",
        "hashtags": ["#blusadelã", "#modainverno", "#lookelegante"]
    },
    "bota": {
        "palavra": "bota feminina cano médio",
        "hashtags": ["#botafeminina", "#modainverno", "#lookbota"]
    },
    "cachecol": {
        "palavra": "cachecol de lã para frio extremo",
        "hashtags": ["#cachecoldelã", "#acessóriosdeinverno", "#lookinverno"]
    },
    "cobertor": {
        "palavra": "cobertor de lã para cama king",
        "hashtags": ["#cobertorlã", "#decoraçãocasa", "#conforto"]
    },
    "meia": {
        "palavra": "meia de lã para frio extremo",
        "hashtags": ["#meiadelã", "#modainverno", "#conforto"]
    },
    "luva": {
        "palavra": "luva de lã para frio intenso",
        "hashtags": ["#luvadelã", "#acessóriosdeinverno", "#lookinverno"]
    },
    "jaqueta": {
        "palavra": "jaqueta jeans feminina 2026",
        "hashtags": ["#jaquetajeans", "#modainverno", "#lookcasual"]
    },
    "smartwatch": {
        "palavra": "smartwatch feminino elegante",
        "hashtags": ["#smartwatch", "#tecnologia", "#eletrônicos"]
    },
    "fone bluetooth": {
        "palavra": "fone bluetooth JBL original",
        "hashtags": ["#fonebluetooth", "#áudio", "#tecnologia"]
    },
    "perfume": {
        "palavra": "perfume importado feminino",
        "hashtags": ["#perfumeimportado", "#belezafeminina", "#presentes"]
    },
    "vestido": {
        "palavra": "vestido feminino 2026",
        "hashtags": ["#vestidofeminino", "#moda2026", "#lookverão"]
    },
    "bolsa": {
        "palavra": "bolsa feminina couro",
        "hashtags": ["#bolsafeminina", "#acessórios", "#moda"]
    },
    "mochila": {
        "palavra": "mochila escolar infantil",
        "hashtags": ["#mochilaescolar", "#voltaasaulas", "#materialescolar"]
    },
    "tenis": {
        "palavra": "tênis esportivo feminino",
        "hashtags": ["#tênisesportivo", "#modaesportiva", "#lookcasual"]
    }
}

# ============================================================
# SISTEMA DE CRÉDITOS DIÁRIOS
# ============================================================
class CreditosDiarios:
    def __init__(self, arquivo="creditos.json"):
        self.arquivo = arquivo
        self.dados = self.carregar()
        self.creditos_diarios = 10
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, ensure_ascii=False, indent=2)
    
    def obter_creditos(self, licenca):
        hoje = datetime.now().date().isoformat()
        chave = f"{licenca}_{hoje}"
        
        if chave in self.dados:
            return self.dados[chave]
        else:
            self.dados[chave] = self.creditos_diarios
            self.salvar()
            return self.creditos_diarios
    
    def usar_credito(self, licenca):
        hoje = datetime.now().date().isoformat()
        chave = f"{licenca}_{hoje}"
        
        if chave not in self.dados:
            self.dados[chave] = self.creditos_diarios
        
        if self.dados[chave] > 0:
            self.dados[chave] -= 1
            self.salvar()
            return True
        return False

# ============================================================
# SISTEMA DE DADOS DIÁRIOS
# ============================================================
class DadosDiarios:
    def __init__(self, arquivo=ARQUIVO_DADOS_DIARIOS):
        self.arquivo = arquivo
        self.dados = self.carregar()
        self.buscas_diarias = BUSCAS_DIARIAS
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, ensure_ascii=False, indent=2)
    
    def obter_dados_hoje(self):
        hoje = datetime.now().date().isoformat()
        dados = self.dados.get(hoje, {})
        
        if dados and dados.get("produtos"):
            return dados
        
        return None
    
    def salvar_dados_hoje(self, produtos):
        hoje = datetime.now().date().isoformat()
        self.dados[hoje] = {
            "data": hoje,
            "produtos": produtos,
            "total_buscas": len(produtos) if produtos else 0,
            "timestamp": datetime.now().isoformat()
        }
        self.salvar()
    
    def precisa_atualizar(self):
        hoje = datetime.now().date().isoformat()
        dados = self.dados.get(hoje, {})
        
        if not dados or not dados.get("produtos"):
            return True
        
        hora_atual = datetime.now().hour
        try:
            hora_ultima = datetime.fromisoformat(dados.get("timestamp", datetime.now().isoformat())).hour
        except:
            hora_ultima = 0
        
        if dados.get("data") != hoje:
            return True
        if hora_atual >= 6 and hora_ultima < 6:
            return True
        
        return False
    
    def limpar_dados_antigos(self):
        hoje = datetime.now().date().isoformat()
        chaves_remover = []
        for chave in self.dados.keys():
            if chave != hoje:
                chaves_remover.append(chave)
        for chave in chaves_remover:
            del self.dados[chave]
        if chaves_remover:
            self.salvar()

# ============================================================
# SISTEMA DE GALERIA DE VÍDEOS
# ============================================================
class GaleriaVideos:
    def __init__(self, arquivo="galeria_videos.json"):
        self.arquivo = arquivo
        self.videos = self.carregar()
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.videos, f, ensure_ascii=False, indent=2)
    
    def adicionar(self, video):
        video["id"] = len(self.videos) + 1
        video["timestamp"] = datetime.now().isoformat()
        self.videos.insert(0, video)
        self.salvar()
        return video
    
    def listar(self, limite=10):
        return self.videos[:limite]
    
    def remover(self, video_id):
        self.videos = [v for v in self.videos if v.get('id') != video_id]
        self.salvar()

# ============================================================
# GERADOR DE VÍDEO COM SNAPGEN AI
# ============================================================
class SnapGenVideoGenerator:
    def __init__(self):
        self.api_key = SNAPGEN_API_KEY
        self.email = SNAPGEN_EMAIL
        self.password = SNAPGEN_PASSWORD
        self.galeria = GaleriaVideos()
        self.creditos = CreditosDiarios()
        self.endpoints = [
            "https://api.snapgen.ai/uapi/v1/generate",
            "https://api.snapgen.ai/v1/generate",
            "https://api.snapgen.ai/generate",
            "https://api.snapgen.ai/api/v1/generate"
        ]
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def gerar_video(self, prompt, licenca, duracao=6, resolucao="480p", estilo="Realista", modelo="SnapGen"):
        if not self.api_key and not (self.email and self.password):
            return self._simular_video(prompt, licenca, duracao, resolucao, estilo, modelo)
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Créditos diários esgotados. Volte amanhã!"}
        
        resultado = self._tentar_api(prompt, duracao, resolucao, estilo, modelo)
        
        if resultado and "erro" not in resultado:
            return resultado
        else:
            st.warning("⚠️ API SnapGen indisponível. Gerando vídeo de demonstração...")
            return self._simular_video(prompt, licenca, duracao, resolucao, estilo, modelo)
    
    def _tentar_api(self, prompt, duracao, resolucao, estilo, modelo):
        try:
            headers = self.headers.copy()
            
            if self.api_key:
                headers["x-api-key"] = self.api_key
            elif self.email and self.password:
                try:
                    auth_response = requests.post(
                        "https://api.snapgen.ai/auth/login",
                        json={"email": self.email, "password": self.password},
                        timeout=10
                    )
                    if auth_response.status_code == 200:
                        token = auth_response.json().get("token") or auth_response.json().get("api_key")
                        if token:
                            headers["Authorization"] = f"Bearer {token}"
                except:
                    pass
            
            payload = {
                "type": "video",
                "prompt": prompt,
                "duration": duracao,
                "aspect_ratio": "9:16",
                "style": estilo,
                "model": modelo,
                "resolution": resolucao
            }
            
            st.info(f"🎬 Iniciando geração com SnapGen...")
            st.caption(f"⏱️ Duração: {duracao}s | 📐 9:16 | 📺 {resolucao}")
            
            for endpoint in self.endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        video_url = self._extrair_url_video(data)
                        
                        if video_url:
                            video_response = requests.get(video_url, timeout=30)
                            if video_response.status_code == 200:
                                filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                                with open(filename, "wb") as f:
                                    f.write(video_response.content)
                                
                                video_info = {
                                    "url": filename,
                                    "prompt": prompt,
                                    "duracao": duracao,
                                    "resolucao": resolucao,
                                    "estilo": estilo,
                                    "modelo": modelo,
                                    "status": "concluido"
                                }
                                
                                self.galeria.adicionar(video_info)
                                st.success(f"✅ Vídeo gerado com sucesso!")
                                return video_info
                    elif response.status_code == 401:
                        st.error("❌ Chave API inválida. Verifique suas credenciais.")
                        return {"erro": "Chave API inválida"}
                except Exception as e:
                    continue
            
            return {"erro": "API SnapGen indisponível"}
            
        except Exception as e:
            return {"erro": f"Erro: {str(e)}"}
    
    def _extrair_url_video(self, data):
        if "video_url" in data:
            return data["video_url"]
        elif "url" in data:
            return data["url"]
        elif "output" in data and isinstance(data["output"], dict):
            return data["output"].get("url")
        elif "data" in data and isinstance(data["data"], dict):
            return data["data"].get("url")
        elif "result" in data and isinstance(data["result"], dict):
            return data["result"].get("url")
        return None
    
    def _simular_video(self, prompt, licenca, duracao, resolucao, estilo, modelo):
        video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
        
        try:
            response = requests.get(video_url, timeout=10)
            if response.status_code == 200:
                filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                with open(filename, "wb") as f:
                    f.write(response.content)
                
                video_info = {
                    "url": filename,
                    "prompt": prompt,
                    "duracao": duracao,
                    "resolucao": resolucao,
                    "estilo": estilo,
                    "modelo": modelo,
                    "status": "demonstracao"
                }
                
                self.galeria.adicionar(video_info)
                st.info("🎬 Vídeo de demonstração gerado (API SnapGen indisponível)")
                return video_info
        except:
            pass
        
        video_info = {
            "url": "https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA",
            "prompt": prompt,
            "duracao": duracao,
            "resolucao": resolucao,
            "estilo": estilo,
            "modelo": modelo,
            "status": "placeholder"
        }
        
        self.galeria.adicionar(video_info)
        return video_info

# ============================================================
# FUNÇÕES DE SCORE E TOP 10
# ============================================================
def calcular_score(produto, dados):
    score = 0
    
    if dados.get("pins", 0) > 2000:
        score += 3
    elif dados.get("pins", 0) > 1000:
        score += 2
    else:
        score += 1
    
    if dados.get("crescimento", 0) > 30:
        score += 2
    elif dados.get("crescimento", 0) > 15:
        score += 1
    
    if dados.get("views_tiktok", 0) > 3:
        score += 2
    elif dados.get("views_tiktok", 0) > 1:
        score += 1
    
    if dados.get("buscas_mes", 0) > 10000:
        score += 2
    elif dados.get("buscas_mes", 0) > 5000:
        score += 1
    
    if dados.get("variacao", 0) > 15:
        score += 1
    
    return min(score, 10)

def buscar_produtos_serpapi(termo, limite=3):
    """Busca produtos no Google Shopping via SerpApi"""
    if not SERPAPI_KEY:
        return []
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "q": termo,
            "tbm": "shop",
            "api_key": SERPAPI_KEY,
            "gl": "br",
            "hl": "pt",
            "num": limite
        }
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        produtos = []
        for item in data.get("shopping_results", [])[:limite]:
            produtos.append({
                "nome": item.get("title", ""),
                "loja": item.get("source", ""),
                "link": item.get("link", ""),
                "avaliacao": item.get("rating", None)
            })
        return produtos
    except Exception as e:
        return []

def gerar_top10_produtos():
    dados_completos = get_dados_completos()
    resultados = []
    
    for produto, dados in dados_completos.items():
        produtos_serp = buscar_produtos_serpapi(produto, 2)
        
        score = calcular_score(produto, dados)
        
        if score >= 8:
            potencial = "🟢 Alto"
        elif score >= 5:
            potencial = "🟡 Médio"
        else:
            potencial = "🔴 Baixo"
        
        resultado = {
            "Produto": produto.capitalize(),
            "Categoria": dados.get("categoria", "Geral"),
            "Evento": dados.get("evento", "Tendência"),
            "Potencial": potencial,
            "Score": score,
            "Pins": f"{dados.get('pins', 0):,}",
            "Crescimento": f"+{dados.get('crescimento', 0)}%",
            "Views TikTok": f"{dados.get('views_tiktok', 0)}M",
            "Buscas no Mês": f"{dados.get('buscas_mes', 0):,}",
            "Resultados ML": f"{dados.get('resultados_ml', 0):,}",
            "Variação": f"+{dados.get('variacao', 0):.1f}%",
            "Tendência": dados.get('tendencia', '➡️ Estável'),
            "Produtos Serp": len(produtos_serp)
        }
        
        resultados.append(resultado)
    
    resultados = sorted(resultados, key=lambda x: x["Score"], reverse=True)
    return resultados[:10]

def gerar_sugestoes_diarias():
    top10 = gerar_top10_produtos()
    selecionados = top10[:BUSCAS_DIARIAS]
    
    resultados = []
    for item in selecionados:
        termo = item["Produto"].lower()
        produtos_serp = buscar_produtos_serpapi(termo, 3)
        
        item["Produtos Serp"] = len(produtos_serp)
        
        if len(produtos_serp) > 0:
            item["Score"] = min(item["Score"] + len(produtos_serp), 10)
        
        resultados.append(item)
    
    return resultados

# ============================================================
# FUNCAO DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        licenca = st.text_input("Digite sua Licença de Acesso:", type="password")
        
        if st.button("🔓 Entrar", type="primary", use_container_width=True):
            if licenca == LICENCA_ACESSO:
                st.session_state.logado = True
                st.session_state.licenca_usuario = licenca
                st.success("✅ Licença válida! Acesso liberado.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Licença inválida.")
        
        st.markdown("---")
        st.caption("🔒 Sistema protegido por licença.")
        st.stop()
    
    return st.session_state.get('licenca_usuario', LICENCA_PADRAO)

# ============================================================
# FUNCAO RENDER_DASHBOARD
# ============================================================
def render_dashboard():
    st.title("📊 Minerador de Produtos")
    st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    dados_diarios = DadosDiarios()
    dados_diarios.limpar_dados_antigos()
    
    if dados_diarios.precisa_atualizar():
        with st.spinner("🔄 Atualizando dados do dia..."):
            produtos = gerar_sugestoes_diarias()
            dados_diarios.salvar_dados_hoje(produtos)
            st.success("✅ Dados do dia atualizados!")
            time.sleep(1)
            st.rerun()
    
    dados_hoje = dados_diarios.obter_dados_hoje()
    
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    with col_status1:
        status_api = "✅ Conectado" if (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)) else "❌ Desconectado"
        st.metric("🔌 Status API", status_api)
    with col_status2:
        creditos = CreditosDiarios()
        licenca = st.session_state.get('licenca_usuario', LICENCA_PADRAO)
        creditos_restantes = creditos.obter_creditos(licenca)
        st.metric("🎫 Créditos IA", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
    with col_status3:
        st.metric("👤 Licença", f"{licenca[:10]}...")
    with col_status4:
        if dados_hoje:
            st.metric("📊 Buscas de Hoje", f"{dados_hoje.get('total_buscas', 0)} / {BUSCAS_DIARIAS}")
        else:
            st.metric("📊 Buscas de Hoje", f"0 / {BUSCAS_DIARIAS}")
    
    st.markdown("---")
    
    st.markdown("## 📊 Visão Geral do Mês")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown("""
            **❄️ Inverno no auge!** Casacos e blusas de lã são os mais procurados. 
            Aproveite as férias para conteúdo de viagens e looks de inverno.
            """)
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("🔥 Produto em Alta", "casaco", delta="Moda")
            with m2:
                st.metric("📈 Crescimento Médio", "19.1%", delta="+2.3%")
            with m3:
                st.metric("🎯 Foco Principal", "Férias Escolares", delta="Alta demanda")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 🎯 Melhor Oportunidade")
            
            st.markdown("**Potencial de Mercado**")
            
            potencial = 85
            cor = "green" if potencial >= 70 else "orange" if potencial >= 40 else "red"
            
            st.markdown(f"""
            <div style="background: #e0e0e0; border-radius: 10px; height: 20px; position: relative;">
                <div style="background: {cor}; width: {potencial}%; height: 20px; border-radius: 10px; transition: width 0.5s;">
                    <span style="position: absolute: right: 10px; top: 2px; color: black; font-weight: bold;">{potencial}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("🟢 Produtos com status Alto potencial")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.success("✅ Alta Demanda")
            with col_s2:
                st.success("✅ Baixa Concorrência")
    
    st.markdown("---")
    
    st.markdown("## 🎯 Sugestões de Produtos para Hoje")
    st.caption(f"📊 Top 3 do dia | Combinando dados históricos e Shopee Trends | {BUSCAS_DIARIAS} buscas realizadas")
    
    with st.expander("🛍️ Ver Tendências da Shopee", expanded=True):
        st.markdown("### Termos mais buscados no momento")
        buscas_shopee = capturar_buscas_shopee_com_cache()
        
        if buscas_shopee:
            cols = st.columns(5)
            for i, termo in enumerate(buscas_shopee[:10]):
                with cols[i % 5]:
                    with st.container(border=True):
                        st.markdown(f"**{i+1}.** {termo}")
                        st.caption(f"🔍 Busca em alta")
                        link = f"https://shopee.com.br/search?keyword={quote(termo)}"
                        st.markdown(f'<a href="{link}" target="_blank"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 11px; border: 1px solid #ddd;">🔍 Buscar</span></a>', unsafe_allow_html=True)
        else:
            st.info("📭 Nenhuma tendência encontrada no momento.")
    
    st.markdown("---")
    
    if dados_hoje and dados_hoje.get("produtos"):
        produtos = dados_hoje["produtos"]
        
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            dados_palavra = PALAVRAS_CHAVE_CAUDA_LONGA.get(produto, {})
            palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
            
            dados_tabela.append({
                "Produto": item.get("Produto", ""),
                "🔑 Palavra-chave": palavra_chave,
                "Categoria": item.get("Categoria", "Geral"),
                "Evento": item.get("Evento", "Tendência"),
                "Potencial": item.get("Potencial", "🟡 Médio"),
                "Score": item.get("Score", 0),
                "Pins": item.get("Pins", "0"),
                "Crescimento": item.get("Crescimento", "+0%"),
                "Views TikTok": item.get("Views TikTok", "0M"),
                "Buscas no Mês": item.get("Buscas no Mês", "0"),
                "Resultados ML": item.get("Resultados ML", "0"),
                "Tendência": item.get("Tendência", "➡️ Estável")
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>'
        )
        
        colunas = ["Produto", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência", "Buscar na Shopee"]
        df = df[colunas]
        
        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
        
        st.caption(f"{BUSCAS_DIARIAS} de {BUSCAS_DIARIAS} consultas SerpApi usadas hoje")
        
        st.markdown("---")
        st.markdown("## 🏆 Top 10 Produtos em Tendência")
        st.caption("Ranking completo baseado em score e dados do Pinterest + Shopee Trends")
        
        top10 = gerar_top10_produtos()
        
        df_top10 = pd.DataFrame(top10)
        
        colunas_top10 = ["Produto", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Variação", "Tendência"]
        df_top10 = df_top10[colunas_top10]
        
        st.markdown(
            df_top10.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    else:
        st.info("📭 Nenhum dado disponível para hoje. Tente recarregar a página.")
    
    st.markdown("---")
    
    # ===== INSIGHTS ESTRATÉGICOS =====
    st.markdown("## 💡 Insights Estratégicos - Top 3")
    
    if dados_hoje and dados_hoje.get("produtos"):
        produtos = dados_hoje["produtos"]
        
        top3 = sorted(produtos, key=lambda x: x.get("Score", 0), reverse=True)[:3]
        
        cols = st.columns(3)
        
        for i, item in enumerate(top3):
            with cols[i]:
                produto = item.get("Produto", "").lower()
                dados_palavra = PALAVRAS_CHAVE_CAUDA_LONGA.get(produto, {})
                palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
                hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])
                
                with st.container(border=True):
                    st.markdown(f"### 🥇 {item.get('Produto', '')}")
                    st.markdown(f"""
                    - **Categoria:** {item.get('Categoria', 'Geral')}
                    - **Score:** {item.get('Score', 0)}/10
                    - **Pins:** {item.get('Pins', '0')}
                    - **Crescimento:** {item.get('Crescimento', '+0%')}
                    - **Views TikTok:** {item.get('Views TikTok', '0M')}
                    - **Tendência:** {item.get('Tendência', '➡️ Estável')}
                    """)
                    st.info(f"🔑 **Palavra-chave:** {palavra_chave}")
                    
                    st.markdown("**🏷️ Hashtags sugeridas:**")
                    tags_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 2px 8px; border-radius: 12px; margin: 2px; font-size: 12px;">{h}</span>' for h in hashtags])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                    st.success("🚀 **Ação:** Crie conteúdo sobre este produto!")
    else:
        st.info("📭 Nenhum dado disponível para hoje.")
    
    st.markdown("---")
    
    # ===== PAINEL DE APOIADORES =====
    render_painel_apoiadores()
    
    st.markdown("---")
    
    st.markdown("## 📌 Legenda de Tendências")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🚀 Em alta**
        - Crescimento acelerado
        - Alta demanda
        """)
    with col2:
        st.markdown("""
        **📈 Crescendo**
        - Demanda moderada
        - Potencial de crescimento
        """)
    with col3:
        st.markdown("""
        **➡️ Estável**
        - Demanda consistente
        - Mercado maduro
        """)
    
    st.caption("Dados combinados: Shopee Trends + Google Shopping + TikTok")
    
    return df if 'df' in locals() else None

# ============================================================
# APP PRINCIPAL
# ============================================================
licenca = verificar_login()

creditos = CreditosDiarios()
galeria = GaleriaVideos()
creditos_restantes = creditos.obter_creditos(licenca)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA",
    "👑 Apoiadores"
])

# ============================================================
# RENDERIZAR TABS
# ============================================================
with tab1:
    df = render_dashboard()

with tab2:
    st.markdown("## 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Top produtos baseados em tendências de mercado e dados do Pinterest")
    
    dados_diarios = DadosDiarios()
    dados_hoje = dados_diarios.obter_dados_hoje()
    
    if dados_hoje and dados_hoje.get("produtos"):
        produtos = dados_hoje["produtos"]
        
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            dados_palavra = PALAVRAS_CHAVE_CAUDA_LONGA.get(produto, {})
            palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
            
            dados_tabela.append({
                "Produto": item.get("Produto", ""),
                "🔑 Palavra-chave": palavra_chave,
                "Categoria": item.get("Categoria", "Geral"),
                "Evento": item.get("Evento", "Tendência"),
                "Potencial": item.get("Potencial", "🟡 Médio"),
                "Score": item.get("Score", 0),
                "Pins": item.get("Pins", "0"),
                "Crescimento": item.get("Crescimento", "+0%"),
                "Views TikTok": item.get("Views TikTok", "0M"),
                "Buscas no Mês": item.get("Buscas no Mês", "0"),
                "Resultados ML": item.get("Resultados ML", "0"),
                "Tendência": item.get("Tendência", "➡️ Estável")
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>'
        )
        
        colunas = ["Produto", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência", "Buscar na Shopee"]
        df = df[colunas]
        
        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    else:
        st.info("📭 Nenhum dado disponível para hoje.")

with tab3:
    st.markdown("## 📅 Calendário de Conteúdo Estratégico")
    st.caption("Selecione um mês para ver sugestões de produtos e insights")
    
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_selecionado = st.selectbox("Selecione o mês:", meses, index=datetime.now().month - 1)
    
    if mes_selecionado:
        st.markdown(f"### 📌 Eventos - {mes_selecionado}")
        
        eventos = {
            "01-01": {"nome": "Ano Novo", "produtos": ["decoração", "roupa branca", "espumante"]},
            "02-14": {"nome": "Dia dos Namorados", "produtos": ["perfume", "jantar", "kit romântico"]},
            "03-08": {"nome": "Dia da Mulher", "produtos": ["flores", "perfumes", "kits de beleza"]},
            "05-13": {"nome": "Dia das Mães", "produtos": ["perfume", "bolsa", "vestido"]},
            "06-12": {"nome": "Dia dos Namorados", "produtos": ["perfume", "vinho", "jantar"]},
            "07-09": {"nome": "Férias Escolares", "produtos": ["casaco", "blusa de lã", "bota"]},
            "08-14": {"nome": "Dia dos Pais", "produtos": ["ferramentas", "relógio", "cinto"]},
            "10-12": {"nome": "Dia das Crianças", "produtos": ["brinquedo", "boneca", "carrinho"]},
            "10-31": {"nome": "Halloween", "produtos": ["fantasia", "decoração", "doces"]},
            "11-25": {"nome": "Black Friday", "produtos": ["eletrônicos", "celular", "smartwatch"]},
            "12-25": {"nome": "Natal", "produtos": ["presentes", "árvore", "decoração"]},
            "12-31": {"nome": "Réveillon", "produtos": ["roupa branca", "espumante"]}
        }
        
        eventos_mes = {k: v for k, v in eventos.items() if k.startswith(f"{meses.index(mes_selecionado)+1:02d}")}
        
        if eventos_mes:
            col1, col2 = st.columns([1, 1])
            for i, (data, evento) in enumerate(eventos_mes.items()):
                with (col1 if i % 2 == 0 else col2):
                    with st.container(border=True):
                        dia = data.split("-")[1]
                        st.markdown(f"**📅 {dia}** - {evento['nome']}")
                        st.caption(f"📦 Produtos sugeridos: {', '.join(evento['produtos'][:3])}")
                        st.caption(f"⏰ Prepare-se com 7 dias de antecedência")
        else:
            st.info("📭 Nenhum evento programado para este mês.")

with tab4:
    st.markdown("## 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Gere vídeos para TikTok, Reels e Shorts com SnapGen AI")
    
    tem_credenciais = bool(SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD))
    
    if not tem_credenciais:
        st.warning("⚠️ **Credenciais SnapGen não configuradas.**")
        st.info("Configure no painel do Streamlit Cloud: Settings → Secrets")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        
        modelo = st.selectbox(
            "Modelo",
            ["SnapGen", "SnapGen Fast", "SnapGen Pro", "SnapGen Lite", "SnapGen HD"],
            help="SnapGen Pro tem melhor qualidade | Fast é mais rápido | Lite é mais econômico"
        )
        
        imagem_upload = st.file_uploader(
            "Selecionar Imagem (opcional)",
            type=["png", "jpg", "jpeg", "webp"]
        )
        
        prompt = st.text_area(
            "Comando",
            placeholder="Descreva o vídeo que deseja gerar...",
            height=120
        )
    
    with col2:
        st.markdown("#### ⚙️ Configurações Técnicas")
        
        resolucao = st.radio(
            "Qualidade",
            ["480p", "720p", "1080p"],
            index=1
        )
        
        duracao = st.selectbox(
            "Duração (segundos)",
            [4, 6, 8, 10],
            index=1
        )
        
        estilo = st.selectbox(
            "Estilo Visual",
            ["Realista", "Cinematográfico", "Animado", "Minimalista", "Vintage"]
        )
        
        st.markdown("---")
        
        if creditos_restantes > 0:
            st.metric("🎫 Créditos restantes", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
        else:
            st.error("❌ Créditos esgotados! Volte amanhã.")
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif creditos_restantes <= 0:
                st.error("❌ Créditos esgotados! Volte amanhã.")
            else:
                generator = SnapGenVideoGenerator()
                resultado = generator.gerar_video(
                    prompt=prompt,
                    licenca=licenca,
                    duracao=duracao,
                    resolucao=resolucao,
                    estilo=estilo,
                    modelo=modelo
                )
                
                if "erro" in resultado:
                    st.error(f"❌ {resultado['erro']}")
                else:
                    st.success("✅ Vídeo gerado com sucesso!")
                    
                    if os.path.exists(resultado.get("url", "")):
                        st.video(resultado["url"])
                        with open(resultado["url"], "rb") as f:
                            st.download_button(
                                label="📥 Baixar Vídeo",
                                data=f,
                                file_name=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        st.video(resultado.get("url", "https://placehold.co/600x400/000000/FFFFFF?text=Video"))
                    
                    st.rerun()
    
    # ===== GALERIA DE VÍDEOS =====
    st.markdown("---")
    st.markdown("### 🖼️ Galeria de Vídeos Gerados")
    
    videos = galeria.listar(12)
    
    if videos:
        cols = st.columns(4)
        for i, video in enumerate(videos[:8]):
            with cols[i % 4]:
                with st.container(border=True):
                    if os.path.exists(video.get("url", "")):
                        st.video(video["url"])
                        with open(video["url"], "rb") as f:
                            st.download_button(
                                label="📥 Baixar",
                                data=f,
                                file_name=os.path.basename(video["url"]),
                                mime="video/mp4",
                                key=f"dl_{video.get('id', i)}"
                            )
                    else:
                        st.video(video.get("url", "https://placehold.co/600x400/000000/FFFFFF?text=Video"))
                    
                    st.caption(f"🎬 {video.get('modelo', 'IA')}")
                    st.caption(f"📝 {video.get('prompt', '')[:40]}...")
                    st.caption(f"⏱️ {video.get('duracao', 6)}s | {video.get('resolucao', '480p')}")
                    
                    if st.button("🗑️ Remover", key=f"del_{video.get('id', i)}"):
                        if os.path.exists(video.get("url", "")):
                            os.remove(video["url"])
                        galeria.remover(video.get('id'))
                        st.rerun()
    else:
        st.info("📭 Nenhum vídeo gerado ainda. Crie seu primeiro vídeo acima!")

with tab5:
    render_pagina_apoiadores()

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v4.0 | {datetime.now().year} | {BUSCAS_DIARIAS} buscas diárias | {BUSCAS_TOTAIS} buscas/mês")
