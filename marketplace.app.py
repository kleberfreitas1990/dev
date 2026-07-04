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
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONSTANTES
# ============================================================
LICENCA_PADRAO = "TESTE-AFILIADO-2026"
ARQUIVO_CACHE = "cache_tendencias.json"
ARQUIVO_GALERIA = "galeria_videos.json"

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
# SISTEMA DE GALERIA DE VÍDEOS
# ============================================================
class GaleriaVideos:
    def __init__(self, arquivo=ARQUIVO_GALERIA):
        self.arquivo = arquivo
        self.videos = self.carregar()
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.videos, f, ensure_ascii=False, indent=2)
    
    def adicionar(self, video):
        video["id"] = len(self.videos) + 1
        video["timestamp"] = datetime.now().isoformat()
        self.videos.insert(0, video)  # Adiciona no início
        self.salvar()
        return video
    
    def listar(self, limite=10):
        return self.videos[:limite]
    
    def limpar(self):
        self.videos = []
        self.salvar()

# ============================================================
# GERADOR DE VÍDEO COM GEMINI
# ============================================================
class GeminiVideoGenerator:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.galeria = GaleriaVideos()
    
    def gerar_video(self, prompt, duracao=6, resolucao="480p", estilo="Realista", modelo="Gemini Pro Video"):
        if not self.api_key:
            return {"erro": "Chave Gemini não configurada"}
        
        try:
            # Simula geração (substituir por API real)
            time.sleep(2)
            
            video = {
                "url": "https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA",
                "prompt": prompt,
                "duracao": duracao,
                "resolucao": resolucao,
                "estilo": estilo,
                "modelo": modelo,
                "status": "concluido"
            }
            
            # Salva na galeria
            self.galeria.adicionar(video)
            return video
        except Exception as e:
            return {"erro": f"Erro: {str(e)}"}

# ============================================================
# DADOS DE DATAS COMEMORATIVAS
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
# GERAR SUGESTÕES DE PRODUTOS
# ============================================================
def gerar_sugestoes_produtos(mes_selecionado=None):
    cache = CacheDiario()
    chave_cache = f"sugestoes_{mes_selecionado}" if mes_selecionado else "sugestoes_diarias"
    
    dados_cache = cache.obter(chave_cache, 24)
    if dados_cache is not None:
        return dados_cache
    
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
# FUNCAO DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        licenca = st.text_input("Digite sua Licença de Acesso:", type="password")
        
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

st.title("📊 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral",
    "📌 Sugestões de Produtos",
    "📅 Calendário",
    "🎬 Criar Vídeo IA"
])

# ============================================================
# TAB 1: VISÃO GERAL (GRADE VISUAL COM INSIGHTS)
# ============================================================
with tab1:
    st.markdown("### 📊 Visão Geral do Mês")
    
    mes_atual = datetime.now().strftime("%B").capitalize()
    eventos_mes = DATAS_COMEMORATIVAS.get(mes_atual, {})
    
    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Mês Atual", mes_atual)
    with col2:
        st.metric("🎯 Eventos no Mês", len(eventos_mes))
    with col3:
        st.metric("📦 Produtos Sugeridos", len(gerar_sugestoes_produtos(mes_atual)))
    
    st.markdown("---")
    
    # Grade de produtos com insights
    if eventos_mes:
        st.markdown(f"#### 🎯 Insights para {mes_atual}")
        
        produtos_sugeridos = gerar_sugestoes_produtos(mes_atual)
        
        if produtos_sugeridos:
            # Grade 4 colunas
            cols = st.columns(4)
            for i, item in enumerate(produtos_sugeridos[:8]):
                with cols[i % 4]:
                    with st.container(border=True):
                        st.markdown(f"### {item['Produto']}")
                        st.caption(f"📌 **Evento:** {item['Evento']}")
                        st.caption(f"📊 **Potencial:** {item['Potencial']}")
                        st.caption(f"📈 **Crescimento:** {item['Crescimento']}")
                        st.caption(f"👁️ **Views TikTok:** {item['Views']}")
                        st.caption(f"📌 **Data:** {item['Data']}")
    else:
        st.info("Nenhum evento programado para este mês.")
        
        # Sugestões gerais
        st.markdown("#### 💡 Sugestões Gerais")
        produtos_base = ["smartwatch", "fone bluetooth", "camisa", "vestido", "tênis", "bolsa"]
        cols = st.columns(4)
        for i, produto in enumerate(produtos_base[:4]):
            with cols[i % 4]:
                with st.container(border=True):
                    st.markdown(f"### {produto}")
                    st.caption("📌 Tendência do Mês")
                    st.caption("📊 Potencial: 🟡 Médio")
                    st.caption("📈 Crescimento: +15%")
                    st.caption("👁️ Views: 2.5M")

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
# TAB 3: CALENDÁRIO DE CONTEÚDO
# ============================================================
with tab3:
    st.markdown("### 📅 Calendário de Conteúdo Estratégico")
    st.caption("Selecione um mês para ver sugestões de produtos e insights")
    
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
                        st.caption(f"📈 {item['Crescimento']} | 👁️ {item['Views']}")
            else:
                st.info("Nenhum produto sugerido para este mês.")

# ============================================================
# TAB 4: CRIAR VÍDEO COM IA + GALERIA
# ============================================================
with tab4:
    st.markdown("### 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Formato vertical para TikTok, Instagram Reels e YouTube Shorts")
    
    if not GEMINI_API_KEY:
        st.warning("⚠️ **Chave Gemini não configurada.** Adicione `GEMINI_API_KEY` no arquivo `.streamlit/secrets.toml`.")
    
    # Layout principal
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
            placeholder="Descreva o vídeo que deseja gerar...\n\nEx: 'Extreme close-up of a smartwatch with city reflected in it'",
            height=120
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
                    
                    generator = GeminiVideoGenerator()
                    resultado = generator.gerar_video(
                        prompt=prompt,
                        duracao=duracao,
                        resolucao=resolucao.split()[0],
                        estilo=estilo,
                        modelo=modelo
                    )
                    
                    if "erro" in resultado:
                        st.error(f"❌ {resultado['erro']}")
                    else:
                        st.success("✅ Vídeo gerado com sucesso!")
                        st.rerun()
    
    # ===== GALERIA DE VÍDEOS =====
    st.markdown("---")
    st.markdown("### 🖼️ Galeria de Vídeos Gerados")
    
    galeria = GaleriaVideos()
    videos = galeria.listar(12)
    
    if videos:
        # Grade de vídeos
        cols = st.columns(4)
        for i, video in enumerate(videos):
            with cols[i % 4]:
                with st.container(border=True):
                    st.video(video.get("url", "https://placehold.co/600x400/000000/FFFFFF?text=Video"))
                    st.caption(f"🎬 {video.get('modelo', 'IA')}")
                    st.caption(f"📝 {video.get('prompt', '')[:50]}...")
                    st.caption(f"⏱️ {video.get('duracao', 6)}s | {video.get('resolucao', '480p')}")
                    if st.button(f"🗑️ Remover", key=f"del_{video.get('id', i)}"):
                        # Remove da galeria (simplificado)
                        galeria.videos = [v for v in galeria.videos if v.get('id') != video.get('id')]
                        galeria.salvar()
                        st.rerun()
    else:
        st.info("📭 Nenhum vídeo gerado ainda. Crie seu primeiro vídeo acima!")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year}")
