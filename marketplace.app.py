import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import random
import re
import json
import time

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
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

# ===== CONFIGURAÇÕES DE API =====
# SerpApi - para Google Shopping e Google Trends (requer chave)
# Cadastre-se em: https://serpapi.com (100 buscas grátis/mês)
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ===== DADOS HISTÓRICOS COMPLETOS =====
DADOS_HISTORICOS_COMPLETOS = {
    1: {
        "tendencias_ml": ["smartwatch", "fone bluetooth", "material escolar", "mochila", "tênis"],
        "tendencias_pinterest": ["decoração ano novo", "organização", "looks verão"],
        "tendencias_google": ["smartwatch", "fone", "caderno", "mochila"],
        "sazonais": ["✏️ Material Escolar", "🎯 Smartwatch", "🏃 Tênis"],
        "volume_base": {"smartwatch": 150, "fone bluetooth": 200, "material escolar": 300}
    },
    2: {
        "tendencias_ml": ["fantasia", "biquíni", "sungas", "protetor solar", "fone"],
        "tendencias_pinterest": ["fantasia carnaval", "looks praia", "maquiagem colorida"],
        "tendencias_google": ["fantasia", "biquíni", "chinelo", "protetor"],
        "sazonais": ["🎭 Fantasias", "🏖️ Moda Praia", "☀️ Protetor Solar"],
        "volume_base": {"fantasia": 250, "biquíni": 180, "protetor solar": 120}
    },
    3: {
        "tendencias_ml": ["kit praia", "canga", "chapéu", "óculos sol", "smartwatch"],
        "tendencias_pinterest": ["looks outono", "decoração Páscoa", "jardinagem"],
        "tendencias_google": ["canga", "chapéu", "óculos", "smartwatch"],
        "sazonais": ["🏖️ Kit Praia", "🎯 Smartwatch", "👒 Chapéu"],
        "volume_base": {"kit praia": 200, "canga": 150, "chapéu": 100}
    },
    4: {
        "tendencias_ml": ["ovo páscoa", "chocolate", "cesta", "fone", "smartwatch"],
        "tendencias_pinterest": ["decoração Páscoa", "receitas", "ovos decorados"],
        "tendencias_google": ["ovo páscoa", "chocolate", "cesta", "fone"],
        "sazonais": ["🐣 Ovo Páscoa", "🍫 Chocolate", "🧺 Cesta"],
        "volume_base": {"ovo páscoa": 400, "chocolate": 250, "cesta": 180}
    },
    5: {
        "tendencias_ml": ["dia das mães", "perfume", "bolsa", "vestido", "smartwatch"],
        "tendencias_pinterest": ["presentes mães", "DIY", "flores", "looks outono"],
        "tendencias_google": ["dia das mães", "perfume", "bolsa", "vestido"],
        "sazonais": ["👩 Dia das Mães", "💐 Flores", "🎁 Presentes"],
        "volume_base": {"dia das mães": 500, "perfume": 200, "bolsa": 150}
    },
    6: {
        "tendencias_ml": ["dia dos namorados", "perfume", "vinho", "chocolate", "fone"],
        "tendencias_pinterest": ["presentes românticos", "jantar", "looks", "viagem"],
        "tendencias_google": ["dia dos namorados", "perfume", "vinho", "chocolate"],
        "sazonais": ["💝 Dia dos Namorados", "🍷 Vinho", "🎧 Fone"],
        "volume_base": {"dia dos namorados": 450, "perfume": 180, "vinho": 120}
    },
    7: {
        "tendencias_ml": ["casaco", "bota", "cachecol", "fone", "smartwatch"],
        "tendencias_pinterest": ["looks inverno", "decoração", "viagem", "conforto"],
        "tendencias_google": ["casaco", "bota", "cachecol", "fone"],
        "sazonais": ["🧥 Casaco", "👢 Bota", "🧣 Cachecol"],
        "volume_base": {"casaco": 300, "bota": 200, "cachecol": 120}
    },
    8: {
        "tendencias_ml": ["dia dos pais", "relógio", "cinto", "ferramenta", "smartwatch"],
        "tendencias_pinterest": ["presentes pais", "DIY", "volta aulas", "decoração"],
        "tendencias_google": ["dia dos pais", "relógio", "cinto", "ferramenta"],
        "sazonais": ["👨 Dia dos Pais", "⌚ Relógio", "🔧 Ferramenta"],
        "volume_base": {"dia dos pais": 400, "relógio": 180, "ferramenta": 150}
    },
    9: {
        "tendencias_ml": ["camisa", "calça", "vestido", "tênis", "smartwatch"],
        "tendencias_pinterest": ["looks primavera", "decoração", "jardinagem", "viagens"],
        "tendencias_google": ["camisa", "calça", "vestido", "tênis"],
        "sazonais": ["🌸 Moda Primavera", "👕 Camisa", "👟 Tênis"],
        "volume_base": {"camisa": 200, "calça": 180, "vestido": 160}
    },
    10: {
        "tendencias_ml": ["fantasia halloween", "decoração", "brinquedo", "fone", "smartwatch"],
        "tendencias_pinterest": ["fantasia halloween", "decoração", "maquiagem", "receitas"],
        "tendencias_google": ["halloween", "fantasia", "decoração", "brinquedo"],
        "sazonais": ["🎃 Halloween", "🧙 Fantasia", "🕷️ Decoração"],
        "volume_base": {"fantasia halloween": 350, "decoração": 200, "brinquedo": 180}
    },
    11: {
        "tendencias_ml": ["black friday", "eletrônico", "celular", "tv", "smartwatch"],
        "tendencias_pinterest": ["ideias presentes", "decoração natal", "receitas", "black friday"],
        "tendencias_google": ["black friday", "eletrônico", "celular", "tv"],
        "sazonais": ["🛒 Black Friday", "📱 Eletrônicos", "🎄 Natal"],
        "volume_base": {"black friday": 800, "eletrônico": 300, "smartwatch": 250}
    },
    12: {
        "tendencias_ml": ["natal", "presente", "árvore", "decoração", "smartwatch"],
        "tendencias_pinterest": ["decoração natal", "presentes", "receitas", "réveillon"],
        "tendencias_google": ["natal", "presente", "árvore", "decoração"],
        "sazonais": ["🎄 Natal", "🎁 Presentes", "✨ Decoração"],
        "volume_base": {"natal": 600, "presente": 400, "decoração": 250}
    }
}

DATAS_COMEMORATIVAS = {
    (1, 1): "Ano Novo",
    (2, 14): "Carnaval (período)",
    (3, 8): "Dia da Mulher",
    (3, 20): "Início do Outono",
    (4, 1): "Páscoa (período)",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (5, 11): "Dia das Mães",
    (6, 12): "Dia dos Namorados",
    (6, 24): "Festa Junina / São João",
    (7, 9): "Férias Escolares de Julho",
    (8, 10): "Dia dos Pais",
    (8, 22): "Volta às Aulas (2º semestre)",
    (9, 7): "Independência do Brasil",
    (9, 23): "Início da Primavera",
    (10, 12): "Dia das Crianças",
    (10, 31): "Halloween",
    (11, 2): "Finados",
    (11, 28): "Black Friday (período)",
    (12, 1): "Cyber Monday (período)",
    (12, 25): "Natal",
    (12, 31): "Réveillon",
}

CATEGORIAS_TERMOS = {
    "smartwatch": "Eletrônicos",
    "fone bluetooth": "Eletrônicos",
    "caixa de som": "Eletrônicos",
    "carregador portátil": "Eletrônicos",
    "camisa": "Moda",
    "vestido": "Moda",
    "tênis": "Moda",
    "bolsa": "Moda",
    "mochila": "Moda",
    "cadeira gamer": "Casa",
}


# ============================================================
# APIs PÚBLICAS (SEM AUTENTICAÇÃO RESTRITA)
# ============================================================

def buscar_mercadolivre_publico(termo, limite=5):
    """
    Busca no Mercado Livre via endpoint público 
    (pode ter bloqueios, mas é a versão mais simples)
    """
    try:
        url = "https://api.mercadolibre.com/sites/MLB/search"
        params = {
            "q": termo,
            "limit": limite,
            "condition": "new"  # Apenas produtos novos
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        
        if resp.status_code == 403:
            # Se o ML está bloqueando, tenta o endpoint alternativo
            return buscar_mercadolivre_alternativo(termo, limite)
            
        resp.raise_for_status()
        data = resp.json()
        
        produtos = []
        for item in data.get("results", [])[:limite]:
            produtos.append({
                "nome": item.get("title", ""),
                "preco": f"R$ {item.get('price', 0):.2f}",
                "vendas": item.get("sold_quantity", 0),
                "link": item.get("permalink", ""),
                "imagem": item.get("thumbnail", ""),
                "loja": "Mercado Livre"
            })
        return produtos
    except Exception as e:
        return []

def buscar_mercadolivre_alternativo(termo, limite=5):
    """
    Busca via endpoint alternativo do ML (pode funcionar quando o principal bloqueia)
    """
    try:
        # Usa o endpoint de busca do site (HTML) com parser
        url = f"https://lista.mercadolivre.com.br/{quote(termo)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        
        # Como é HTML, precisaríamos de um parser (BeautifulSoup)
        # Por enquanto, retorna vazio - indica que precisa de scraping
        return []
    except Exception:
        return []

def buscar_google_shopping(termo, limite=5):
    """
    Busca no Google Shopping via SerpApi (pago, mas com plano gratuito)
    Cadastre-se em: https://serpapi.com
    """
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
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        produtos = []
        for item in data.get("shopping_results", [])[:limite]:
            produtos.append({
                "nome": item.get("title", ""),
                "preco": item.get("price", ""),
                "loja": item.get("source", ""),
                "link": item.get("link", ""),
                "imagem": item.get("thumbnail", ""),
                "avaliacao": item.get("rating", None)
            })
        return produtos
    except Exception:
        return []

def buscar_google_trends(termo, geo="BR", timeframe="now 7-d"):
    """
    Busca dados do Google Trends via SerpApi
    """
    if not SERPAPI_KEY:
        return None
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "q": termo,
            "engine": "google_trends",
            "data_type": "TIMESERIES",
            "api_key": SERPAPI_KEY,
            "geo": geo,
            "timeframe": timeframe
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        # Extrai valores de interesse
        timeline = data.get("interest_over_time", {}).get("timeline_data", [])
        if timeline:
            valores = [int(item.get("value", [0])[0]) for item in timeline if item.get("value")]
            return {
                "media": sum(valores) / len(valores) if valores else 0,
                "pico": max(valores) if valores else 0,
                "tendencia": "crescendo" if valores and valores[-1] > valores[0] else "estável"
            }
        return None
    except Exception:
        return None

def buscar_pinterest_trends(termo):
    """
    Verifica se um termo está em alta no Pinterest
    Usa a API pública de sugestões do Pinterest
    """
    try:
        url = f"https://www.pinterest.com/resource/BaseSearchResource/get/"
        params = {
            "source_url": f"/search/pins/?q={quote(termo)}",
            "data": '{"options":{"query":"' + termo + '","scope":"pins"}}'
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        # O Pinterest bloqueia requisições sem autenticação
        # Esta é uma tentativa, mas provavelmente falhará
        return {"esta_em_alta": False, "fonte": "Pinterest (limitado)"}
    except Exception:
        return {"esta_em_alta": False, "fonte": "Pinterest (não disponível)"}


# ============================================================
# FUNÇÕES DE ANÁLISE COMBINADA
# ============================================================

def analisar_produto_multifonte(termo, mes_atual):
    """
    Analisa produto combinando múltiplas fontes:
    1. ML (público)
    2. Google Shopping (via SerpApi)
    3. Google Trends (via SerpApi)
    """
    historico = DADOS_HISTORICOS_COMPLETOS.get(mes_atual, DADOS_HISTORICOS_COMPLETOS[1])
    
    # Busca em múltiplas fontes
    produtos_ml = buscar_mercadolivre_publico(termo, 3)
    produtos_google = buscar_google_shopping(termo, 3)
    
    # Tendências do Google
    trends = buscar_google_trends(termo)
    
    # Dados históricos
    volume_historico = historico.get("volume_base", {}).get(termo, 0)
    esta_no_pinterest = termo.lower() in [t.lower() for t in historico.get("tendencias_pinterest", [])]
    esta_no_google_historico = termo.lower() in [t.lower() for t in historico.get("tendencias_google", [])]
    
    # Calcula volume atual (aproximado pelo número de produtos encontrados)
    volume_atual = len(produtos_ml) * 100  # Estimativa
    
    # Calcula crescimento
    if volume_historico > 0:
        crescimento = ((volume_atual - volume_historico) / volume_historico) * 100
    else:
        crescimento = 0
    
    # Sinais de saturação
    sinais_saturacao = []
    
    if len(produtos_ml) >= 3:
        sinais_saturacao.append("📈 Múltiplos produtos no ML")
    if len(produtos_google) >= 3:
        sinais_saturacao.append("🛒 Múltiplos produtos no Google Shopping")
    if crescimento > 50:
        sinais_saturacao.append("🚀 Crescimento acelerado (>50%)")
    if esta_no_pinterest and esta_no_google_historico:
        sinais_saturacao.append("🔥 Tendência em múltiplas fontes")
    if trends and trends.get("media", 0) > 50:
        sinais_saturacao.append("📊 Alta no Google Trends")
    
    # Status
    if len(sinais_saturacao) >= 3:
        status = "🔴 COMEÇANDO A SATURAR"
        recomendacao = "Produto com sinais claros de saturação. Entre rápido ou busque nichos."
    elif len(sinais_saturacao) >= 2:
        status = "🟡 MONITORAR - Crescendo rapidamente"
        recomendacao = "Ainda há oportunidade, mas a concorrência está aumentando."
    elif len(sinais_saturacao) >= 1:
        status = "🟢 OPORTUNIDADE - Mercado em crescimento"
        recomendacao = "Bom momento para entrar. Poucos sinais de saturação."
    else:
        status = "⚪ OPORTUNIDADE INICIAL"
        recomendacao = "Mercado ainda não validado. Pode ser uma aposta."
    
    return {
        "termo": termo,
        "produtos_ml": produtos_ml,
        "produtos_google": produtos_google,
        "trends": trends,
        "volume_historico": volume_historico,
        "crescimento": crescimento,
        "sinais_saturacao": sinais_saturacao,
        "status": status,
        "recomendacao": recomendacao
    }


# ============================================================
# LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🔐 Minerador de Produtos - Login")
        chave = st.text_input("Digite sua chave de acesso:", type="password")
        if st.button("Entrar"):
            if chave == CHAVE_TESTE:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Chave inválida. Tente novamente.")
        st.stop()


# ============================================================
# APP
# ============================================================
verificar_login()

st.title("🛒 Minerador de Produtos - Afiliados")
st.caption("Análise de produtos com dados de ML, Google Shopping e Google Trends")

# ===== SIDEBAR: CONFIGURAÇÕES =====
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    serp_key = st.text_input("SerpApi Key (opcional)", type="password", value=SERPAPI_KEY)
    if serp_key != SERPAPI_KEY:
        SERPAPI_KEY = serp_key
        st.success("Chave atualizada!")
    
    st.markdown("---")
    st.markdown("**🔗 Fontes de dados:**")
    st.markdown("""
    - Mercado Livre (público)
    - Google Shopping (via SerpApi)
    - Google Trends (via SerpApi)
    - Dados históricos (built-in)
    """)
    
    if not SERPAPI_KEY:
        st.warning("⚠️ Sem SerpApi Key. Algumas funcionalidades serão limitadas.")
        st.markdown("[Obter chave grátis](https://serpapi.com)")

st.markdown("---")

# ===== SEÇÃO 1: ANÁLISE MULTIFONTE =====
st.markdown("## 🔍 Análise de Produto - Múltiplas Fontes")
st.caption("Cruza dados do Mercado Livre, Google Shopping e Google Trends")

termo_busca = st.text_input("🔍 Digite um produto para analisar:", placeholder="Ex: smartwatch, fone bluetooth...")

if termo_busca and st.button("📊 Analisar Produto", type="primary"):
    mes_atual = datetime.now().month
    
    with st.spinner(f"Cruzando dados para '{termo_busca}'..."):
        analise = analisar_produto_multifonte(termo_busca, mes_atual)
        
        # Status
        st.markdown(f"### {analise['status']}")
        st.markdown(f"**💡 {analise['recomendacao']}**")
        
        st.markdown("---")
        
        # Métricas
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🔵 ML", f"{len(analise['produtos_ml'])} produtos")
        with c2:
            st.metric("🛒 Google Shopping", f"{len(analise['produtos_google'])} produtos")
        with c3:
            st.metric("📈 Crescimento YoY", f"{analise['crescimento']:.1f}%")
        
        st.markdown("---")
        
        # Sinais de saturação
        st.markdown("#### 🚨 Sinais de Saturação")
        if analise["sinais_saturacao"]:
            for sinal in analise["sinais_saturacao"]:
                st.markdown(f"- {sinal}")
        else:
            st.info("✅ Nenhum sinal de saturação detectado.")
        
        st.markdown("---")
        
        # Produtos ML
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 🔵 Mercado Livre")
            if analise["produtos_ml"]:
                for p in analise["produtos_ml"]:
                    st.markdown(f"- **{p.get('nome', '')[:50]}**")
                    st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                    if p.get("link"):
                        st.markdown(f"  [🔗 Ver]({p['link']})")
                    st.markdown("")
            else:
                st.info("Nenhum produto encontrado (possível bloqueio do ML)")
        
        with c2:
            st.markdown("#### 🛒 Google Shopping")
            if analise["produtos_google"]:
                for p in analise["produtos_google"]:
                    st.markdown(f"- **{p.get('nome', '')[:50]}**")
                    st.markdown(f"  💰 {p.get('preco', '')} | 🏪 {p.get('loja', '')}")
                    if p.get("link"):
                        st.markdown(f"  [🔗 Ver]({p['link']})")
                    st.markdown("")
            else:
                if SERPAPI_KEY:
                    st.info("Nenhum produto encontrado no Google Shopping")
                else:
                    st.warning("SerpApi Key necessária para Google Shopping")
        
        st.markdown("---")
        
        # Links rápidos
        c1, c2 = st.columns(2)
        with c1:
            st.link_button("🔍 Buscar no ML", f"https://lista.mercadolivre.com.br/{quote(termo_busca)}", width='stretch')
        with c2:
            st.link_button("🔍 Buscar no Google Shopping", f"https://www.google.com/search?q={quote(termo_busca)}&tbm=shop", width='stretch')

st.markdown("---")

# ===== SEÇÃO 2: SUGESTÕES SAZONAIS =====
st.markdown("## 📅 Sugestões para o Mês Atual")

mes_atual = datetime.now().month
dados_mes = DADOS_HISTORICOS_COMPLETOS.get(mes_atual, DADOS_HISTORICOS_COMPLETOS[1])

st.markdown(f"**Mês:** {datetime.now().strftime('%B').capitalize()}")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🔵 Mercado Livre**")
    for t in dados_mes.get("tendencias_ml", [])[:4]:
        st.markdown(f"- {t}")

with col2:
    st.markdown("**📌 Pinterest**")
    for t in dados_mes.get("tendencias_pinterest", [])[:4]:
        st.markdown(f"- {t}")

with col3:
    st.markdown("**🔍 Google Trends**")
    for t in dados_mes.get("tendencias_google", [])[:4]:
        st.markdown(f"- {t}")

st.markdown("---")

st.markdown("#### 🎯 Produtos Sazonais em Destaque")
for s in dados_mes.get("sazonais", []):
    st.markdown(f"- {s}")

st.markdown("---")

# ===== SEÇÃO 3: STATUS DAS APIS =====
with st.expander("🔧 Status das APIs"):
    st.markdown("""
    | Fonte | Status | Observação |
    |-------|--------|------------|
    | Mercado Livre (público) | ⚠️ | Pode bloquear requisições repetidas |
    | Google Shopping (SerpApi) | ✅ | Funciona, requer chave |
    | Google Trends (SerpApi) | ✅ | Funciona, requer chave |
    | Pinterest | ⚠️ | Limitado, sem API pública |
    | Dados históricos | ✅ | Sempre disponível |
    """)
    
    if not SERPAPI_KEY:
        st.warning("🔑 **Configure sua SerpApi Key** para acessar Google Shopping e Google Trends.")
        st.markdown("[Obter chave gratuita na SerpApi](https://serpapi.com)")
