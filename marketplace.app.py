import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import random
import json
import os
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTES
# ============================================================
CHAVE_TESTE = "TESTE-AFILIADO-2026"
ARQUIVO_CACHE = "cache_tendencias.json"

# ============================================================
# CONFIGURACAO DAS APIS
# ============================================================
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================
# SISTEMA DE CACHE
# ============================================================
class CacheDiario:
    def __init__(self, arquivo=ARQUIVO_CACHE):
        self.arquivo = arquivo
        self.dados = self.carregar()
    
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
    
    def obter(self, chave, validade_horas=None):
        if validade_horas is None:
            validade_horas = st.session_state.get("validade_cache", 1)
        
        hoje = datetime.now().date().isoformat()
        dados = self.dados.get(chave, {})
        
        if dados and dados.get("data") == hoje:
            try:
                hora_cache = datetime.strptime(dados.get("hora", "00:00"), "%H:%M")
                hora_atual = datetime.now()
                diferenca = (hora_atual - hora_cache.replace(year=hora_atual.year, 
                                                             month=hora_atual.month, 
                                                             day=hora_atual.day)).total_seconds() / 3600
                
                if diferenca < validade_horas:
                    return dados.get("valor")
            except:
                return None
        
        return None
    
    def definir(self, chave, valor):
        hoje = datetime.now()
        self.dados[chave] = {
            "valor": valor,
            "data": hoje.date().isoformat(),
            "hora": hoje.strftime("%H:%M")
        }
        self.salvar()
        return valor
    
    def limpar(self):
        self.dados = {}
        self.salvar()
    
    def info(self):
        total_chaves = len(self.dados)
        hoje = datetime.now().date().isoformat()
        chaves_hoje = sum(1 for k, v in self.dados.items() if v.get("data") == hoje)
        return {
            "total_chaves": total_chaves,
            "chaves_hoje": chaves_hoje,
            "arquivo": self.arquivo
        }

# ============================================================
# CLASSE GOOGLE SHOPPING
# ============================================================
class GoogleShoppingAPI:
    def __init__(self):
        self.api_key = SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
        self.cache = CacheDiario()
    
    def buscar_produtos(self, termo, limite=10, forcar_atualizacao=False):
        if not self.api_key:
            return []
        
        chave_cache = f"produtos_{termo}_{limite}"
        
        if not forcar_atualizacao:
            cache_valor = self.cache.obter(chave_cache)
            if cache_valor is not None:
                return cache_valor
        
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
                    "plataforma": "Google Shopping",
                    "data_consulta": datetime.now().isoformat()
                })
            
            self.cache.definir(chave_cache, produtos)
            return produtos
        except Exception as e:
            st.error(f"Erro no Google Shopping: {e}")
            return []
    
    def buscar_total_resultados(self, termo, forcar_atualizacao=False):
        if not self.api_key:
            return 0
        
        chave_cache = f"total_{termo}"
        
        if not forcar_atualizacao:
            cache_valor = self.cache.obter(chave_cache)
            if cache_valor is not None:
                return cache_valor
        
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
            total = data.get("search_information", {}).get("total_results", 0)
            
            self.cache.definir(chave_cache, total)
            return total
        except:
            return 0

# ============================================================
# CLASSE MERCADO LIVRE
# ============================================================
class MercadoLivreScraper:
    def __init__(self):
        self.base_url = "https://api.mercadolibre.com/sites/MLB/search"
        self.cache = CacheDiario()
    
    def buscar_produtos(self, termo, limite=10, forcar_atualizacao=False):
        chave_cache = f"ml_produtos_{termo}_{limite}"
        
        if not forcar_atualizacao:
            cache_valor = self.cache.obter(chave_cache)
            if cache_valor is not None:
                return cache_valor
        
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
                    "plataforma": "Mercado Livre",
                    "data_consulta": datetime.now().isoformat()
                })
            
            self.cache.definir(chave_cache, produtos)
            return produtos
        except:
            return []
    
    def buscar_total_resultados(self, termo, forcar_atualizacao=False):
        chave_cache = f"ml_total_{termo}"
        
        if not forcar_atualizacao:
            cache_valor = self.cache.obter(chave_cache)
            if cache_valor is not None:
                return cache_valor
        
        try:
            params = {"q": termo, "limit": 1}
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                total = data.get("paging", {}).get("total", 0)
                self.cache.definir(chave_cache, total)
                return total
            return 0
        except:
            return 0

# ============================================================
# DADOS E TENDENCIAS
# ============================================================
TENDENCIAS_PINTEREST = {
    "2025": {
        "beauty": ["jelly blush", "maquiagem glacial", "makeup gotica"],
        "fashion": ["broches", "terno oversized", "rendas", "estilo expedicao"],
        "decor": ["afrodecor", "neo deco", "lar ludico"],
        "gifts": ["entre postais", "infancia retro", "perfume nichado"]
    },
    "2026": {
        "beauty": ["blush em gel", "iluminador furta-cor", "batom metalico"],
        "fashion": ["maximalismo", "moda utilitaria", "acessorios vintage"],
        "decor": ["decoracao circense", "arte etiope", "marmore vermelho"],
        "gifts": ["brinquedos anos 2000", "papelaria criativa", "kits de perfume"]
    }
}

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

# ============================================================
# FUNCOES DE ANALISE
# ============================================================
def analisar_saturacao(total):
    if total == 0:
        return {"nivel": "Sem dados", "cor": "gray", "recomendacao": "Nenhum produto encontrado"}
    elif total < 50:
        return {"nivel": "Baixa saturacao", "cor": "green", "recomendacao": "Otimo! Pouca concorrencia. Aproveite!"}
    elif total < 200:
        return {"nivel": "Saturacao moderada", "cor": "orange", "recomendacao": "Concorrencia razoavel. Ainda ha espaco."}
    elif total < 500:
        return {"nivel": "Saturacao alta", "cor": "red", "recomendacao": "Mercado concorrido. Foque em nichos especificos."}
    else:
        return {"nivel": "Saturacao muito alta", "cor": "darkred", "recomendacao": "Mercado saturado. Busque variacoes menos competitivas."}

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
# FUNCOES DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos - Afiliados")
        st.markdown("### 🔐 Login")
        chave = st.text_input("Digite sua chave de acesso:", type="password")
        if st.button("Entrar", type="primary"):
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

# Inicializa cache e APIs
cache = CacheDiario()
google_shopping = GoogleShoppingAPI()
ml_scraper = MercadoLivreScraper()

# ============================================================
# SIDEBAR - CONFIGURACOES
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/shopping-cart.png", width=60)
    st.markdown("### ⚙️ Configurações")
    
    validade = st.selectbox(
        "⏱️ Validade do cache",
        [1, 2, 4, 6, 12, 24],
        index=0,
        help="Tempo em horas que os dados ficam armazenados"
    )
    st.session_state.validade_cache = validade
    
    if validade == 1:
        st.caption("🔄 Dados atualizados a cada hora")
    elif validade == 24:
        st.caption("📅 Dados atualizados uma vez por dia")
    else:
        st.caption(f"🔄 Dados atualizados a cada {validade} horas")
    
    st.markdown("---")
    
    info_cache = cache.info()
    st.markdown("### 📊 Status do Cache")
    st.caption(f"📁 Total de chaves: {info_cache['total_chaves']}")
    st.caption(f"📅 Chaves de hoje: {info_cache['chaves_hoje']}")
    
    st.markdown("---")
    
    if SERPAPI_KEY:
        st.success("✅ Google Shopping conectado")
    else:
        st.warning("⚠️ SerpApi Key nao configurada")
        st.caption("Obtenha em: serpapi.com")
    
    st.markdown("---")
    
    if st.button("🗑️ Limpar Cache", use_container_width=True):
        cache.limpar()
        st.success("Cache limpo!")
        st.rerun()

# ============================================================
# PAINEL PRINCIPAL
# ============================================================
st.title("🛒 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

# ============================================================
# METRICAS RAPIDAS
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📦 Produtos no Cache", info_cache['total_chaves'])

with col2:
    st.metric("📊 Categorias", len(TENDENCIAS_PINTEREST["2026"]))

with col3:
    mes_atual = datetime.now().month
    st.metric("📅 Mês Atual", f"{mes_atual}/12")

with col4:
    status_api = "✅" if SERPAPI_KEY else "⚠️"
    st.metric("🔌 API Status", status_api)

st.markdown("---")

# ============================================================
# TABS PRINCIPAIS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Buscar Produtos",
    "📊 Análise de Saturação",
    "🎯 Oportunidades",
    "📌 Tendências"
])

# ============================================================
# TAB 1: BUSCAR PRODUTOS
# ============================================================
with tab1:
    st.markdown("### 🔍 Buscar Produtos no Mercado")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        termo_busca = st.text_input(
            "Digite um produto para buscar:",
            placeholder="Ex: smartwatch, fone bluetooth, camisa...",
            label_visibility="collapsed"
        )
    with col2:
        modo = st.radio(
            "Modo:",
            ["Cache", "Real-time"],
            horizontal=True,
            index=0
        )
    
    if termo_busca:
        forcar = (modo == "Real-time")
        
        if st.button("🔍 Buscar", type="primary", use_container_width=True):
            with st.spinner("Buscando dados..."):
                produtos_google = google_shopping.buscar_produtos(termo_busca, 8, forcar)
                total_google = google_shopping.buscar_total_resultados(termo_busca, forcar)
                produtos_ml = ml_scraper.buscar_produtos(termo_busca, 5, forcar)
                total_ml = ml_scraper.buscar_total_resultados(termo_busca, forcar)
                total = total_google + total_ml
                
                st.markdown(f"### 📊 Resultados para '{termo_busca}'")
                
                # Metricas
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🛒 Google Shopping", len(produtos_google))
                c2.metric("📦 Mercado Livre", len(produtos_ml))
                c3.metric("📊 Total Resultados", total)
                
                saturacao = analisar_saturacao(total)
                c4.metric("📈 Saturação", saturacao["nivel"])
                
                st.markdown("---")
                
                # Mostra produtos
                if produtos_google:
                    st.markdown("#### 🛒 Google Shopping")
                    for p in produtos_google[:5]:
                        with st.container(border=True):
                            c1, c2 = st.columns([4, 1])
                            with c1:
                                st.markdown(f"**{p.get('nome', '')[:80]}**")
                                st.markdown(f"💰 {p.get('preco', '')} | 🏪 {p.get('loja', '')}")
                                if p.get('avaliacao'):
                                    st.caption(f"⭐ {p.get('avaliacao')} ({p.get('reviews', 0)} avaliações)")
                            with c2:
                                if p.get("link"):
                                    st.link_button("🔗 Ver", p["link"], use_container_width=True)
                
                if produtos_ml:
                    st.markdown("#### 📦 Mercado Livre")
                    for p in produtos_ml[:3]:
                        with st.container(border=True):
                            c1, c2 = st.columns([4, 1])
                            with c1:
                                st.markdown(f"**{p.get('nome', '')[:80]}**")
                                st.markdown(f"💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                            with c2:
                                if p.get("link"):
                                    st.link_button("🔗 Ver", p["link"], use_container_width=True)

# ============================================================
# TAB 2: ANALISE DE SATURACAO
# ============================================================
with tab2:
    st.markdown("### 📊 Análise de Saturação")
    st.caption("Quanto menor o número de resultados, menor a concorrência")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        termo_sat = st.text_input(
            "Digite um produto para analisar:",
            placeholder="Ex: smartwatch...",
            label_visibility="collapsed",
            key="sat"
        )
    
    if termo_sat and st.button("📊 Analisar", key="btn_sat"):
        with st.spinner("Analisando..."):
            total_google = google_shopping.buscar_total_resultados(termo_sat)
            total_ml = ml_scraper.buscar_total_resultados(termo_sat)
            total = total_google + total_ml
            
            saturacao = analisar_saturacao(total)
            
            # Gráfico de gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = min(total / 5, 100),
                title = {'text': "Nível de Saturação"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': saturacao['cor']},
                    'steps': [
                        {'range': [0, 20], 'color': "lightgreen"},
                        {'range': [20, 50], 'color': "yellow"},
                        {'range': [50, 80], 'color': "orange"},
                        {'range': [80, 100], 'color': "red"}
                    ]
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("🛒 Google Shopping", total_google)
            with c2:
                st.metric("📦 Mercado Livre", total_ml)
            
            st.markdown(f"### {saturacao['nivel']}")
            st.markdown(f"💡 {saturacao['recomendacao']}")

# ============================================================
# TAB 3: OPORTUNIDADES
# ============================================================
with tab3:
    st.markdown("### 🎯 Oportunidades para Afiliados")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Produtos com melhor Score e menor concorrência")
    with col2:
        usar_cache = st.toggle("Usar cache", value=True)
    
    if st.button("🚀 Analisar Oportunidades", type="primary", use_container_width=True):
        with st.spinner("Analisando oportunidades..."):
            mes_atual = datetime.now().month
            resultados = []
            
            # Combina dados históricos e tendências
            todos_termos = list(DADOS_HISTORICOS.get(mes_atual, ["smartwatch", "fone"]))
            for categoria in TENDENCIAS_PINTEREST["2026"].values():
                for item in categoria[:2]:
                    if item not in todos_termos:
                        todos_termos.append(item)
            
            progress = st.progress(0)
            for i, termo in enumerate(todos_termos[:10]):
                produtos = google_shopping.buscar_produtos(termo, 3, not usar_cache)
                total = google_shopping.buscar_total_resultados(termo, not usar_cache) + ml_scraper.buscar_total_resultados(termo, not usar_cache)
                score = calcular_score(total, produtos)
                
                resultados.append({
                    "Produto": termo,
                    "Score": score,
                    "Total Resultados": total,
                    "Produtos Encontrados": len(produtos)
                })
                progress.progress((i + 1) / 10)
                time.sleep(0.2)
            
            df = pd.DataFrame(resultados).sort_values("Score", ascending=False).reset_index(drop=True)
            
            st.markdown("---")
            st.markdown("### 📊 Ranking de Oportunidades")
            st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            # Destaque do melhor
            if not df.empty:
                melhor = df.iloc[0]
                st.success(f"🏆 Melhor oportunidade: **{melhor['Produto']}** (Score: {melhor['Score']}/10)")
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Score": st.column_config.NumberColumn("Score", format="%d"),
                    "Total Resultados": st.column_config.NumberColumn("Total Resultados", format="%d"),
                    "Produtos Encontrados": st.column_config.NumberColumn("Produtos Encontrados", format="%d")
                }
            )
            
            st.info("💡 Foque nos produtos com maior Score e menor número de resultados!")

# ============================================================
# TAB 4: TENDENCIAS
# ============================================================
with tab4:
    st.markdown("### 📌 Tendências Pinterest 2025-2026")
    st.caption("Baseado no relatório Pinterest Predicts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📅 2025")
        for categoria, items in TENDENCIAS_PINTEREST["2025"].items():
            with st.expander(f"📌 {categoria.capitalize()}"):
                for item in items:
                    st.markdown(f"- {item}")
    
    with col2:
        st.markdown("#### 📅 2026")
        for categoria, items in TENDENCIAS_PINTEREST["2026"].items():
            with st.expander(f"📌 {categoria.capitalize()}"):
                for item in items:
                    st.markdown(f"- {item}")
    
    st.markdown("---")
    st.markdown("### 💡 Como usar estas tendências")
    st.markdown("""
    1. Escolha uma tendência da lista acima
    2. Vá para a aba **Buscar Produtos** e pesquise
    3. Analise a saturação e concorrência
    4. Crie conteúdo para redes sociais sobre o produto
    """)

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v1.0 | {datetime.now().year} | Dados: Google Shopping, Mercado Livre")
