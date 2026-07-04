import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import random
import json
import os

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
ARQUIVO_CACHE = "cache_tendencias.json"

# ============================================================
# CONFIGURACAO DAS APIS
# ============================================================
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================
# SISTEMA DE CACHE DIARIO
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
    
    def obter(self, chave, validade_horas=24):
        hoje = datetime.now().date().isoformat()
        dados = self.dados.get(chave, {})
        
        if dados and dados.get("data") == hoje:
            hora_cache = datetime.strptime(dados.get("hora", "00:00"), "%H:%M")
            hora_atual = datetime.now()
            diferenca = (hora_atual - hora_cache.replace(year=hora_atual.year, 
                                                         month=hora_atual.month, 
                                                         day=hora_atual.day)).total_seconds() / 3600
            
            if diferenca < validade_horas:
                return dados.get("valor")
        
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

# ============================================================
# CLASSE PARA GOOGLE SHOPPING (VIA SERPAPI)
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
# CLASSE PARA MERCADO LIVRE (VIA API PUBLICA)
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
# TENDENCIAS PINTEREST 2025-2026
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

# INICIALIZA AS APIS AQUI (ANTES DE USAR)
cache = CacheDiario()
google_shopping = GoogleShoppingAPI()
ml_scraper = MercadoLivreScraper()

st.title("Minerador de Produtos - Afiliados")
st.caption("Consultas diarias com cache automatico - Google Shopping + Mercado Livre + Google Trends")

# Status no sidebar
with st.sidebar:
    st.markdown("### Status")
    st.markdown(f"**Data/Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    st.markdown("**Cache:**")
    st.caption(f"Arquivo: {ARQUIVO_CACHE}")
    st.caption("Validade: 24 horas")
    
    if SERPAPI_KEY:
        st.success("Google Shopping (SerpApi) - OK")
    else:
        st.warning("SerpApi Key nao configurada")
    
    st.markdown("---")
    if st.button("Limpar Cache"):
        cache.limpar()
        st.success("Cache limpo com sucesso!")
        st.rerun()

st.markdown("---")

# ===== SECAO 1: TENDENCIAS PINTEREST =====
st.markdown("## Tendencias Pinterest 2025-2026")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**2025**")
    for categoria, items in TENDENCIAS_PINTEREST["2025"].items():
        st.markdown(f"*{categoria}*")
        for item in items[:3]:
            st.markdown(f"- {item}")

with col2:
    st.markdown("**2026**")
    for categoria, items in TENDENCIAS_PINTEREST["2026"].items():
        st.markdown(f"*{categoria}*")
        for item in items[:3]:
            st.markdown(f"- {item}")

st.markdown("---")

# ===== SECAO 2: BUSCAR PRODUTOS =====
st.markdown("## Buscar Produtos (Cache Diario)")

termo_busca = st.text_input("Digite um produto:", placeholder="Ex: smartwatch, fone bluetooth...")

col_forcar = st.columns([3, 1])
with col_forcar[0]:
    if termo_busca and st.button("Buscar", type="primary"):
        st.session_state.termo_busca = termo_busca
        st.session_state.forcar = False

with col_forcar[1]:
    if termo_busca and st.button("Atualizar", type="secondary"):
        st.session_state.termo_busca = termo_busca
        st.session_state.forcar = True

if "termo_busca" in st.session_state and st.session_state.termo_busca:
    termo = st.session_state.termo_busca
    forcar = st.session_state.get("forcar", False)
    
    st.markdown(f"### Resultados para '{termo}'")
    
    if forcar:
        st.info("Atualizacao forcada - buscando dados novos...")
    
    with st.spinner("Buscando no Google Shopping..."):
        produtos_google = google_shopping.buscar_produtos(termo, 8, forcar)
        total_google = google_shopping.buscar_total_resultados(termo, forcar)
    
    with st.spinner("Buscando no Mercado Livre..."):
        produtos_ml = ml_scraper.buscar_produtos(termo, 5, forcar)
        total_ml = ml_scraper.buscar_total_resultados(termo, forcar)
    
    st.caption(f"Consulta realizada em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
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

# ===== SECAO 3: MINERADOR PRO =====
st.markdown("## Minerador Pro - Oportunidades")

if st.button("Analisar Oportunidades Diarias", type="primary"):
    with st.spinner("Analisando oportunidades..."):
        mes_atual = datetime.now().month
        resultados = []
        
        # Adiciona tendencias do Pinterest
        todos_termos = list(DADOS_HISTORICOS.get(mes_atual, ["smartwatch", "fone"]))
        
        for categoria in TENDENCIAS_PINTEREST["2026"].values():
            for item in categoria[:2]:
                if item not in todos_termos:
                    todos_termos.append(item)
        
        for termo in todos_termos[:10]:
            produtos = google_shopping.buscar_produtos(termo, 3, False)
            total = google_shopping.buscar_total_resultados(termo, False) + ml_scraper.buscar_total_resultados(termo, False)
            score = calcular_score(total, produtos)
            
            resultados.append({
                "Produto": termo,
                "Score": score,
                "Total Resultados": total,
                "Produtos Encontrados": len(produtos),
                "Fonte": "Pinterest" if termo in str(TENDENCIAS_PINTEREST) else "Historico"
            })
            time.sleep(0.5)
        
        df = pd.DataFrame(resultados).sort_values("Score", ascending=False).reset_index(drop=True)
        
        st.markdown("### Oportunidades do Dia")
        st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.info("Foque nos produtos com maior Score e menor numero de resultados!")

st.markdown("---")

# ===== CONFIGURACAO =====
with st.expander("Sobre o Cache Diario"):
    st.markdown("""
    **Como funciona o cache diario:**
    
    - Os dados sao armazenados localmente por 24 horas
    - Consultas repetidas usam o cache para economizar recursos
    - Clique em 'Atualizar' para forcar uma nova consulta
    - Clique em 'Limpar Cache' para remover todos os dados armazenados
    
    **Vantagens:**
    - Menos requisicoes as APIs
    - Resposta mais rapida
    - Economia de cotas (SerpApi)
    - Dados consistentes durante o dia
    """)
    
    if not SERPAPI_KEY:
        st.warning("SerpApi Key nao configurada. Obtenha em serpapi.com")
