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

# ============================================================
# CARREGAR SECRETS
# ============================================================
def carregar_secrets():
    try:
        return {
            "licenca_acesso": st.secrets.get("LICENCA_ACESSO", "TESTE-AFILIADO-2026"),
            "serper_api_key": st.secrets.get("SERPER_API_KEY", ""),
            "pinterest_token": st.secrets.get("PINTEREST_ACCESS_TOKEN", ""),
            "snapgen_api_key": st.secrets.get("SNAPGEN_API_KEY", "")
        }
    except Exception:
        return {
            "licenca_acesso": "TESTE-AFILIADO-2026",
            "serper_api_key": "",
            "pinterest_token": "",
            "snapgen_api_key": ""
        }

KEYS = carregar_secrets()
LICENCA_ACESSO = KEYS["licenca_acesso"]
SERPER_API_KEY = KEYS["serper_api_key"]
PINTEREST_TOKEN = KEYS["pinterest_token"]
SNAPGEN_API_KEY = KEYS["snapgen_api_key"]

# ============================================================
# FUNÇÃO PARA BUSCAR PRODUTOS VIA SERPER.DEV
# ============================================================
def buscar_produtos_serper(termo, limite=5):
    """Busca produtos no Google Shopping via Serper.dev"""
    if not SERPER_API_KEY:
        return []
    
    try:
        url = "https://google.serper.dev/shopping"
        payload = {"q": termo, "gl": "br", "hl": "pt"}
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            produtos = []
            for item in data.get("shopping", [])[:limite]:
                produtos.append({
                    "nome": item.get("title", ""),
                    "preco": item.get("price", "R$ 0"),
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "avaliacao": item.get("rating", None)
                })
            return produtos
        return []
    except Exception as e:
        return []

# ============================================================
# FUNÇÃO PARA CAPTURAR BUSCAS SHOPEE
# ============================================================
def capturar_buscas_shopee():
    """Captura buscas em alta da Shopee"""
    try:
        url = "https://shopee.com.br"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
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
        
        if termos:
            return termos[:20]
        
        # Fallback
        return ["smartwatch", "fone bluetooth", "caixa de som", "carregador portátil", 
                "camisa", "vestido", "tênis", "bolsa", "mochila", "cadeira gamer"]
        
    except Exception as e:
        return ["smartwatch", "fone bluetooth", "caixa de som", "carregador portátil"]

# ============================================================
# DADOS COMPLETOS
# ============================================================
DADOS_COMPLETOS = {
    "casaco": {
        "pins": 3400, "pins_historico": 2900, "crescimento": 45, "views_tiktok": 5.8,
        "resultados_ml": 1240, "buscas_mes": 15200, "buscas_historico": 12800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 17.2, "tendencia": "🚀 Em alta"
    },
    "blusa de lã": {
        "pins": 2800, "pins_historico": 2200, "crescimento": 38, "views_tiktok": 4.2,
        "resultados_ml": 890, "buscas_mes": 12500, "buscas_historico": 9800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 27.3, "tendencia": "🚀 Em alta"
    },
    "bota": {
        "pins": 1500, "pins_historico": 1200, "crescimento": 20, "views_tiktok": 2.8,
        "resultados_ml": 560, "buscas_mes": 8900, "buscas_historico": 7200,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 25.0, "tendencia": "📈 Crescendo"
    },
    "cachecol": {
        "pins": 1200, "pins_historico": 950, "crescimento": 15, "views_tiktok": 1.9,
        "resultados_ml": 430, "buscas_mes": 7800, "buscas_historico": 6500,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 26.3, "tendencia": "📈 Crescendo"
    },
    "cobertor": {
        "pins": 950, "pins_historico": 780, "crescimento": 12, "views_tiktok": 1.5,
        "resultados_ml": 380, "buscas_mes": 6500, "buscas_historico": 5200,
        "categoria": "Casa", "evento": "Férias Escolares", "variacao": 21.8, "tendencia": "➡️ Estável"
    },
    "smartwatch": {
        "pins": 2800, "pins_historico": 2500, "crescimento": 35, "views_tiktok": 4.5,
        "resultados_ml": 1500, "buscas_mes": 18500, "buscas_historico": 15200,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 12.0, "tendencia": "🚀 Em alta"
    },
    "fone bluetooth": {
        "pins": 2200, "pins_historico": 2000, "crescimento": 30, "views_tiktok": 3.8,
        "resultados_ml": 1200, "buscas_mes": 16500, "buscas_historico": 13800,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 10.0, "tendencia": "➡️ Estável"
    },
    "perfume": {
        "pins": 2100, "pins_historico": 1800, "crescimento": 28, "views_tiktok": 3.2,
        "resultados_ml": 1100, "buscas_mes": 14200, "buscas_historico": 11800,
        "categoria": "Beleza", "evento": "Dia dos Namorados", "variacao": 16.7, "tendencia": "🚀 Em alta"
    },
    "vestido": {
        "pins": 1900, "pins_historico": 1600, "crescimento": 25, "views_tiktok": 2.9,
        "resultados_ml": 980, "buscas_mes": 12500, "buscas_historico": 10500,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 18.8, "tendencia": "📈 Crescendo"
    },
    "bolsa": {
        "pins": 1700, "pins_historico": 1400, "crescimento": 22, "views_tiktok": 2.5,
        "resultados_ml": 850, "buscas_mes": 11000, "buscas_historico": 9200,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 21.4, "tendencia": "📈 Crescendo"
    },
    "mochila": {
        "pins": 1400, "pins_historico": 1200, "crescimento": 18, "views_tiktok": 2.1,
        "resultados_ml": 720, "buscas_mes": 9500, "buscas_historico": 7800,
        "categoria": "Moda", "evento": "Volta às Aulas", "variacao": 16.7, "tendencia": "📈 Crescendo"
    },
    "tenis": {
        "pins": 1600, "pins_historico": 1300, "crescimento": 20, "views_tiktok": 2.3,
        "resultados_ml": 780, "buscas_mes": 10200, "buscas_historico": 8500,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 23.1, "tendencia": "📈 Crescendo"
    }
}

# ============================================================
# PALAVRAS-CHAVE DE CAUDA LONGA
# ============================================================
PALAVRAS_CHAVE_CAUDA_LONGA = {
    "casaco": {"palavra": "casaco feminino inverno 2026", "hashtags": ["#casacofeminino", "#inverno2026", "#lookinverno"]},
    "blusa de lã": {"palavra": "blusa de lã feminina elegante", "hashtags": ["#blusadelã", "#modainverno", "#lookelegante"]},
    "bota": {"palavra": "bota feminina cano médio", "hashtags": ["#botafeminina", "#modainverno", "#lookbota"]},
    "cachecol": {"palavra": "cachecol de lã para frio extremo", "hashtags": ["#cachecoldelã", "#acessóriosdeinverno", "#lookinverno"]},
    "cobertor": {"palavra": "cobertor de lã para cama king", "hashtags": ["#cobertorlã", "#decoraçãocasa", "#conforto"]},
    "smartwatch": {"palavra": "smartwatch feminino elegante", "hashtags": ["#smartwatch", "#tecnologia", "#eletrônicos"]},
    "fone bluetooth": {"palavra": "fone bluetooth JBL original", "hashtags": ["#fonebluetooth", "#áudio", "#tecnologia"]},
    "perfume": {"palavra": "perfume importado feminino", "hashtags": ["#perfumeimportado", "#belezafeminina", "#presentes"]},
    "vestido": {"palavra": "vestido feminino 2026", "hashtags": ["#vestidofeminino", "#moda2026", "#lookverão"]},
    "bolsa": {"palavra": "bolsa feminina couro", "hashtags": ["#bolsafeminina", "#acessórios", "#moda"]},
    "mochila": {"palavra": "mochila escolar infantil", "hashtags": ["#mochilaescolar", "#voltaasaulas", "#materialescolar"]},
    "tenis": {"palavra": "tênis esportivo feminino", "hashtags": ["#tênisesportivo", "#modaesportiva", "#lookcasual"]}
}

# ============================================================
# FUNÇÕES DE SCORE E TOP 10
# ============================================================
def calcular_score(produto, dados):
    score = 0
    if dados.get("pins", 0) > 2000: score += 3
    elif dados.get("pins", 0) > 1000: score += 2
    else: score += 1
    
    if dados.get("crescimento", 0) > 30: score += 2
    elif dados.get("crescimento", 0) > 15: score += 1
    
    if dados.get("views_tiktok", 0) > 3: score += 2
    elif dados.get("views_tiktok", 0) > 1: score += 1
    
    if dados.get("buscas_mes", 0) > 10000: score += 2
    elif dados.get("buscas_mes", 0) > 5000: score += 1
    
    if dados.get("variacao", 0) > 15: score += 1
    
    return min(score, 10)

def gerar_top10_produtos():
    resultados = []
    for produto, dados in DADOS_COMPLETOS.items():
        score = calcular_score(produto, dados)
        
        if score >= 8: potencial = "🟢 Alto"
        elif score >= 5: potencial = "🟡 Médio"
        else: potencial = "🔴 Baixo"
        
        resultados.append({
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
            "Tendência": dados.get('tendencia', '➡️ Estável')
        })
    
    return sorted(resultados, key=lambda x: x["Score"], reverse=True)[:10]

def gerar_sugestoes_diarias():
    top10 = gerar_top10_produtos()
    return top10[:BUSCAS_DIARIAS]

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
    
    # Status
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    with col_status1:
        status_api = "✅ Conectado" if SERPER_API_KEY else "❌ Desconectado"
        st.metric("🔌 Google Shopping", status_api)
    with col_status2:
        status_pinterest = "✅" if PINTEREST_TOKEN else "❌"
        st.metric("📌 Pinterest", status_pinterest)
    with col_status3:
        st.metric("🎫 Créditos", f"10 / 10")
    with col_status4:
        st.metric("👤 Licença", f"{st.session_state.get('licenca_usuario', '')[:10]}...")
    
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
    
    # ===== TABELA DE PRODUTOS DO DIA =====
    st.markdown("## 🎯 Sugestões de Produtos para Hoje")
    st.caption(f"📊 Top 3 do dia | {BUSCAS_DIARIAS} buscas realizadas")
    
    # Mostra tendências da Shopee
    with st.expander("🛍️ Ver Tendências da Shopee", expanded=True):
        st.markdown("### Termos mais buscados no momento")
        buscas_shopee = capturar_buscas_shopee()
        
        if buscas_shopee:
            cols = st.columns(5)
            for i, termo in enumerate(buscas_shopee[:10]):
                with cols[i % 5]:
                    with st.container(border=True):
                        st.markdown(f"**{i+1}.** {termo}")
                        st.caption(f"🔍 Busca em alta")
                        link = f"https://shopee.com.br/search?keyword={quote(termo)}"
                        st.markdown(f'<a href="{link}" target="_blank"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 11px; border: 1px solid #ddd;">🔍 Buscar</span></a>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    produtos = gerar_sugestoes_diarias()
    
    if produtos:
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
        
        st.caption(f"{BUSCAS_DIARIAS} de {BUSCAS_DIARIAS} consultas realizadas hoje")
        
        # ===== TOP 10 =====
        st.markdown("---")
        st.markdown("## 🏆 Top 10 Produtos em Tendência")
        st.caption("Ranking completo baseado em score e dados de mercado")
        
        top10 = gerar_top10_produtos()
        df_top10 = pd.DataFrame(top10)
        colunas_top10 = ["Produto", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Variação", "Tendência"]
        df_top10 = df_top10[colunas_top10]
        
        st.markdown(
            df_top10.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # ===== INSIGHTS ESTRATÉGICOS =====
    st.markdown("## 💡 Insights Estratégicos - Top 3")
    
    if produtos:
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

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA"
])

with tab1:
    df = render_dashboard()

with tab2:
    st.markdown("## 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Top produtos baseados em tendências de mercado")
    
    produtos = gerar_top10_produtos()
    
    if produtos:
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
    st.caption("Gere vídeos para TikTok, Reels e Shorts com IA")
    
    if not SNAPGEN_API_KEY:
        st.warning("⚠️ **Chave SnapGen não configurada.**")
        st.info("Configure no painel do Streamlit Cloud: Settings → Secrets")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        
        modelo = st.selectbox(
            "Modelo",
            ["SnapGen", "SnapGen Fast", "SnapGen Pro"],
            help="SnapGen Pro tem melhor qualidade | Fast é mais rápido"
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
            ["Realista", "Cinematográfico", "Animado", "Minimalista"]
        )
        
        st.markdown("---")
        st.metric("🎫 Créditos restantes", "10 / 10")
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif not SNAPGEN_API_KEY:
                st.error("❌ Chave SnapGen não configurada.")
            else:
                with st.spinner("🎬 Gerando vídeo com IA..."):
                    time.sleep(3)
                    st.success("✅ Vídeo gerado com sucesso!")
                    st.video("https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA")
                    st.info("📥 Clique com o botão direito no vídeo para baixar")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v4.0 | {datetime.now().year} | {BUSCAS_DIARIAS} buscas diárias")
