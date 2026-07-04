import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import random

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide"
)

# ============================================================
# CONSTANTES
# ============================================================
CHAVE_TESTE = "TESTE-AFILIADO-2026"

# ============================================================
# CONFIGURACAO DAS APIS
# ============================================================
# SerpApi - Cadastre-se em https://serpapi.com (100 buscas gratis/mes)
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================
# CLASSE PARA GOOGLE SHOPPING (VIA SERPAPI)
# ============================================================
class GoogleShoppingAPI:
    def __init__(self):
        self.api_key = SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
    
    def buscar_produtos(self, termo, limite=10):
        """Busca produtos no Google Shopping"""
        if not self.api_key:
            return []
        
        try:
            params = {
                "q": termo,
                "tbm": "shop",
                "api_key": self.api_key,
                "gl": "br",
                "hl": "pt",
                "num": limite,
                "location": "Brazil"
            }
            
            resp = requests.get(self.base_url, params=params, timeout=15)
            data = resp.json()
            
            produtos = []
            for item in data.get("shopping_results", [])[:limite]:
                preco_str = item.get("price", "R$ 0").replace("R$", "").replace(",", ".").strip()
                try:
                    preco_num = float(preco_str.split()[0]) if preco_str else 0
                except:
                    preco_num = 0
                
                produtos.append({
                    "nome": item.get("title", ""),
                    "preco": item.get("price", "R$ 0"),
                    "preco_numero": preco_num,
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "imagem": item.get("thumbnail", ""),
                    "avaliacao": item.get("rating", None),
                    "reviews": item.get("reviews", 0),
                    "plataforma": "Google Shopping"
                })
            
            return produtos
        except Exception as e:
            st.error(f"Erro no Google Shopping: {e}")
            return []
    
    def buscar_total_resultados(self, termo):
        """Retorna o numero total de resultados"""
        if not self.api_key:
            return 0
        
        try:
            params = {
                "q": termo,
                "tbm": "shop",
                "api_key": self.api_key,
                "gl": "br",
                "hl": "pt",
                "num": 1
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            data = resp.json()
            return data.get("search_information", {}).get("total_results", 0)
        except:
            return 0

# ============================================================
# CLASSE PARA MERCADO LIVRE (VIA API PUBLICA)
# ============================================================
class MercadoLivreScraper:
    def __init__(self):
        self.base_url = "https://api.mercadolibre.com/sites/MLB/search"
    
    def buscar_produtos(self, termo, limite=10):
        """Busca produtos via API publica do ML"""
        try:
            params = {
                "q": termo,
                "limit": limite,
                "condition": "new"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            produtos = []
            for item in data.get("results", [])[:limite]:
                produtos.append({
                    "nome": item.get("title", ""),
                    "preco": f"R$ {item.get('price', 0):.2f}",
                    "preco_numero": item.get("price", 0),
                    "loja": "Mercado Livre",
                    "link": item.get("permalink", ""),
                    "vendas": item.get("sold_quantity", 0),
                    "imagem": item.get("thumbnail", ""),
                    "plataforma": "Mercado Livre"
                })
            return produtos
        except:
            return []
    
    def buscar_total_resultados(self, termo):
        try:
            params = {"q": termo, "limit": 1}
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("paging", {}).get("total", 0)
            return 0
        except:
            return 0

# ============================================================
# CLASSE PARA GOOGLE TRENDS (VIA PYTREADS)
# ============================================================
class GoogleTrendsAPI:
    def __init__(self):
        self.pytrends = None
        try:
            from pytrends.request import TrendReq
            self.pytrends = TrendReq(hl='pt-BR', tz=-180)
        except:
            pass
    
    def buscar_tendencias(self, termos, timeframe='now 7-d'):
        """Busca interesse ao longo do tempo"""
        if not self.pytrends:
            return None
        
        try:
            self.pytrends.build_payload(
                kw_list=termos[:5],
                cat=0,
                timeframe=timeframe,
                geo='BR'
            )
            dados = self.pytrends.interest_over_time()
            if dados.empty:
                return None
            if 'isPartial' in dados.columns:
                dados = dados.drop('isPartial', axis=1)
            return dados
        except:
            return None

# ============================================================
# FUNCOES DE ANALISE
# ============================================================
def analisar_saturacao(total):
    if total == 0:
        return {"nivel": "Sem dados", "recomendacao": "Nenhum produto encontrado"}
    elif total < 50:
        return {"nivel": "Baixa saturacao", "recomendacao": "Otimo! Pouca concorrencia. Aproveite!"}
    elif total < 200:
        return {"nivel": "Saturacao moderada", "recomendacao": "Concorrencia razoavel. Ainda ha espaco."}
    elif total < 500:
        return {"nivel": "Saturacao alta", "recomendacao": "Mercado concorrido. Foque em nichos especificos."}
    else:
        return {"nivel": "Saturacao muito alta", "recomendacao": "Mercado saturado. Busque variacoes menos competitivas."}

def calcular_score(total_resultados, produtos):
    if total_resultados <= 0:
        return 0
    
    score = 0
    
    if total_resultados < 50:
        score += 4
    elif total_resultados < 200:
        score += 3
    elif total_resultados < 500:
        score += 1
    
    if produtos:
        score += 2
        
        precos = [p.get("preco_numero", 0) for p in produtos if p.get("preco_numero", 0) > 0]
        if precos:
            preco_medio = sum(precos) / len(precos)
            if 30 <= preco_medio <= 150:
                score += 2
            elif 150 < preco_medio <= 300:
                score += 1
    
    return min(score, 10)

# ============================================================
# DADOS HISTORICOS (FALLBACK)
# ============================================================
DADOS_HISTORICOS = {
    1: ["smartwatch", "fone bluetooth", "material escolar", "mochila", "tenis"],
    2: ["fantasia", "biquini", "sungas", "protetor solar", "fone"],
    3: ["kit praia", "canga", "chapeu", "oculos sol", "smartwatch"],
    4: ["ovo pascoa", "chocolate", "cesta", "fone", "smartwatch"],
    5: ["dia das maes", "perfume", "bolsa", "vestido", "smartwatch"],
    6: ["dia dos namorados", "perfume", "vinho", "chocolate", "fone"],
    7: ["casaco", "bota", "cachecol", "fone", "smartwatch"],
    8: ["dia dos pais", "relogio", "cinto", "ferramenta", "smartwatch"],
    9: ["camisa", "calca", "vestido", "tenis", "smartwatch"],
    10: ["fantasia halloween", "decoracao", "brinquedo", "fone", "smartwatch"],
    11: ["black friday", "eletronico", "celular", "tv", "smartwatch"],
    12: ["natal", "presente", "arvore", "decoracao", "smartwatch"]
}

DATAS_COMEMORATIVAS = {
    (1, 1): "Ano Novo",
    (2, 14): "Carnaval",
    (3, 8): "Dia da Mulher",
    (5, 11): "Dia das Maes",
    (6, 12): "Dia dos Namorados",
    (8, 10): "Dia dos Pais",
    (10, 12): "Dia das Criancas",
    (10, 31): "Halloween",
    (11, 25): "Black Friday",
    (12, 25): "Natal"
}

# ============================================================
# FUNCOES DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("Minerador de Produtos - Login")
        chave = st.text_input("Digite sua chave de acesso:", type="password")
        if st.button("Entrar"):
            if chave == CHAVE_TESTE:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Chave invalida. Tente novamente.")
        st.stop()

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

st.title("Minerador de Produtos - Afiliados")
st.caption("Busca em Google Shopping + Mercado Livre + Google Trends")

# Status das APIs no sidebar
with st.sidebar:
    st.markdown("### Status das APIs")
    
    if SERPAPI_KEY:
        st.success("Google Shopping (SerpApi) - OK")
    else:
        st.warning("SerpApi Key nao configurada")
        st.caption("Obtenha em: serpapi.com")
    
    st.markdown("---")
    st.markdown("**Fontes de dados:**")
    st.markdown("""
    - Google Shopping (SerpApi)
    - Mercado Livre (publico)
    - Google Trends (pytrends)
    - Dados historicos
    """)

# Inicializa as APIs
google_shopping = GoogleShoppingAPI()
ml_scraper = MercadoLivreScraper()
trends = GoogleTrendsAPI()

st.markdown("---")

# ===== SECAO 1: BUSCAR PRODUTOS =====
st.markdown("## Buscar Produtos")

termo_busca = st.text_input("Digite um produto:", placeholder="Ex: smartwatch, fone bluetooth...")

if termo_busca and st.button("Buscar", type="primary"):
    st.markdown(f"### Resultados para '{termo_busca}'")
    
    with st.spinner("Buscando no Google Shopping..."):
        produtos_google = google_shopping.buscar_produtos(termo_busca, 8)
        total_google = google_shopping.buscar_total_resultados(termo_busca)
    
    with st.spinner("Buscando no Mercado Livre..."):
        produtos_ml = ml_scraper.buscar_produtos(termo_busca, 5)
        total_ml = ml_scraper.buscar_total_resultados(termo_busca)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Google Shopping", f"{len(produtos_google)} produtos")
    with col2:
        st.metric("Mercado Livre", f"{len(produtos_ml)} produtos")
    with col3:
        total = total_google + total_ml
        st.metric("Total Resultados", total)
    
    st.markdown("---")
    
    saturacao = analisar_saturacao(total)
    st.markdown(f"### {saturacao['nivel']}")
    st.markdown(f"{saturacao['recomendacao']}")
    
    st.markdown("---")
    
    if produtos_google:
        st.markdown("#### Google Shopping")
        for p in produtos_google[:5]:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{p.get('nome', '')[:80]}**")
                    st.markdown(f"Preco: {p.get('preco', '')} | Loja: {p.get('loja', '')}")
                    if p.get('avaliacao'):
                        st.caption(f"Avaliacao: {p.get('avaliacao')} ({p.get('reviews', 0)} reviews)")
                with col2:
                    if p.get("link"):
                        st.link_button("Ver", p["link"], use_container_width=True)
    
    if produtos_ml:
        st.markdown("#### Mercado Livre")
        for p in produtos_ml[:3]:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{p.get('nome', '')[:80]}**")
                    st.markdown(f"Preco: {p.get('preco', '')} | Vendas: {p.get('vendas', 0)}")
                with col2:
                    if p.get("link"):
                        st.link_button("Ver", p["link"], use_container_width=True)

st.markdown("---")

# ===== SECAO 2: ANALISE DE SATURACAO =====
st.markdown("## Analise de saturacao")

termo_sat = st.text_input("Digite um produto para analisar:", placeholder="Ex: smartwatch...", key="sat")

if termo_sat and st.button("Analisar", key="btn_sat"):
    with st.spinner("Analisando..."):
        total_google = google_shopping.buscar_total_resultados(termo_sat)
        total_ml = ml_scraper.buscar_total_resultados(termo_sat)
        total = total_google + total_ml
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Google Shopping", total_google)
        with col2:
            st.metric("Mercado Livre", total_ml)
        
        saturacao = analisar_saturacao(total)
        st.markdown(f"### {saturacao['nivel']}")
        st.markdown(f"{saturacao['recomendacao']}")

st.markdown("---")

# ===== SECAO 3: SUGESTOES POR DATA =====
st.markdown("## Sugestoes por Data")

mes_atual = datetime.now().month
dados_mes = DADOS_HISTORICOS.get(mes_atual, ["smartwatch", "fone"])

hoje = datetime.now()
evento_hoje = None
for (m, d), nome in DATAS_COMEMORATIVAS.items():
    if m == hoje.month and d == hoje.day:
        evento_hoje = nome
        break

if evento_hoje:
    st.success(f"Hoje e {evento_hoje}!")
else:
    st.info("Nenhuma data comemorativa hoje.")

st.markdown("#### Produtos em tendencia para este mes")
for t in dados_mes[:6]:
    st.markdown(f"- {t}")

st.markdown("---")

# ===== SECAO 4: MINERADOR PRO =====
st.markdown("## Minerador Pro")

if st.button("Analisar Oportunidades", type="primary"):
    with st.spinner("Analisando oportunidades..."):
        resultados = []
        
        for termo in list(DADOS_HISTORICOS.get(mes_atual, ["smartwatch", "fone"]))[:8]:
            produtos = google_shopping.buscar_produtos(termo, 3)
            total = google_shopping.buscar_total_resultados(termo) + ml_scraper.buscar_total_resultados(termo)
            score = calcular_score(total, produtos)
            
            resultados.append({
                "Produto": termo,
                "Score": score,
                "Total Resultados": total,
                "Produtos Encontrados": len(produtos)
            })
            time.sleep(0.5)
        
        df = pd.DataFrame(resultados).sort_values("Score", ascending=False).reset_index(drop=True)
        
        st.markdown("### Oportunidades")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.info("Foque nos produtos com maior Score e menor numero de resultados!")

st.markdown("---")

# ===== CONFIGURACAO =====
with st.expander("Configuracao da SerpApi"):
    st.markdown("""
    **Como obter sua chave SerpApi:**
    
    1. Acesse [SerpApi](https://serpapi.com)
    2. Crie uma conta gratuita (100 buscas/mes)
    3. Copie sua API Key
    4. Adicione no arquivo `.streamlit/secrets.toml`:
    
    ```toml
    SERPAPI_KEY = "sua_chave_aqui"
