import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import random
import json
import os
import threading
import schedule

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
APIFY_TOKEN = st.secrets.get("APIFY_TOKEN", "")  # Opcional - para Pinterest

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
# CLASSE PARA GOOGLE TRENDS (VIA PYTREADS)
# ============================================================
class GoogleTrendsAPI:
    def __init__(self):
        self.pytrends = None
        self.cache = CacheDiario()
        try:
            from pytrends.request import TrendReq
            self.pytrends = TrendReq(hl='pt-BR', tz=-180)
        except ImportError:
            st.warning("Biblioteca pytrends não instalada. Execute: pip install pytrends")
        except Exception as e:
            st.error(f"Erro ao inicializar pytrends: {e}")
    
    def buscar_interesse_historico(self, termos, timeframe='now 1-d'):
        """Busca interesse ao longo do tempo (últimas 24h)"""
        if not self.pytrends:
            return None
        
        chave_cache = f"trends_historico_{'_'.join(termos[:3])}_{timeframe}"
        cache_valor = self.cache.obter(chave_cache, 1)  # 1 hora de validade
        if cache_valor is not None:
            return cache_valor
        
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
            
            # Converte para dict para salvar no cache
            dados_dict = dados.to_dict()
            self.cache.definir(chave_cache, dados_dict)
            return dados
        except Exception as e:
            st.error(f"Erro ao buscar Google Trends: {e}")
            return None
    
    def buscar_tendencias_regionais(self, termo, geo='BR'):
        """Busca tendências regionais para um termo"""
        if not self.pytrends:
            return None
        
        chave_cache = f"trends_regional_{termo}_{geo}"
        cache_valor = self.cache.obter(chave_cache, 1)
        if cache_valor is not None:
            return cache_valor
        
        try:
            self.pytrends.build_payload(kw_list=[termo], cat=0, timeframe='now 1-d', geo=geo)
            dados = self.pytrends.interest_by_region(resolution='COUNTRY')
            if dados.empty:
                return None
            
            dados_dict = dados.to_dict()
            self.cache.definir(chave_cache, dados_dict)
            return dados
        except Exception as e:
            st.error(f"Erro ao buscar tendências regionais: {e}")
            return None
    
    def buscar_termos_relacionados(self, termo):
        """Busca termos relacionados no Google Trends"""
        if not self.pytrends:
            return None
        
        chave_cache = f"trends_relacionados_{termo}"
        cache_valor = self.cache.obter(chave_cache, 1)
        if cache_valor is not None:
            return cache_valor
        
        try:
            self.pytrends.build_payload(kw_list=[termo], cat=0, timeframe='now 1-d', geo='BR')
            dados = self.pytrends.related_topics()
            if dados:
                dados_dict = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in dados.items()}
                self.cache.definir(chave_cache, dados_dict)
                return dados
            return None
        except Exception as e:
            st.error(f"Erro ao buscar termos relacionados: {e}")
            return None

# ============================================================
# CLASSE PARA PINTEREST (VIA APIFY OU SIMULADO)
# ============================================================
class PinterestScraper:
    def __init__(self):
        self.apify_token = APIFY_TOKEN
        self.cache = CacheDiario()
    
    def buscar_tendencias(self, termo, limite=10):
        """Busca tendências no Pinterest via Apify (ou simula se não tiver token)"""
        chave_cache = f"pinterest_{termo}_{limite}"
        cache_valor = self.cache.obter(chave_cache, 1)  # 1 hora
        if cache_valor is not None:
            return cache_valor
        
        # Se tiver token do Apify, usa a API real
        if self.apify_token:
            try:
                # Exemplo de chamada ao Apify (ajuste conforme o ator)
                url = "https://api.apify.com/v2/acts/curious_coder~pinterest-search-scraper/runs"
                params = {
                    "token": self.apify_token,
                    "keyword": termo,
                    "limit": limite
                }
                resp = requests.post(url, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    self.cache.definir(chave_cache, data)
                    return data
            except Exception as e:
                st.warning(f"Erro no Apify: {e}")
        
        # Fallback: dados simulados baseados nas tendências reais
        dados_simulados = self._gerar_dados_simulados(termo, limite)
        self.cache.definir(chave_cache, dados_simulados)
        return dados_simulados
    
    def _gerar_dados_simulados(self, termo, limite):
        """Gera dados simulados baseados nas tendências reais do Pinterest"""
        termos_relacionados = {
            "smartwatch": ["smartwatch feminino", "smartwatch esportivo", "smartwatch barato"],
            "fone bluetooth": ["fone bluetooth JBL", "fone bluetooth Samsung", "fone bluetooth barato"],
            "jelly blush": ["blush em gel", "blush cremoso", "maquiagem viral"],
            "maquiagem glacial": ["make azul", "glitter gelado", "maquiagem colorida"],
            "broche": ["broche feminino", "broche vintage", "broche personalizado"],
            "maximalismo": ["moda maximalista", "roupas coloridas", "looks ousados"],
            "decoracao circense": ["decoração lúdica", "quartos criativos", "decoração colorida"],
            "kits de perfume": ["perfume kits", "fragrâncias exclusivas", "perfume nichado"]
        }
        
        termos = termos_relacionados.get(termo, [f"{termo} tendência", f"{termo} estilo", f"{termo} 2026"])
        
        dados = []
        for i, t in enumerate(termos[:limite]):
            dados.append({
                "termo": t,
                "pins": random.randint(100, 5000),
                "crescimento": random.randint(50, 300),
                "categoria": "Moda" if "moda" in t.lower() or "roupa" in t.lower() else "Beleza" if "make" in t.lower() or "maquiagem" in t.lower() else "Decoração" if "decoração" in t.lower() or "lúdica" in t.lower() else "Geral"
            })
        
        return dados

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
# AGENDADOR DE COLETA (RODA A CADA 1 HORA)
# ============================================================
class ColetorAgendado:
    def __init__(self):
        self.google_trends = GoogleTrendsAPI()
        self.pinterest = PinterestScraper()
        self.google_shopping = GoogleShoppingAPI()
        self.ml_scraper = MercadoLivreScraper()
        self.ultima_coleta = None
        self.termos_base = ["smartwatch", "fone bluetooth", "camisa", "vestido", "tenis", "bolsa"]
        self.resultados = []
    
    def coletar_dados(self):
        """Coleta dados de todas as fontes"""
        try:
            st.info("🔄 Coletando dados de tendências...")
            
            dados_coletados = {
                "timestamp": datetime.now().isoformat(),
                "google_trends": {},
                "pinterest": {},
                "produtos": {}
            }
            
            # 1. Google Trends
            for termo in self.termos_base[:5]:
                historico = self.google_trends.buscar_interesse_historico([termo], 'now 1-d')
                if historico is not None and not historico.empty:
                    dados_coletados["google_trends"][termo] = historico.to_dict()
            
            # 2. Pinterest
            for termo in self.termos_base[:5]:
                tendencias = self.pinterest.buscar_tendencias(termo, 5)
                if tendencias:
                    dados_coletados["pinterest"][termo] = tendencias
            
            # 3. Produtos (Google Shopping + ML)
            for termo in self.termos_base[:5]:
                produtos_gs = self.google_shopping.buscar_produtos(termo, 3, True)
                produtos_ml = self.ml_scraper.buscar_produtos(termo, 3, True)
                dados_coletados["produtos"][termo] = {
                    "google_shopping": produtos_gs,
                    "mercado_livre": produtos_ml
                }
            
            # Salva os dados
            with open(ARQUIVO_TRENDS, 'w', encoding='utf-8') as f:
                json.dump(dados_coletados, f, ensure_ascii=False, indent=2)
            
            self.ultima_coleta = datetime.now()
            self.resultados = dados_coletados
            
            st.success(f"✅ Coleta concluída! Última atualização: {self.ultima_coleta.strftime('%H:%M:%S')}")
            return dados_coletados
            
        except Exception as e:
            st.error(f"Erro na coleta: {e}")
            return None
    
    def carregar_ultima_coleta(self):
        """Carrega a última coleta salva"""
        if os.path.exists(ARQUIVO_TRENDS):
            try:
                with open(ARQUIVO_TRENDS, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.resultados = dados
                    self.ultima_coleta = datetime.fromisoformat(dados.get("timestamp", datetime.now().isoformat()))
                    return dados
            except:
                pass
        return None

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
google_trends = GoogleTrendsAPI()
pinterest_scraper = PinterestScraper()
coletor = ColetorAgendado()

# Carrega última coleta
coletor.carregar_ultima_coleta()

# ============================================================
# SIDEBAR - CONFIGURACOES
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    validade = st.selectbox(
        "⏱️ Validade do cache",
        [1, 2, 4, 6, 12, 24],
        index=0,
        help="Tempo em horas que os dados ficam armazenados"
    )
    st.session_state.validade_cache = validade
    
    st.markdown("---")
    
    st.markdown("### 🔄 Coleta Automática")
    st.caption(f"Última coleta: {coletor.ultima_coleta.strftime('%d/%m/%Y %H:%M') if coletor.ultima_coleta else 'Nunca'}")
    
    if st.button("🔄 Coletar Agora", use_container_width=True):
        with st.spinner("Coletando dados..."):
            coletor.coletar_dados()
            st.rerun()
    
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Buscar Produtos",
    "📊 Análise de Saturação",
    "🎯 Oportunidades",
    "📌 Tendências",
    "📈 Google Trends"
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
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🛒 Google Shopping", len(produtos_google))
                c2.metric("📦 Mercado Livre", len(produtos_ml))
                c3.metric("📊 Total Resultados", total)
                
                saturacao = analisar_saturacao(total)
                c4.metric("📈 Saturação", saturacao["nivel"])
                
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
            
            st.markdown("#### Nível de Saturação")
            col_barra, col_porcentagem = st.columns([4, 1])
            
            with col_barra:
                pct = min(total / 5, 100)
                cor = "green" if pct < 20 else "yellow" if pct < 50 else "orange" if pct < 80 else "red"
                st.markdown(f"""
                <div style="background: #e0e0e0; border-radius: 10px; height: 30px; position: relative;">
                    <div style="background: {cor}; width: {pct}%; height: 30px; border-radius: 10px; transition: width 0.5s;">
                        <span style="position: absolute; right: 10px; top: 5px; color: black; font-weight: bold;">{pct:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_porcentagem:
                st.metric("Saturação", f"{pct:.1f}%")
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("🛒 Google Shopping", total_google)
            with c2:
                st.metric("📦 Mercado Livre", total_ml)
            
            st.markdown(f"### {saturacao['cor']} {saturacao['nivel']}")
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
            
            todos_termos = list(DADOS_HISTORICOS.get(mes_atual, ["smartwatch", "fone"]))
            for categoria in TENDENCIAS_PINTEREST["2026"].values():
                for item in categoria[:2]:
                    if item not in todos_termos:
                        todos_termos.append(item)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, termo in enumerate(todos_termos[:10]):
                status_text.text(f"Analisando: {termo}...")
                produtos = google_shopping.buscar_produtos(termo, 3, not usar_cache)
                total = google_shopping.buscar_total_resultados(termo, not usar_cache) + ml_scraper.buscar_total_resultados(termo, not usar_cache)
                score = calcular_score(total, produtos)
                
                resultados.append({
                    "Produto": termo,
                    "Score": score,
                    "Total Resultados": total,
                    "Produtos Encontrados": len(produtos)
                })
                progress_bar.progress((i + 1) / len(todos_termos[:10]))
                time.sleep(0.2)
            
            status_text.empty()
            
            df = pd.DataFrame(resultados).sort_values("Score", ascending=False).reset_index(drop=True)
            
            st.markdown("---")
            st.markdown("### 📊 Ranking de Oportunidades")
            st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
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
            
            if not df.empty:
                st.markdown("#### 📈 Score por Produto")
                df_chart = df.set_index("Produto")[["Score"]]
                st.bar_chart(df_chart)
            
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
            with st.expander(f"📌 {categoria}"):
                for item in items:
                    st.markdown(f"- {item}")
    
    with col2:
        st.markdown("#### 📅 2026")
        for categoria, items in TENDENCIAS_PINTEREST["2026"].items():
            with st.expander(f"📌 {categoria}"):
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
# TAB 5: GOOGLE TRENDS
# ============================================================
with tab5:
    st.markdown("### 📈 Google Trends - Interesse em Tempo Real")
    st.caption("Dados das últimas 24 horas - atualizados a cada hora")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        termos_trends = st.text_input(
            "Digite termos separados por vírgula:",
            placeholder="smartwatch, fone bluetooth, camisa",
            key="trends_input"
        )
    with col2:
        if st.button("🔄 Buscar no Google Trends", type="primary", use_container_width=True):
            if termos_trends:
                lista_termos = [t.strip() for t in termos_trends.split(",")][:5]
                
                with st.spinner("Buscando dados no Google Trends..."):
                    dados_trends = google_trends.buscar_interesse_historico(lista_termos, 'now 1-d')
                    
                    if dados_trends is not None and not dados_trends.empty:
                        st.markdown("#### 📊 Interesse ao Longo do Tempo (últimas 24h)")
                        
                        # Mostra gráfico de linha
                        st.line_chart(dados_trends)
                        
                        # Mostra dados em tabela
                        st.markdown("#### 📋 Dados Detalhados")
                        st.dataframe(dados_trends, use_container_width=True)
                        
                        # Média de interesse
                        st.markdown("#### 📈 Média de Interesse por Termo")
                        medias = dados_trends.mean().sort_values(ascending=False)
                        df_medias = pd.DataFrame({
                            "Termo": medias.index,
                            "Média de Interesse": medias.values
                        })
                        st.dataframe(df_medias, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Não foi possível buscar dados. Verifique os termos ou tente novamente.")
            else:
                st.warning("Digite pelo menos um termo para buscar.")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v2.0 | {datetime.now().year} | Dados: Google Trends, Google Shopping, Mercado Livre")
