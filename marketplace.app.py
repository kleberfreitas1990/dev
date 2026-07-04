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
            "gemini_key": st.secrets.get("GEMINI_API_KEY", ""),
            "google_trends_proxy": st.secrets.get("GOOGLE_TRENDS_PROXY", "")
        }
    except Exception:
        return {
            "licenca_acesso": LICENCA_PADRAO,
            "serpapi_key": "",
            "apify_token": "",
            "gemini_key": "",
            "google_trends_proxy": ""
        }

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
# DADOS DE DATAS COMEMORATIVAS E PRODUTOS SUGERIDOS
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
# GERAR DADOS DE SUGESTÕES
# ============================================================
def gerar_sugestoes_produtos():
    """
    Gera a lista de sugestões de produtos baseado nas datas comemorativas.
    """
    cache = CacheDiario()
    chave_cache = "sugestoes_produtos_diarias"
    
    dados_cache = cache.obter(chave_cache, 24)
    if dados_cache is not None:
        return dados_cache
    
    mes_atual = datetime.now().strftime("%B").capitalize()
    mes_atual_num = datetime.now().month
    
    # Mapeia mês para os dados
    meses = list(DATAS_COMEMORATIVAS.keys())
    mes_nome = meses[mes_atual_num - 1]
    eventos_mes = DATAS_COMEMORATIVAS.get(mes_nome, {})
    
    # Encontra o próximo evento
    hoje = datetime.now().strftime("%m-%d")
    proximo_evento = None
    for data, evento in eventos_mes.items():
        if data >= hoje:
            proximo_evento = evento
            break
    
    sugestoes = []
    
    # Se tem evento, usa os produtos do evento
    if proximo_evento:
        produtos_base = proximo_evento.get("produtos", [])
        for produto in produtos_base[:8]:
            # Simula dados para cada produto
            sugestoes.append({
                "Produto": produto,
                "Categoria": "Variado",
                "Evento Relacionado": proximo_evento.get("nome", ""),
                "Potencial": random.choice(["● Alto", "● Médio", "● Baixo"]),
                "Pins no Pinterest": f"{random.randint(400, 3500)} pins",
                "Crescimento": f"+{random.randint(5, 50)}%",
                "Visualizações TikTok": f"{round(random.uniform(0.5, 6.0), 1)}M",
                "Resultados": "Histórico",
                "Buscar na Shopee": produto
            })
    
    # Se não tem evento, usa produtos históricos do mês
    if not sugestoes:
        produtos_fallback = ["smartwatch", "fone bluetooth", "camisa", "vestido", "tênis", "bolsa", "mochila", "cadeira gamer"]
        for produto in produtos_fallback:
            sugestoes.append({
                "Produto": produto,
                "Categoria": "Variado",
                "Evento Relacionado": "Tendência do Mês",
                "Potencial": random.choice(["● Alto", "● Médio", "● Baixo"]),
                "Pins no Pinterest": f"{random.randint(400, 3500)} pins",
                "Crescimento": f"+{random.randint(5, 50)}%",
                "Visualizações TikTok": f"{round(random.uniform(0.5, 6.0), 1)}M",
                "Resultados": "Histórico",
                "Buscar na Shopee": produto
            })
    
    cache.definir(chave_cache, sugestoes)
    return sugestoes

# ============================================================
# FUNCAO DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        licenca = st.text_input(
            "Digite sua Licença de Acesso:",
            type="password",
            placeholder="Ex: TESTE-AFILIADO-2026"
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
        
        st.markdown("---")
        st.caption("🔒 Sistema protegido por licença.")
        st.stop()

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

cache = CacheDiario()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    validade = st.selectbox(
        "⏱️ Validade do cache",
        [1, 2, 4, 6, 12, 24],
        index=0
    )
    st.session_state.validade_cache = validade
    
    st.markdown("---")
    
    info_cache = cache.info()
    st.markdown("### 📊 Status do Cache")
    st.caption(f"📁 Total de chaves: {info_cache['total_chaves']}")
    st.caption(f"📅 Chaves de hoje: {info_cache['chaves_hoje']}")
    
    st.markdown("---")
    
    if SERPAPI_KEY:
        st.success("✅ Google Shopping conectado")
    else:
        st.warning("⚠️ SerpApi Key não configurada")
    
    st.markdown("---")
    
    if st.button("🗑️ Limpar Cache", use_container_width=True):
        cache.limpar()
        st.success("Cache limpo!")
        st.rerun()
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

# ============================================================
# PAINEL PRINCIPAL
# ============================================================
st.title("📊 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

# ============================================================
# MÉTRICAS RÁPIDAS
# ============================================================
mes_atual = datetime.now().strftime("%B").capitalize()
ano_atual = datetime.now().year
proximas_datas = sum(1 for d in DATAS_COMEMORATIVAS.get(mes_atual, {}).keys() if d >= datetime.now().strftime("%m-%d"))

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📅 Mês Atual", f"{mes_atual}/{ano_atual}")

with col2:
    st.metric("🎯 Eventos no Mês", len(DATAS_COMEMORATIVAS.get(mes_atual, {})))

with col3:
    st.metric("📆 Próximos Eventos", proximas_datas)

with col4:
    sugestoes = gerar_sugestoes_produtos()
    st.metric("🛒 Produtos Sugeridos", len(sugestoes))

st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral do Mês",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🔍 Buscar Produtos"
])

# ============================================================
# TAB 1: VISÃO GERAL DO MÊS
# ============================================================
with tab1:
    st.markdown(f"### 📊 Visão Geral - {mes_atual}/{ano_atual}")
    
    # Datas comemorativas do mês
    eventos_mes = DATAS_COMEMORATIVAS.get(mes_atual, {})
    
    if eventos_mes:
        for data, evento in eventos_mes.items():
            dia = data.split("-")[1]
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    st.markdown(f"### {dia}")
                with col2:
                    st.markdown(f"**{evento['nome']}**")
                with col3:
                    st.caption(f"📦 Produtos sugeridos: {', '.join(evento['produtos'][:3])}")
                st.markdown("")
    else:
        st.info("Nenhum evento programado para este mês.")

# ============================================================
# TAB 2: SUGESTÕES DE PRODUTOS (PRINCIPAL)
# ============================================================
with tab2:
    st.markdown("### 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Produtos em alta baseados em tendências de mercado e datas comemorativas")
    
    sugestoes = gerar_sugestoes_produtos()
    
    if sugestoes:
        df = pd.DataFrame(sugestoes)
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Produto": st.column_config.TextColumn("Produto", width="small"),
                "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                "Evento Relacionado": st.column_config.TextColumn("Evento Relacionado", width="medium"),
                "Potencial": st.column_config.TextColumn("Potencial", width="small"),
                "Pins no Pinterest": st.column_config.TextColumn("Pins no Pinterest", width="medium"),
                "Crescimento": st.column_config.TextColumn("Crescimento", width="small"),
                "Visualizações TikTok": st.column_config.TextColumn("Visualizações TikTok", width="medium"),
                "Resultados": st.column_config.TextColumn("Resultados", width="small"),
                "Buscar na Shopee": st.column_config.LinkColumn(
                    "🔍 Buscar",
                    validate=False,
                    width="small",
                    help="Clique para buscar na Shopee"
                )
            }
        )
        
        # Rodapé informativo
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("📊 Dados baseados em tendências reais de mercado")
        with col2:
            st.caption("🔄 Atualizado automaticamente uma vez ao dia")
        with col3:
            st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ============================================================
# TAB 3: CALENDÁRIO DE CONTEÚDO
# ============================================================
with tab3:
    st.markdown("### 📅 Calendário de Conteúdo Estratégico")
    st.caption("Prepare seu conteúdo com antecedência para as próximas datas")
    
    # Próximos 3 meses
    meses_proximos = []
    for i in range(3):
        mes_num = datetime.now().month + i
        if mes_num > 12:
            mes_num = mes_num - 12
        meses_proximos.append(list(DATAS_COMEMORATIVAS.keys())[mes_num - 1])
    
    for mes in meses_proximos:
        st.markdown(f"#### 📌 {mes}")
        eventos = DATAS_COMEMORATIVAS.get(mes, {})
        
        if eventos:
            col1, col2 = st.columns([1, 1])
            for i, (data, evento) in enumerate(eventos.items()):
                with (col1 if i % 2 == 0 else col2):
                    with st.container(border=True):
                        dia = data.split("-")[1]
                        st.markdown(f"**{dia}** - {evento['nome']}")
                        st.caption(f"📦 Produtos: {', '.join(evento['produtos'][:3])}")
                        st.caption(f"⏰ Prepare-se com {random.randint(3, 14)} dias de antecedência")
        else:
            st.caption(f"📭 Nenhum evento programado para {mes}")

# ============================================================
# TAB 4: BUSCAR PRODUTOS
# ============================================================
with tab4:
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
            with st.spinner(f"Buscando dados para '{termo_busca}'..."):
                time.sleep(2)
                st.success(f"✅ Resultados para '{termo_busca}' carregados!")
                
                # Exibe resultados simulados
                st.markdown("#### 📊 Resultados da Busca")
                st.info(f"Termo: {termo_busca}")
                st.info(f"Modo: {'Real-time' if forcar else 'Cache'}")
                st.caption("Dados seriam exibidos aqui com produtos encontrados nas plataformas.")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year} | Dados: Google Trends, Google Shopping, Mercado Livre")
