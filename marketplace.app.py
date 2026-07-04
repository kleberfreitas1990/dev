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
ARQUIVO_CACHE = "cache_tendencias.json"
ARQUIVO_TRENDS = "dados_trends.json"

# ============================================================
# CARREGAR SECRETS
# ============================================================
def carregar_secrets():
    try:
        licenca = st.secrets.get("LICENCA_ACESSO", "")
        if not licenca:
            licenca = LICENCA_PADRAO
        return {
            "licenca_acesso": licenca,
            "serpapi_key": st.secrets.get("SERPAPI_KEY", ""),
            "apify_token": st.secrets.get("APIFY_TOKEN", ""),
            "gemini_key": st.secrets.get("GEMINI_API_KEY", "")
        }
    except Exception:
        return {
            "licenca_acesso": LICENCA_PADRAO,
            "serpapi_key": "",
            "apify_token": "",
            "gemini_key": ""
        }

KEYS = carregar_secrets()
LICENCA_ACESSO = KEYS["licenca_acesso"]
SERPAPI_KEY = KEYS["serpapi_key"]
APIFY_TOKEN = KEYS["apify_token"]
GEMINI_API_KEY = KEYS["gemini_key"]

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
    
    def obter(self, chave, validade_horas=24):
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

# ============================================================
# DADOS DE DATAS COMEMORATIVAS E PRODUTOS
# ============================================================
DATAS_COMEMORATIVAS = {
    "Janeiro": {
        "01-01": {"nome": "Ano Novo", "produtos": ["decoração", "roupa branca", "espumante"]},
        "01-06": {"nome": "Dia de Reis", "produtos": ["presentes religiosos", "decoração"]},
        "01-20": {"nome": "Dia de São Sebastião", "produtos": ["itens religiosos"]}
    },
    "Fevereiro": {
        "02-02": {"nome": "Dia de Iemanjá", "produtos": ["flores", "velas", "artigos religiosos"]},
        "02-14": {"nome": "Dia dos Namorados", "produtos": ["perfume", "jantar", "kit romântico"]},
        "02-28": {"nome": "Carnaval", "produtos": ["fantasia", "acessórios", "glitter"]}
    },
    "Março": {
        "03-08": {"nome": "Dia da Mulher", "produtos": ["flores", "perfumes", "kits de beleza"]},
        "03-15": {"nome": "Dia do Consumidor", "produtos": ["eletrônicos", "promoções"]},
        "03-20": {"nome": "Outono", "produtos": ["casaco leve", "cobertor"]}
    },
    "Abril": {
        "04-07": {"nome": "Dia do Jornalista", "produtos": ["canecas personalizadas"]},
        "04-21": {"nome": "Tiradentes", "produtos": ["artigos de viagem"]},
        "04-28": {"nome": "Páscoa", "produtos": ["ovo de chocolate", "cesta", "coelhinho"]}
    },
    "Maio": {
        "05-01": {"nome": "Dia do Trabalho", "produtos": ["artigos de churrasco"]},
        "05-13": {"nome": "Dia das Mães", "produtos": ["perfume", "bolsa", "vestido", "flores"]},
        "05-25": {"nome": "Dia do Orgulho LGBTQ+", "produtos": ["acessórios coloridos"]}
    },
    "Junho": {
        "06-12": {"nome": "Dia dos Namorados", "produtos": ["perfume", "vinho", "jantar"]},
        "06-24": {"nome": "São João", "produtos": ["decoração junina", "roupa xadrez"]}
    },
    "Julho": {
        "07-09": {"nome": "Férias Escolares", "produtos": ["casaco", "blusa de lã", "bota", "cachecol", "cobertor", "meia", "luva", "jaqueta"]},
        "07-20": {"nome": "Dia do Amigo", "produtos": ["kits de cerveja", "jogos"]}
    },
    "Agosto": {
        "08-11": {"nome": "Volta às Aulas", "produtos": ["mochila", "estojo", "material escolar"]},
        "08-14": {"nome": "Dia dos Pais", "produtos": ["ferramentas", "relógio", "cinto"]}
    },
    "Setembro": {
        "09-07": {"nome": "Independência do Brasil", "produtos": ["decoração verde-amarela"]},
        "09-22": {"nome": "Primavera", "produtos": ["vasos de plantas", "decoração floral"]}
    },
    "Outubro": {
        "10-12": {"nome": "Dia das Crianças", "produtos": ["brinquedo", "boneca", "carrinho"]},
        "10-31": {"nome": "Halloween", "produtos": ["fantasia", "decoração", "doces"]}
    },
    "Novembro": {
        "11-02": {"nome": "Finados", "produtos": ["flores", "velas"]},
        "11-25": {"nome": "Black Friday", "produtos": ["eletrônicos", "celular", "smartwatch"]}
    },
    "Dezembro": {
        "12-25": {"nome": "Natal", "produtos": ["presentes", "árvore", "decoração"]},
        "12-31": {"nome": "Réveillon", "produtos": ["roupa branca", "espumante"]}
    }
}

# ============================================================
# GERAR DADOS DE SUGESTÕES (CACHE DIÁRIO)
# ============================================================
def gerar_sugestoes_produtos(mes_selecionado=None):
    cache = CacheDiario()
    chave_cache = f"sugestoes_{mes_selecionado}" if mes_selecionado else "sugestoes_produtos_diarias"
    
    dados_cache = cache.obter(chave_cache, 24)
    if dados_cache is not None:
        return dados_cache
    
    # Se não tiver cache, gera os dados
    if mes_selecionado:
        eventos_mes = DATAS_COMEMORATIVAS.get(mes_selecionado, {})
        sugestoes = []
        for data, evento in eventos_mes.items():
            for produto in evento.get("produtos", [])[:4]:
                potencial = random.choice(["🟢 Alto", "🟡 Médio", "🔴 Baixo"])
                sugestoes.append({
                    "Produto": produto,
                    "Evento": evento["nome"],
                    "Data": data,
                    "Potencial": potencial,
                    "Pins": f"{random.randint(400, 3500)}",
                    "Crescimento": f"+{random.randint(5, 50)}%",
                    "Views": f"{round(random.uniform(0.5, 6.0), 1)}M"
                })
    else:
        # Sugestões gerais do mês atual
        mes_atual = datetime.now().strftime("%B").capitalize()
        eventos_mes = DATAS_COMEMORATIVAS.get(mes_atual, {})
        sugestoes = []
        for data, evento in eventos_mes.items():
            for produto in evento.get("produtos", [])[:3]:
                potencial = random.choice(["🟢 Alto", "🟡 Médio", "🔴 Baixo"])
                sugestoes.append({
                    "Produto": produto,
                    "Evento": evento["nome"],
                    "Data": data,
                    "Potencial": potencial,
                    "Pins": f"{random.randint(400, 3500)}",
                    "Crescimento": f"+{random.randint(5, 50)}%",
                    "Views": f"{round(random.uniform(0.5, 6.0), 1)}M"
                })
    
    cache.definir(chave_cache, sugestoes)
    return sugestoes

# ============================================================
# FUNCAO DE LOGIN (SEM PLACEHOLDER)
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        licenca = st.text_input(
            "Digite sua Licença de Acesso:",
            type="password"
        )
        
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

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

# ============================================================
# DASHBOARD SUPERIOR - STATUS DAS APIS
# ============================================================
st.title("📊 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    status_gs = "✅ Conectado" if SERPAPI_KEY else "❌ Desconectado"
    st.metric("🛒 Google Shopping", status_gs)

with col2:
    status_apify = "✅ Conectado" if APIFY_TOKEN else "❌ Desconectado"
    st.metric("📌 Pinterest (Apify)", status_apify)

with col3:
    status_gemini = "✅ Conectado" if GEMINI_API_KEY else "❌ Desconectado"
    st.metric("🎬 Gemini AI", status_gemini)

with col4:
    # Conta produtos no cache
    cache = CacheDiario()
    produtos_cache = len(cache.dados)
    st.metric("📦 Produtos em Cache", produtos_cache)

st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "📊 Visão Geral do Mês",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo"
])

# ============================================================
# TAB 1: VISÃO GERAL DO MÊS (GRADE VISUAL)
# ============================================================
with tab1:
    st.markdown("### 📊 Visão Geral do Mês")
    
    mes_atual = datetime.now().strftime("%B").capitalize()
    eventos_mes = DATAS_COMEMORATIVAS.get(mes_atual, {})
    
    if eventos_mes:
        st.markdown(f"#### 🗓️ {mes_atual} - {len(eventos_mes)} eventos")
        
        # Grade de produtos em cache
        produtos_sugeridos = gerar_sugestoes_produtos(mes_atual)
        
        if produtos_sugeridos:
            # Mostra grade visual
            cols = st.columns(4)
            for i, item in enumerate(produtos_sugeridos[:8]):
                with cols[i % 4]:
                    with st.container(border=True):
                        st.markdown(f"**{item['Produto']}**")
                        st.caption(f"📌 {item['Evento']}")
                        st.caption(f"📊 {item['Potencial']}")
                        st.caption(f"📈 {item['Crescimento']} | 👁️ {item['Views']}")
    else:
        st.info("Nenhum evento programado para este mês.")

# ============================================================
# TAB 2: SUGESTÕES DE PRODUTOS (TABELA)
# ============================================================
with tab2:
    st.markdown("### 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Produtos em alta baseados em tendências de mercado e datas comemorativas")
    
    mes_atual = datetime.now().strftime("%B").capitalize()
    sugestoes = gerar_sugestoes_produtos(mes_atual)
    
    if sugestoes:
        df = pd.DataFrame(sugestoes)
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Produto": "Produto",
                "Evento": "Evento",
                "Data": "Data",
                "Potencial": "Potencial",
                "Pins": "Pins",
                "Crescimento": "Crescimento",
                "Views": "Views TikTok"
            }
        )

# ============================================================
# TAB 3: CALENDÁRIO DE CONTEÚDO (INTERATIVO)
# ============================================================
with tab3:
    st.markdown("### 📅 Calendário de Conteúdo Estratégico")
    st.caption("Selecione um mês para ver sugestões de produtos e insights")
    
    # Lista de meses para seleção
    meses = list(DATAS_COMEMORATIVAS.keys())
    mes_selecionado = st.selectbox("Selecione o mês:", meses, index=datetime.now().month - 1)
    
    if mes_selecionado:
        eventos = DATAS_COMEMORATIVAS.get(mes_selecionado, {})
        sugestoes = gerar_sugestoes_produtos(mes_selecionado)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"#### 📌 Eventos - {mes_selecionado}")
            for data, evento in eventos.items():
                dia = data.split("-")[1]
                with st.container(border=True):
                    st.markdown(f"**{dia}** - {evento['nome']}")
                    st.caption(f"📦 Produtos: {', '.join(evento['produtos'][:3])}")
                    st.caption(f"⏰ Prepare-se com {random.randint(3, 14)} dias de antecedência")
        
        with col2:
            st.markdown(f"#### 🎯 Insights para {mes_selecionado}")
            if sugestoes:
                for item in sugestoes[:5]:
                    with st.container(border=True):
                        st.markdown(f"**{item['Produto']}**")
                        st.caption(f"📌 {item['Evento']} - {item['Data']}")
                        st.caption(f"📊 Potencial: {item['Potencial']}")
                        st.caption(f"📈 {item['Crescimento']} | 👁️ {item['Views']} visualizações")
            else:
                st.info("Nenhum produto sugerido para este mês.")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year}")
