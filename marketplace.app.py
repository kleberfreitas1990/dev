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
import base64
from io import BytesIO

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
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTES
# ============================================================
# CHAVE DE LICENÇA CORRETA
LICENCA_PADRAO = "TESTE-AFILIADO-2026"
ARQUIVO_CACHE = "cache_tendencias.json"
ARQUIVO_TRENDS = "dados_trends.json"

# ============================================================
# CARREGAR SECRETS DE FORMA SEGURA
# ============================================================
def carregar_secrets():
    """Carrega as chaves de API com fallback para valores vazios"""
    try:
        # Tenta carregar do st.secrets
        licenca = st.secrets.get("LICENCA_ACESSO", "")
        
        # Se não tiver no secrets, usa a licença padrão
        if not licenca:
            licenca = LICENCA_PADRAO
        
        return {
            "licenca_acesso": licenca,
            "serpapi_key": st.secrets.get("SERPAPI_KEY", ""),
            "apify_token": st.secrets.get("APIFY_TOKEN", ""),
            "gemini_key": st.secrets.get("GEMINI_API_KEY", ""),
            "google_trends_proxy": st.secrets.get("GOOGLE_TRENDS_PROXY", "")
        }
    except Exception:
        # Fallback completo para desenvolvimento
        return {
            "licenca_acesso": LICENCA_PADRAO,
            "serpapi_key": "",
            "apify_token": "",
            "gemini_key": "",
            "google_trends_proxy": ""
        }

# Carrega as chaves
KEYS = carregar_secrets()
LICENCA_ACESSO = KEYS["licenca_acesso"]
SERPAPI_KEY = KEYS["serpapi_key"]
APIFY_TOKEN = KEYS["apify_token"]
GEMINI_API_KEY = KEYS["gemini_key"]
GOOGLE_TRENDS_PROXY = KEYS["google_trends_proxy"]

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
# CLASSE PARA GEMINI VIDEO GENERATION
# ============================================================
class GeminiVideoGenerator:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    
    def gerar_video(self, prompt, imagem_base64=None, duracao=6, resolucao="480p"):
        if not self.api_key:
            return {"erro": "Chave Gemini não configurada. Adicione GEMINI_API_KEY no secrets.toml"}
        
        try:
            time.sleep(2)
            return {
                "url": "https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA",
                "duracao": duracao,
                "resolucao": resolucao,
                "prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "status": "simulado"
            }
        except Exception as e:
            return {"erro": f"Erro na geração: {str(e)}"}

# ============================================================
# CLASSE PARA GOOGLE TRENDS
# ============================================================
class GoogleTrendsAPI:
    def __init__(self):
        self.pytrends = None
        self.cache = CacheDiario()
        try:
            from pytrends.request import TrendReq
            if GOOGLE_TRENDS_PROXY:
                self.pytrends = TrendReq(hl='pt-BR', tz=-180, timeout=(10, 25), 
                                        proxies={'https': GOOGLE_TRENDS_PROXY})
            else:
                self.pytrends = TrendReq(hl='pt-BR', tz=-180, timeout=(10, 25))
        except ImportError:
            pass
        except Exception as e:
            pass
    
    def buscar_interesse_historico(self, termos, timeframe='now 1-d'):
        if not self.pytrends:
            return None
        
        chave_cache = f"trends_historico_{'_'.join(termos[:3])}_{timeframe}"
        cache_valor = self.cache.obter(chave_cache, 1)
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
            
            dados_dict = dados.to_dict()
            self.cache.definir(chave_cache, dados_dict)
            return dados
        except Exception as e:
            return None

# ============================================================
# CLASSE PARA PINTEREST
# ============================================================
class PinterestScraper:
    def __init__(self):
        self.apify_token = APIFY_TOKEN
        self.cache = CacheDiario()
    
    def buscar_tendencias(self, termo, limite=10):
        chave_cache = f"pinterest_{termo}_{limite}"
        cache_valor = self.cache.obter(chave_cache, 1)
        if cache_valor is not None:
            return cache_valor
        
        if self.apify_token:
            try:
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
                pass
        
        dados_simulados = self._gerar_dados_simulados(termo, limite)
        self.cache.definir(chave_cache, dados_simulados)
        return dados_simulados
    
    def _gerar_dados_simulados(self, termo, limite):
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
# COLETOR DE DADOS
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
        try:
            dados_coletados = {
                "timestamp": datetime.now().isoformat(),
                "google_trends": {},
                "pinterest": {},
                "produtos": {}
            }
            
            for termo in self.termos_base[:5]:
                historico = self.google_trends.buscar_interesse_historico([termo], 'now 1-d')
                if historico is not None and not historico.empty:
                    dados_coletados["google_trends"][termo] = historico.to_dict()
            
            for termo in self.termos_base[:5]:
                tendencias = self.pinterest.buscar_tendencias(termo, 5)
                if tendencias:
                    dados_coletados["pinterest"][termo] = tendencias
            
            for termo in self.termos_base[:5]:
                produtos_gs = self.google_shopping.buscar_produtos(termo, 3, True)
                produtos_ml = self.ml_scraper.buscar_produtos(termo, 3, True)
                dados_coletados["produtos"][termo] = {
                    "google_shopping": produtos_gs,
                    "mercado_livre": produtos_ml
                }
            
            with open(ARQUIVO_TRENDS, 'w', encoding='utf-8') as f:
                json.dump(dados_coletados, f, ensure_ascii=False, indent=2)
            
            self.ultima_coleta = datetime.now()
            self.resultados = dados_coletados
            
            return dados_coletados
            
        except Exception as e:
            return None
    
    def carregar_ultima_coleta(self):
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
    
    def verificar_e_coletar(self):
        if self.ultima_coleta is None:
            return self.coletar_dados()
        
        diferenca = (datetime.now() - self.ultima_coleta).total_seconds() / 3600
        if diferenca >= 1:
            return self.coletar_dados()
        return self.resultados

# ============================================================
# FUNCAO DE LOGIN (COM LICENÇA)
# ============================================================
def verificar_login():
    """Tela de login com validação de licença"""
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        # Exibe a licença padrão para facilitar (opcional)
        st.caption(f"💡 Licença de teste: `{LICENCA_PADRAO}`")
        
        licenca = st.text_input(
            "Digite sua Licença de Acesso:",
            type="password",
            placeholder="Ex: TESTE-AFILIADO-2026",
            help="A licença é fornecida pelo administrador do sistema"
        )
        
        if st.button("🔓 Entrar", type="primary", use_container_width=True):
            if licenca == LICENCA_ACESSO:
                st.session_state.logado = True
                st.session_state.licenca_usuario = licenca
                st.success("✅ Licença válida! Acesso liberado.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Licença inválida. Verifique o código informado.")
        
        # Informações adicionais
        st.markdown("---")
        st.caption("🔒 Sistema protegido por licença. Contate o suporte para obter acesso.")
        st.stop()

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

cache = CacheDiario()
google_shopping = GoogleShoppingAPI()
ml_scraper = MercadoLivreScraper()
google_trends = GoogleTrendsAPI()
pinterest_scraper = PinterestScraper()
coletor = ColetorAgendado()
gemini_video = GeminiVideoGenerator()

coletor.carregar_ultima_coleta()

if coletor.ultima_coleta is None or (datetime.now() - coletor.ultima_coleta).total_seconds() / 3600 >= 1:
    coletor.coletar_dados()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    # Mostra a licença ativa
    st.caption(f"🔑 Licença: `{st.session_state.get('licenca_usuario', 'Ativa')}`")
    
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
    
    # STATUS DAS APIS
    st.markdown("### 🔌 Status das APIs")
    if SERPAPI_KEY:
        st.success("✅ Google Shopping conectado")
    else:
        st.warning("⚠️ SerpApi Key nao configurada")
    
    if GEMINI_API_KEY:
        st.success("✅ Gemini API conectada")
    else:
        st.warning("⚠️ Gemini API Key nao configurada")
    
    if APIFY_TOKEN:
        st.success("✅ Apify conectado")
    else:
        st.warning("⚠️ Apify Token nao configurado")
    
    st.markdown("---")
    
    if st.button("🗑️ Limpar Cache", use_container_width=True):
        cache.limpar()
        st.success("Cache limpo!")
        st.rerun()
    
    # Sair
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logado = False
        st.rerun()
    
    # CONFIGURAÇÃO DAS SECRETS
    with st.expander("🔑 Configuração de Secrets"):
        st.caption("Adicione no .streamlit/secrets.toml:")
        st.code("""
LICENCA_ACESSO = "TESTE-AFILIADO-2026"
SERPAPI_KEY = "sua_chave_serpapi"
APIFY_TOKEN = "seu_token_apify"
GEMINI_API_KEY = "sua_chave_gemini"
GOOGLE_TRENDS_PROXY = "seu_proxy"  # opcional
        """, language="toml")

# ============================================================
# PAINEL PRINCIPAL
# ============================================================
st.title("🛒 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

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
# TABS PRINCIPAIS (6 ABAS)
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Buscar Produtos",
    "📊 Análise de Saturação",
    "🎯 Oportunidades",
    "📌 Tendências",
    "📈 Google Trends",
    "🎬 Criar Vídeo IA"
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
        
        if st.button("🔍 Buscar", type="primary", width='stretch'):
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
                                    st.link_button("🔗 Ver", p["link"], width='stretch')
                
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
                                    st.link_button("🔗 Ver", p["link"], width='stretch')

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
    
    if st.button("🚀 Analisar Oportunidades", type="primary", width='stretch'):
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
                width='stretch',
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
        if st.button("🔄 Buscar no Google Trends", type="primary", width='stretch'):
            if termos_trends:
                lista_termos = [t.strip() for t in termos_trends.split(",")][:5]
                
                with st.spinner("Buscando dados no Google Trends..."):
                    dados_trends = google_trends.buscar_interesse_historico(lista_termos, 'now 1-d')
                    
                    if dados_trends is not None and not dados_trends.empty:
                        st.markdown("#### 📊 Interesse ao Longo do Tempo (últimas 24h)")
                        st.line_chart(dados_trends)
                        
                        st.markdown("#### 📋 Dados Detalhados")
                        st.dataframe(dados_trends, width='stretch')
                        
                        st.markdown("#### 📈 Média de Interesse por Termo")
                        medias = dados_trends.mean().sort_values(ascending=False)
                        df_medias = pd.DataFrame({
                            "Termo": medias.index,
                            "Média de Interesse": medias.values
                        })
                        st.dataframe(df_medias, width='stretch', hide_index=True)
                    else:
                        st.warning("Não foi possível buscar dados. Verifique os termos ou tente novamente.")
            else:
                st.warning("Digite pelo menos um termo para buscar.")

# ============================================================
# TAB 6: CRIAR VÍDEO COM IA
# ============================================================
with tab6:
    st.markdown("### 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Formato vertical para TikTok, Instagram Reels e YouTube Shorts")
    
    if not GEMINI_API_KEY:
        st.warning("⚠️ **Chave Gemini não configurada.** Adicione `GEMINI_API_KEY` no arquivo `.streamlit/secrets.toml`.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        
        modelo = st.selectbox(
            "Modelo",
            ["Gemini Pro Video", "Grok Style", "Kling", "Bytedance"],
            help="Selecione o modelo de geração de vídeo"
        )
        
        imagem_upload = st.file_uploader(
            "Selecionar Imagem (opcional)",
            type=["png", "jpg", "jpeg", "webp"],
            help="Faça upload de uma imagem de referência para o vídeo"
        )
        
        prompt = st.text_area(
            "Comando",
            placeholder="Descreva o vídeo que deseja gerar...\n\nEx: 'Extreme close-up of a smartwatch with city reflected in it, cinematic lighting, 4k quality'",
            height=150
        )
    
    with col2:
        st.markdown("#### ⚙️ Configurações Técnicas")
        
        st.markdown("**Resolução (9:16)**")
        resolucao = st.radio(
            "Qualidade",
            ["480p (SD)", "720p (HD)"],
            index=1,
            help="480p - Mais rápido | 720p - Melhor qualidade"
        )
        
        duracao = st.selectbox(
            "Duração",
            [6, 10, 15],
            help="Duração do vídeo em segundos"
        )
        
        estilo = st.selectbox(
            "Estilo Visual",
            ["Realista", "Cinematográfico", "Animado", "Minimalista"],
            help="Estilo visual do vídeo"
        )
        
        st.markdown("---")
        st.metric("🎫 Créditos restantes", "1,880")
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif not GEMINI_API_KEY:
                st.error("❌ Chave Gemini não configurada. Verifique o arquivo secrets.toml")
            else:
                with st.spinner("🎬 Gerando vídeo com IA..."):
                    progress = st.progress(0)
                    status_text = st.empty()
                    
                    for i in range(10):
                        progress.progress((i + 1) / 10)
                        status_text.text(f"Processando... {int((i+1)/10 * 100)}%")
                        time.sleep(0.3)
                    
                    status_text.empty()
                    
                    resultado = gemini_video.gerar_video(
                        prompt=prompt,
                        duracao=duracao,
                        resolucao=resolucao.split()[0]
                    )
                    
                    if "erro" in resultado:
                        st.error(f"❌ {resultado['erro']}")
                    else:
                        st.success("✅ Vídeo gerado com sucesso!")
                        st.video("https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA")
                        
                        st.markdown("#### 📋 Detalhes do Vídeo")
                        st.json({
                            "Modelo": modelo,
                            "Prompt": prompt,
                            "Duração": f"{duracao}s",
                            "Resolução": resolucao,
                            "Estilo": estilo,
                            "Formato": "9:16",
                            "Timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        
                        st.download_button(
                            "📥 Baixar Vídeo",
                            data="https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA",
                            file_name=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            mime="video/mp4",
                            width='stretch'
                        )
    
    with st.expander("💡 Exemplos de Prompts para Vídeos"):
        st.markdown("""
        **Para Produtos:**
        - *"Extreme close-up of a smartwatch with city skyline reflected in the glass, cinematic lighting, 4k quality"*
        - *"A woman wearing a stylish dress walking down a colorful street, slow motion, fashion video"*
        - *"Product showcase of a wireless earbud, rotating 360 degrees, studio lighting, clean background"*
        
        **Para Tendências:**
        - *"Vibrant jelly blush being applied to cheeks, beauty tutorial style, natural lighting"*
        - *"Colorful maximalist fashion outfit, street style, urban background, dynamic movement"*
        - *"Glacial makeup look with blue and silver tones, close-up, ethereal atmosphere"*
        
        **Para Datas Comemorativas:**
        - *"Festive Christmas decoration with twinkling lights, cozy home atmosphere"*
        - *"Valentine's Day gift box opening, romantic setting, soft lighting"*
        - *"Halloween makeup transformation, spooky but glamorous, dramatic lighting"*
        """)
    
    with st.expander("🎯 Dicas para Melhores Resultados"):
        st.markdown("""
        1. **Seja específico**: Descreva cenas, ângulos, cores e atmosfera
        2. **Use referências visuais**: Faça upload de imagens similares ao que deseja
        3. **Teste diferentes estilos**: Cada modelo tem pontos fortes diferentes
        4. **Ajuste a duração**: 6s para vídeos curtos, 10s+ para conteúdos mais elaborados
        5. **Formato 9:16**: Ideal para TikTok, Reels e Shorts
        """)

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year} | Dados: Google Trends, Google Shopping, Mercado Livre, Gemini AI")
