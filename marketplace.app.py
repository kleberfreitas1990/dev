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

# ============================================================
# SUPRIMIR WARNINGS
# ============================================================
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

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
ARQUIVO_TRENDS = "dados_trends.json"

# ============================================================
# CONFIGURACAO DAS APIS
# ============================================================
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")
APIFY_TOKEN = st.secrets.get("APIFY_TOKEN", "")

# ============================================================
# LIMITE DE BUSCAS POR DIA
# ============================================================
class ControleBuscas:
    def __init__(self):
        self.arquivo = "controle_buscas.json"
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
    
    def pode_buscar(self):
        hoje = datetime.now().date().isoformat()
        if hoje not in self.dados:
            self.dados[hoje] = {"buscas": 0, "termos": []}
            self.salvar()
        
        if self.dados[hoje]["buscas"] >= 3:
            return False, f"Limite de 3 buscas/dia atingido. Aguarde amanhã."
        
        return True, f"Restam {3 - self.dados[hoje]['buscas']} buscas hoje"
    
    def registrar_busca(self, termo):
        hoje = datetime.now().date().isoformat()
        if hoje not in self.dados:
            self.dados[hoje] = {"buscas": 0, "termos": []}
        
        self.dados[hoje]["buscas"] += 1
        self.dados[hoje]["termos"].append({
            "termo": termo,
            "hora": datetime.now().strftime("%H:%M")
        })
        self.salvar()
    
    def get_buscas_hoje(self):
        hoje = datetime.now().date().isoformat()
        if hoje in self.dados:
            return self.dados[hoje]["buscas"]
        return 0
    
    def get_termos_hoje(self):
        hoje = datetime.now().date().isoformat()
        if hoje in self.dados:
            return [t["termo"] for t in self.dados[hoje]["termos"]]
        return []

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
            validade_horas = st.session_state.get("validade_cache", 24)
        
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
        self.controle = ControleBuscas()
    
    def buscar_produtos(self, termo, limite=10, forcar_atualizacao=False):
        if not self.api_key:
            return []
        
        chave_cache = f"produtos_{termo}_{limite}"
        
        if not forcar_atualizacao:
            cache_valor = self.cache.obter(chave_cache, 24)
            if cache_valor is not None:
                return cache_valor
        
        pode, mensagem = self.controle.pode_buscar()
        if not pode:
            st.warning(f"⚠️ {mensagem}")
            return self._buscar_cache_fallback(termo)
        
        try:
            params = {
                "q": termo,
                "tbm": "shop",
                "api_key": self.api_key,
                "gl": "br",
                "hl": "pt",
                "num": limite,
                "location": "Brazil",
                "device": "desktop"
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
            
            self.controle.registrar_busca(termo)
            self.cache.definir(chave_cache, produtos)
            return produtos
            
        except Exception as e:
            st.error(f"Erro no Google Shopping: {e}")
            return self._buscar_cache_fallback(termo)
    
    def _buscar_cache_fallback(self, termo):
        chave_cache = f"produtos_{termo}_10"
        cache_valor = self.cache.obter(chave_cache, 720)
        if cache_valor is not None:
            st.info("📌 Usando dados em cache (limite de buscas atingido)")
            return cache_valor
        return []
    
    def buscar_total_resultados(self, termo, forcar_atualizacao=False):
        if not self.api_key:
            return 0
        
        chave_cache = f"total_{termo}"
        
        if not forcar_atualizacao:
            cache_valor = self.cache.obter(chave_cache, 24)
            if cache_valor is not None:
                return cache_valor
        
        pode, _ = self.controle.pode_buscar()
        if not pode:
            return self.cache.obter(chave_cache, 720) or 0
        
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
            
            self.controle.registrar_busca(termo)
            self.cache.definir(chave_cache, total)
            return total
        except:
            return self.cache.obter(chave_cache, 720) or 0
    
    def get_status_buscas(self):
        return {
            "hoje": self.controle.get_buscas_hoje(),
            "limite": 3,
            "restam": 3 - self.controle.get_buscas_hoje(),
            "termos": self.controle.get_termos_hoje()
        }

# ============================================================
# CLASSE GOOGLE TRENDS
# ============================================================
class GoogleTrendsAPI:
    def __init__(self):
        self.api_key = SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
        self.cache = CacheDiario()
        self.controle = ControleBuscas()
    
    def buscar_interesse_historico(self, termo, timeframe='now 1-d'):
        if not self.api_key:
            return None
        
        chave_cache = f"trends_{termo}_{timeframe}"
        cache_valor = self.cache.obter(chave_cache, 24)
        if cache_valor is not None:
            return cache_valor
        
        pode, _ = self.controle.pode_buscar()
        if not pode:
            return self._buscar_cache_fallback(termo)
        
        try:
            params = {
                "q": termo,
                "engine": "google_trends",
                "data_type": "TIMESERIES",
                "api_key": self.api_key,
                "geo": "BR",
                "timeframe": timeframe,
                "hl": "pt"
            }
            
            resp = requests.get(self.base_url, params=params, timeout=15)
            data = resp.json()
            
            if "interest_over_time" in data:
                timeline = data["interest_over_time"].get("timeline_data", [])
                if timeline:
                    dados = []
                    for item in timeline:
                        valores = item.get("value", [0])
                        data_str = item.get("date", "")
                        try:
                            data_dt = pd.to_datetime(data_str, format='%Y-%m-%d %H:%M')
                        except:
                            data_dt = pd.to_datetime(data_str)
                        
                        dados.append({
                            "date": data_dt,
                            termo: int(valores[0]) if valores else 0
                        })
                    
                    df = pd.DataFrame(dados)
                    if not df.empty:
                        df = df.set_index('date')
                        self.controle.registrar_busca(termo)
                        self.cache.definir(chave_cache, df.to_dict())
                        return df
            
            return None
        except Exception as e:
            return self._buscar_cache_fallback(termo)
    
    def _buscar_cache_fallback(self, termo):
        chave_cache = f"trends_{termo}_now 1-d"
        cache_valor = self.cache.obter(chave_cache, 720)
        if cache_valor is not None:
            return cache_valor
        return None

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
        "Beleza": ["jelly blush", "maquiagem glacial", "makeup gotica"],
        "Moda": ["broches", "terno oversized", "rendas", "estilo expedicao"],
        "Decoracao": ["afrodecor", "neo deco", "lar ludico"],
        "Presentes": ["entre postais", "infancia retro", "perfume nichado"]
    },
    "2026": {
        "Beleza": ["blush em gel", "iluminador furta-cor", "batom metalico"],
        "Moda": ["maximalismo", "moda utilitaria", "acessorios vintage"],
        "Decoracao": ["decoracao circense", "arte etiope", "marmore vermelho"],
        "Presentes": ["brinquedos anos 2000", "papelaria criativa", "kits de perfume"]
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
# SUGESTOES PRE-CALCULADAS (EXIBIDAS DIRETAMENTE)
# ============================================================
SUGESTOES_PRODUTOS = [
    {
        "produto": "jelly blush",
        "categoria": "Beleza",
        "oportunidade": "🔥 Excelente",
        "motivo": "Tendência Pinterest +130% em 2025",
        "cor": "green",
        "link": "https://shopee.com.br/search?keyword=jelly%20blush"
    },
    {
        "produto": "broche personalizado",
        "categoria": "Moda",
        "oportunidade": "🔥 Excelente",
        "motivo": "Tendência Pinterest +110% em 2025",
        "cor": "green",
        "link": "https://shopee.com.br/search?keyword=broche%20personalizado"
    },
    {
        "produto": "kits de perfume",
        "categoria": "Presentes",
        "oportunidade": "🚀 Alta",
        "motivo": "Crescimento +500% no Pinterest 2026",
        "cor": "green",
        "link": "https://shopee.com.br/search?keyword=kit%20perfume"
    },
    {
        "produto": "blush em gel",
        "categoria": "Beleza",
        "oportunidade": "🚀 Alta",
        "motivo": "Tendência Pinterest 2026 em alta",
        "cor": "green",
        "link": "https://shopee.com.br/search?keyword=blush%20em%20gel"
    },
    {
        "produto": "decoracao circense",
        "categoria": "Decoracao",
        "oportunidade": "🚀 Alta",
        "motivo": "Tendência Pinterest +130% em 2026",
        "cor": "green",
        "link": "https://shopee.com.br/search?keyword=decoracao%20circense"
    },
    {
        "produto": "terno oversized",
        "categoria": "Moda",
        "oportunidade": "⭐ Boa",
        "motivo": "Tendência Pinterest +225% em 2025",
        "cor": "yellow",
        "link": "https://shopee.com.br/search?keyword=terno%20oversized"
    },
    {
        "produto": "smartwatch",
        "categoria": "Eletrônicos",
        "oportunidade": "📊 Média",
        "motivo": "Mercado consolidado, ainda com espaço",
        "cor": "orange",
        "link": "https://shopee.com.br/search?keyword=smartwatch"
    },
    {
        "produto": "fone bluetooth",
        "categoria": "Eletrônicos",
        "oportunidade": "📊 Média",
        "motivo": "Alta demanda, concorrência moderada",
        "cor": "orange",
        "link": "https://shopee.com.br/search?keyword=fone%20bluetooth"
    },
    {
        "produto": "camisa feminina",
        "categoria": "Moda",
        "oportunidade": "📊 Média",
        "motivo": "Sempre em alta, nichos específicos",
        "cor": "orange",
        "link": "https://shopee.com.br/search?keyword=camisa%20feminina"
    },
    {
        "produto": "cadeira gamer",
        "categoria": "Casa",
        "oportunidade": "📊 Média",
        "motivo": "Mercado em crescimento",
        "cor": "orange",
        "link": "https://shopee.com.br/search?keyword=cadeira%20gamer"
    }
]

# ============================================================
# FUNCOES DE ANALISE
# ============================================================
def analisar_saturacao(total):
    if total == 0:
        return {"nivel": "Sem dados", "cor": "gray", "recomendacao": "Nenhum produto encontrado"}
    elif total < 50:
        return {"nivel": "Baixa saturacao", "cor": "🟢", "recomendacao": "Otimo! Pouca concorrencia. Aproveite!"}
    elif total < 200:
        return {"nivel": "Saturacao moderada", "cor": "🟡", "recomendacao": "Concorrencia razoavel. Ainda ha espaco."}
    elif total < 500:
        return {"nivel": "Saturacao alta", "cor": "🟠", "recomendacao": "Mercado concorrido. Foque em nichos especificos."}
    else:
        return {"nivel": "Saturacao muito alta", "cor": "🔴", "recomendacao": "Mercado saturado. Busque variacoes menos competitivas."}

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

cache = CacheDiario()
google_shopping = GoogleShoppingAPI()
ml_scraper = MercadoLivreScraper()
google_trends = GoogleTrendsAPI()
controle = ControleBuscas()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    validade = st.selectbox(
        "⏱️ Validade do cache",
        [1, 2, 4, 6, 12, 24],
        index=4,
        help="Tempo em horas que os dados ficam armazenados"
    )
    st.session_state.validade_cache = validade
    
    st.markdown("---")
    
    status_buscas = google_shopping.get_status_buscas()
    st.markdown("### 🔢 Buscas SerpApi Hoje")
    st.caption(f"📊 {status_buscas['hoje']} de {status_buscas['limite']} usadas")
    
    if status_buscas['restam'] > 0:
        st.success(f"✅ {status_buscas['restam']} buscas restantes")
    else:
        st.warning("⚠️ Limite de 3 buscas/dia atingido")
    
    if status_buscas['termos']:
        st.caption(f"📌 Termos: {', '.join(status_buscas['termos'])}")
    
    st.markdown("---")
    
    st.markdown("### 🔌 Status das APIs")
    if SERPAPI_KEY:
        st.success("✅ SerpApi configurada")
        st.caption("3 buscas/dia")
    else:
        st.warning("⚠️ SerpApi nao configurada")
    
    st.markdown("---")
    
    info_cache = cache.info()
    st.markdown("### 📊 Cache")
    st.caption(f"📁 Chaves: {info_cache['total_chaves']}")
    st.caption(f"📅 Hoje: {info_cache['chaves_hoje']}")
    
    st.markdown("---")
    
    if st.button("🗑️ Limpar Cache", width='stretch'):
        cache.limpar()
        st.success("Cache limpo!")
        st.rerun()

# ============================================================
# PAINEL PRINCIPAL
# ============================================================
st.title("🛒 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📦 Cache", info_cache['total_chaves'])

with col2:
    st.metric("📊 Categorias", len(TENDENCIAS_PINTEREST["2026"]))

with col3:
    mes_atual = datetime.now().month
    st.metric("📅 Mês", f"{mes_atual}/12")

with col4:
    buscas_hoje = controle.get_buscas_hoje()
    st.metric("🔍 Buscas", f"{buscas_hoje}/3")

st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "💡 Sugestões de Produtos",
    "🔍 Buscar Produtos",
    "📈 Google Trends"
])

# ============================================================
# TAB 1: SUGESTOES (VISIVEL SEM EXPANDIR)
# ============================================================
with tab1:
    st.markdown("### 🎯 Produtos Recomendados para Afiliados")
    st.caption("Baseado em tendências Pinterest 2025-2026 e dados históricos")
    
    status_buscas = google_shopping.get_status_buscas()
    if status_buscas['restam'] > 0:
        st.info(f"📌 {status_buscas['restam']} buscas disponíveis hoje para detalhamento")
    else:
        st.warning("⚠️ Limite de buscas atingido. Use o cache para ver detalhes.")
    
    st.markdown("---")
    
    # Exibe produtos em cards (sem expandir)
    for p in SUGESTOES_PRODUTOS:
        cor = p['cor']
        oportunidade = p['oportunidade']
        
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])
            
            with col1:
                st.markdown(f"**{p['produto']}**")
                st.caption(f"📂 {p['categoria']}")
            
            with col2:
                if "🔥" in oportunidade:
                    st.markdown(f"🟢 **{oportunidade}**")
                elif "🚀" in oportunidade:
                    st.markdown(f"🟢 **{oportunidade}**")
                elif "⭐" in oportunidade:
                    st.markdown(f"🟡 **{oportunidade}**")
                else:
                    st.markdown(f"🟠 **{oportunidade}**")
            
            with col3:
                st.caption(p['motivo'])
            
            with col4:
                # Botão para pesquisar na Shopee
                if st.button(f"🔍 Ver na Shopee", key=f"shopee_{p['produto']}"):
                    # Abre o link em nova aba
                    st.markdown(f'<a href="{p["link"]}" target="_blank">Abrir Shopee</a>', unsafe_allow_html=True)
                
                # Botão para buscar dados reais
                if status_buscas['restam'] > 0:
                    if st.button(f"📊 Detalhar", key=f"det_{p['produto']}"):
                        st.session_state.termo_busca = p['produto']
                        st.session_state.aba_busca = "buscar"
                        st.rerun()
    
    # Dicas rápidas
    st.markdown("---")
    st.markdown("### 💡 Dicas para Afiliados")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **🔥 Melhores Oportunidades**
        - Jelly Blush (+130% Pinterest)
        - Broches (+110% Pinterest)
        - Kits de Perfume (+500% Pinterest)
        - Blush em Gel (Tendência 2026)
        """)
    with col2:
        st.success("""
        **📈 Como usar estas sugestões**
        1. Escolha um produto da lista
        2. Clique em "Ver na Shopee" para ver produtos reais
        3. Clique em "Detalhar" para ver dados de mercado
        4. Crie conteúdo para redes sociais
        """)

# ============================================================
# TAB 2: BUSCAR PRODUTOS
# ============================================================
with tab2:
    st.markdown("### 🔍 Buscar Produtos no Mercado")
    st.caption("Dados REAIS do Google Shopping via SerpApi (3 buscas/dia)")
    
    # Verifica se veio da aba de sugestões
    termo_inicial = st.session_state.get("termo_busca", "")
    if termo_inicial:
        st.info(f"🔍 Buscando: {termo_inicial}")
        # Limpa após usar
        st.session_state.termo_busca = ""
    
    status_buscas = google_shopping.get_status_buscas()
    if status_buscas['restam'] <= 0:
        st.warning("⚠️ Limite de 3 buscas/dia atingido. Aguarde amanhã.")
    else:
        st.info(f"📌 {status_buscas['restam']} buscas disponíveis hoje")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        termo_busca = st.text_input(
            "Digite um produto:",
            value=termo_inicial,
            placeholder="Ex: smartwatch, jelly blush...",
            label_visibility="collapsed",
            key="busca_input"
        )
    with col2:
        usar_cache = st.checkbox("Usar cache", value=True, key="cache_checkbox_busca")
    
    if termo_busca:
        forcar = not usar_cache
        
        if st.button("🔍 Buscar", type="primary", width='stretch'):
            with st.spinner("Buscando dados..."):
                produtos_google = google_shopping.buscar_produtos(termo_busca, 8, forcar)
                total_google = google_shopping.buscar_total_resultados(termo_busca, forcar)
                
                st.markdown(f"### 📊 Resultados para '{termo_busca}'")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total de Resultados", total_google)
                with col2:
                    st.metric("Produtos Exibidos", len(produtos_google))
                
                status_atual = google_shopping.get_status_buscas()
                st.caption(f"🔍 Buscas usadas hoje: {status_atual['hoje']}/3")
                
                st.markdown("---")
                
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
                                    st.link_button("🔗 Ver", p["link"], width='stretch')
                else:
                    st.warning("Nenhum produto encontrado.")

# ============================================================
# TAB 3: GOOGLE TRENDS
# ============================================================
with tab3:
    st.markdown("### 📈 Google Trends")
    st.caption("Dados REAIS via SerpApi (3 buscas/dia)")
    
    status_buscas = google_shopping.get_status_buscas()
    if status_buscas['restam'] <= 0:
        st.warning("⚠️ Limite de 3 buscas/dia atingido.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        termo_trends = st.text_input(
            "Digite um termo:",
            placeholder="smartwatch",
            label_visibility="collapsed",
            key="trends_input"
        )
    with col2:
        if st.button("🔄 Buscar Trends", type="primary", width='stretch'):
            if termo_trends:
                with st.spinner("Buscando dados..."):
                    dados_trends = google_trends.buscar_interesse_historico(termo_trends, 'now 1-d')
                    
                    if dados_trends is not None and not dados_trends.empty:
                        st.markdown("#### 📊 Interesse (últimas 24h)")
                        st.line_chart(dados_trends)
                        
                        st.markdown("#### 📋 Dados")
                        st.dataframe(dados_trends, width='stretch')
                        
                        st.success(f"✅ Dados para '{termo_trends}'")
                        
                        status_atual = google_shopping.get_status_buscas()
                        st.caption(f"🔍 Buscas hoje: {status_atual['hoje']}/3")
                    else:
                        st.warning("Não foi possível buscar dados.")
            else:
                st.warning("Digite um termo.")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v2.0 | 3 buscas/dia SerpApi")
