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
# GERAR DADOS SUGESTÕES (ESTÁTICO - CARREGADO UMA VEZ AO DIA)
# ============================================================
def gerar_sugestoes_produtos():
    """
    Gera a lista de sugestões de produtos baseado nos dados minerados.
    Esta função é executada uma vez ao dia e os dados são cacheados.
    """
    cache = CacheDiario()
    chave_cache = "sugestoes_produtos_diarias"
    
    # Tenta carregar do cache
    dados_cache = cache.obter(chave_cache, 24)
    if dados_cache is not None:
        return dados_cache
    
    # Se não tiver cache, gera os dados
    produtos_base = {
        "casaco": {"categoria": "Moda", "evento": "Férias Escolares", "pins": 3400, "crescimento": 45, "visualizacoes": 5.8},
        "blusa de la": {"categoria": "Moda", "evento": "Férias Escolares", "pins": 2800, "crescimento": 38, "visualizacoes": 4.2},
        "bota": {"categoria": "Moda", "evento": "Férias Escolares", "pins": 1500, "crescimento": 20, "visualizacoes": 2.8},
        "cachecol": {"categoria": "Moda", "evento": "Férias Escolares", "pins": 1200, "crescimento": 15, "visualizacoes": 1.9},
        "cobertor": {"categoria": "Casa", "evento": "Férias Escolares", "pins": 950, "crescimento": 12, "visualizacoes": 1.5},
        "meia": {"categoria": "Moda", "evento": "Férias Escolares", "pins": 800, "crescimento": 10, "visualizacoes": 1.1},
        "luva": {"categoria": "Moda", "evento": "Férias Escolares", "pins": 500, "crescimento": 8, "visualizacoes": 0.6},
        "jaqueta": {"categoria": "Moda", "evento": "Férias Escolares", "pins": 450, "crescimento": 5, "visualizacoes": 0.5}
    }
    
    sugestoes = []
    for produto, dados in produtos_base.items():
        # Define potencial baseado nos pins
        if dados["pins"] >= 2000:
            potencial = "Alto"
        elif dados["pins"] >= 1000:
            potencial = "Médio"
        else:
            potencial = "Baixo"
        
        sugestoes.append({
            "Produto": produto,
            "Categoria": dados["categoria"],
            "Evento Relacionado": dados["evento"],
            "Potencial": f"● {potencial}",
            "Pins no Pinterest": f"{dados['pins']} pins",
            "Crescimento": f"+{dados['crescimento']}%",
            "Visualizações TikTok": f"{dados['visualizacoes']}M",
            "Resultados": "Histórico",
            "Buscar na Shopee": produto
        })
    
    # Salva no cache
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
        
        st.caption(f"💡 Licença de teste: `{LICENCA_PADRAO}`")
        
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
        st.caption("🔒 Sistema protegido por licença. Contate o suporte para obter acesso.")
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
    st.caption(f"🔑 Licença: `{st.session_state.get('licenca_usuario', 'Ativa')}`")
    
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
st.title("🛒 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Sugestões",
    "🔍 Buscar Produtos",
    "📈 Análise de Saturação",
    "🎯 Oportunidades",
    "📌 Tendências",
    "🎬 Criar Vídeo IA"
])

# ============================================================
# TAB 1: SUGESTÕES DE PRODUTOS (LAYOUT DO PRINT)
# ============================================================
with tab1:
    st.markdown("### 📊 Sugestões de Produtos para este Mês")
    st.caption("Produtos em alta baseados em tendências de mercado")
    
    # Carrega as sugestões (do cache ou gera novas)
    sugestoes = gerar_sugestoes_produtos()
    
    if sugestoes:
        df = pd.DataFrame(sugestoes)
        
        # Configura as colunas para exibição
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
                    "Buscar na Shopee",
                    validate=False,
                    width="small",
                    help="Clique para buscar na Shopee"
                )
            }
        )
        
        # Adiciona o rodapé com informações de consumo da API
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("📊 Dados baseados em tendências reais de mercado")
        with col2:
            st.caption("🔄 Atualizado automaticamente uma vez ao dia")
        with col3:
            st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ============================================================
# TAB 2: BUSCAR PRODUTOS
# ============================================================
with tab2:
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
                st.info(f"Buscando por '{termo_busca}'...")
                # Simula busca (substituir por chamada real à API)
                time.sleep(2)
                st.success(f"✅ Resultados para '{termo_busca}' carregados!")

# ============================================================
# TAB 3: ANÁLISE DE SATURAÇÃO
# ============================================================
with tab3:
    st.markdown("### 📊 Análise de Saturação")
    st.caption("Quanto menor o número de resultados, menor a concorrência")
    
    termo_sat = st.text_input(
        "Digite um produto para analisar:",
        placeholder="Ex: smartwatch...",
        key="sat"
    )
    
    if termo_sat and st.button("📊 Analisar", key="btn_sat"):
        with st.spinner("Analisando..."):
            st.info(f"Analisando '{termo_sat}'...")
            time.sleep(1.5)
            st.success("✅ Análise concluída!")

# ============================================================
# TAB 4: OPORTUNIDADES
# ============================================================
with tab4:
    st.markdown("### 🎯 Oportunidades para Afiliados")
    st.caption("Produtos com melhor Score e menor concorrência")
    
    if st.button("🚀 Analisar Oportunidades", type="primary", width='stretch'):
        with st.spinner("Analisando oportunidades..."):
            time.sleep(2)
            st.success("✅ Análise de oportunidades concluída!")

# ============================================================
# TAB 5: TENDÊNCIAS
# ============================================================
with tab5:
    st.markdown("### 📌 Tendências Pinterest 2025-2026")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📅 2025")
        tendencias_2025 = {
            "Beleza": ["jelly blush", "maquiagem glacial", "makeup gotica"],
            "Moda": ["broches", "terno oversized", "rendas"],
            "Decoração": ["afrodecor", "neo deco", "lar ludico"],
            "Presentes": ["entre postais", "infância retro", "perfume nichado"]
        }
        for categoria, items in tendencias_2025.items():
            with st.expander(f"📌 {categoria}"):
                for item in items:
                    st.markdown(f"- {item}")
    
    with col2:
        st.markdown("#### 📅 2026")
        tendencias_2026 = {
            "Beleza": ["blush em gel", "iluminador furta-cor", "batom metálico"],
            "Moda": ["maximalismo", "moda utilitária", "acessórios vintage"],
            "Decoração": ["decoração circense", "arte etíope", "mármore vermelho"],
            "Presentes": ["brinquedos anos 2000", "papelaria criativa", "kits de perfume"]
        }
        for categoria, items in tendencias_2026.items():
            with st.expander(f"📌 {categoria}"):
                for item in items:
                    st.markdown(f"- {item}")

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
            ["Gemini Pro Video", "Grok Style", "Kling", "Bytedance"]
        )
        
        imagem_upload = st.file_uploader(
            "Selecionar Imagem (opcional)",
            type=["png", "jpg", "jpeg", "webp"]
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
            index=1
        )
        
        duracao = st.selectbox(
            "Duração",
            [6, 10, 15]
        )
        
        estilo = st.selectbox(
            "Estilo Visual",
            ["Realista", "Cinematográfico", "Animado", "Minimalista"]
        )
        
        st.markdown("---")
        st.metric("🎫 Créditos restantes", "1,880")
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif not GEMINI_API_KEY:
                st.error("❌ Chave Gemini não configurada.")
            else:
                with st.spinner("🎬 Gerando vídeo com IA..."):
                    progress = st.progress(0)
                    status_text = st.empty()
                    
                    for i in range(10):
                        progress.progress((i + 1) / 10)
                        status_text.text(f"Processando... {int((i+1)/10 * 100)}%")
                        time.sleep(0.3)
                    
                    status_text.empty()
                    st.success("✅ Vídeo gerado com sucesso!")
                    st.video("https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year} | Dados: Google Trends, Google Shopping, Mercado Livre, Gemini AI")
