import os

# ============================================================
# ESTRUTURA DE PASTAS E ARQUIVOS
# ============================================================

# Conteúdo dos arquivos
ARQUIVOS = {
    "marketplace.app.py": '''import streamlit as st
import warnings
from datetime import datetime

# ============================================================
# IMPORTAR MÓDULOS
# ============================================================
from modules.auth import verificar_login
from modules.creditos import CreditosDiarios
from modules.galeria import GaleriaVideos
from modules.cache import CacheDiario
from modules.video_generator import SnapGenVideoGenerator
from modules.dashboard import render_dashboard
from modules.products import render_products
from modules.calendar import render_calendar

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
# CARREGAR SECRETS
# ============================================================
def carregar_secrets():
    try:
        return {
            "licenca_acesso": st.secrets.get("LICENCA_ACESSO", "TESTE-AFILIADO-2026"),
            "serpapi_key": st.secrets.get("SERPAPI_KEY", ""),
            "apify_token": st.secrets.get("APIFY_TOKEN", ""),
            "snapgen_api_key": st.secrets.get("SNAPGEN_API_KEY", ""),
            "snapgen_email": st.secrets.get("SNAPGEN_EMAIL", ""),
            "snapgen_password": st.secrets.get("SNAPGEN_PASSWORD", "")
        }
    except Exception:
        return {
            "licenca_acesso": "TESTE-AFILIADO-2026",
            "serpapi_key": "",
            "apify_token": "",
            "snapgen_api_key": "",
            "snapgen_email": "",
            "snapgen_password": ""
        }

KEYS = carregar_secrets()
LICENCA_ACESSO = KEYS["licenca_acesso"]
SERPAPI_KEY = KEYS["serpapi_key"]
APIFY_TOKEN = KEYS["apify_token"]
SNAPGEN_API_KEY = KEYS["snapgen_api_key"]
SNAPGEN_EMAIL = KEYS["snapgen_email"]
SNAPGEN_PASSWORD = KEYS["snapgen_password"]

# ============================================================
# VERIFICAR LOGIN
# ============================================================
licenca = verificar_login()

# ============================================================
# INICIALIZAR SISTEMAS
# ============================================================
creditos = CreditosDiarios()
galeria = GaleriaVideos()
cache = CacheDiario()
CREDITOS_DIARIOS = 10
creditos_restantes = creditos.obter_creditos(licenca)

# ============================================================
# STATUS DA API
# ============================================================
status_api = "✅ Conectado" if (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)) else "❌ Desconectado"

# ============================================================
# MENU LATERAL
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Menu")
    st.markdown(f"**🔌 Status API:** {status_api}")
    st.markdown("---")
    st.markdown("### 🎫 Créditos")
    st.metric("Disponíveis hoje", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
    
    if creditos_restantes == 0:
        st.warning("⚠️ Créditos esgotados! Volte amanhã.")
    
    st.markdown("---")
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logado = False
        st.rerun()
    
    st.caption(f"👤 Licença: {licenca[:10]}...")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA"
])

# ============================================================
# RENDERIZAR TABS
# ============================================================
with tab1:
    df = render_dashboard()

with tab2:
    if 'df' in locals():
        render_products(df)
    else:
        st.warning("Carregue o Dashboard primeiro")

with tab3:
    render_calendar()

with tab4:
    # Renderiza o gerador de vídeo
    st.markdown("## 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Gere vídeos para TikTok, Reels e Shorts com SnapGen AI")
    
    if not (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)):
        st.warning("⚠️ **Credenciais SnapGen não configuradas.**")
        st.info("Configure no arquivo .streamlit/secrets.toml")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        
        modelo = st.selectbox(
            "Modelo",
            ["SnapGen", "SnapGen Fast", "SnapGen Pro"],
            help="SnapGen Pro tem melhor qualidade | Fast é mais rápido"
        )
        
        imagem_upload = st.file_uploader(
            "Selecionar Imagem (opcional)",
            type=["png", "jpg", "jpeg", "webp"]
        )
        
        prompt = st.text_area(
            "Comando",
            placeholder="Descreva o vídeo que deseja gerar...",
            height=120
        )
    
    with col2:
        st.markdown("#### ⚙️ Configurações Técnicas")
        
        resolucao = st.radio(
            "Qualidade",
            ["480p", "720p", "1080p"],
            index=1
        )
        
        duracao = st.selectbox(
            "Duração (segundos)",
            [4, 6, 8, 10],
            index=1
        )
        
        estilo = st.selectbox(
            "Estilo Visual",
            ["Realista", "Cinematográfico", "Animado", "Minimalista", "Vintage"]
        )
        
        st.markdown("---")
        
        if creditos_restantes > 0:
            st.metric("🎫 Créditos restantes", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
        else:
            st.error("❌ Créditos esgotados! Volte amanhã.")
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif not (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)):
                st.error("❌ Credenciais SnapGen não configuradas.")
            elif creditos_restantes <= 0:
                st.error("❌ Créditos esgotados! Volte amanhã.")
            else:
                generator = SnapGenVideoGenerator(
                    api_key=SNAPGEN_API_KEY,
                    email=SNAPGEN_EMAIL,
                    password=SNAPGEN_PASSWORD,
                    galeria=galeria,
                    creditos=creditos
                )
                
                resultado = generator.gerar_video(
                    prompt=prompt,
                    licenca=licenca,
                    duracao=duracao,
                    resolucao=resolucao,
                    estilo=estilo,
                    modelo=modelo
                )
                
                if "erro" in resultado:
                    st.error(f"❌ {resultado['erro']}")
                else:
                    st.success("✅ Vídeo gerado com sucesso!")
                    
                    if os.path.exists(resultado["url"]):
                        st.video(resultado["url"])
                        with open(resultado["url"], "rb") as f:
                            st.download_button(
                                label="📥 Baixar Vídeo",
                                data=f,
                                file_name=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                    
                    st.rerun()
    
    # ===== GALERIA DE VÍDEOS =====
    st.markdown("---")
    st.markdown("### 🖼️ Galeria de Vídeos Gerados")
    
    videos = galeria.listar(12)
    
    if videos:
        cols = st.columns(4)
        for i, video in enumerate(videos[:8]):
            with cols[i % 4]:
                with st.container(border=True):
                    if os.path.exists(video.get("url", "")):
                        st.video(video["url"])
                        with open(video["url"], "rb") as f:
                            st.download_button(
                                label="📥 Baixar",
                                data=f,
                                file_name=os.path.basename(video["url"]),
                                mime="video/mp4",
                                key=f"dl_{video.get('id', i)}"
                            )
                    else:
                        st.video(video.get("url", "https://placehold.co/600x400/000000/FFFFFF?text=Video"))
                    
                    st.caption(f"🎬 {video.get('modelo', 'IA')}")
                    st.caption(f"📝 {video.get('prompt', '')[:40]}...")
                    st.caption(f"⏱️ {video.get('duracao', 6)}s | {video.get('resolucao', '480p')}")
                    
                    if st.button("🗑️ Remover", key=f"del_{video.get('id', i)}"):
                        if os.path.exists(video.get("url", "")):
                            os.remove(video["url"])
                        galeria.remover(video.get('id'))
                        st.rerun()
    else:
        st.info("📭 Nenhum vídeo gerado ainda. Crie seu primeiro vídeo acima!")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year} | Gerador de Vídeo com SnapGen AI")
''',

    "modules/__init__.py": '''# Torna a pasta 'modules' um pacote Python
# Este arquivo pode ficar vazio
''',

    "modules/auth.py": '''import streamlit as st
import time

LICENCA_PADRAO = "TESTE-AFILIADO-2026"

def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        licenca = st.text_input("Digite sua Licença de Acesso:", type="password")
        
        if st.button("🔓 Entrar", type="primary", use_container_width=True):
            if licenca == LICENCA_PADRAO:
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
    
    return st.session_state.get('licenca_usuario', LICENCA_PADRAO)
''',

    "modules/creditos.py": '''import json
import os
from datetime import datetime

class CreditosDiarios:
    def __init__(self, arquivo="creditos.json"):
        self.arquivo = arquivo
        self.dados = self.carregar()
        self.creditos_diarios = 10
    
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
    
    def obter_creditos(self, licenca):
        hoje = datetime.now().date().isoformat()
        chave = f"{licenca}_{hoje}"
        
        if chave in self.dados:
            return self.dados[chave]
        else:
            self.dados[chave] = self.creditos_diarios
            self.salvar()
            return self.creditos_diarios
    
    def usar_credito(self, licenca):
        hoje = datetime.now().date().isoformat()
        chave = f"{licenca}_{hoje}"
        
        if chave not in self.dados:
            self.dados[chave] = self.creditos_diarios
        
        if self.dados[chave] > 0:
            self.dados[chave] -= 1
            self.salvar()
            return True
        return False
''',

    "modules/galeria.py": '''import json
import os
from datetime import datetime

class GaleriaVideos:
    def __init__(self, arquivo="galeria_videos.json"):
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
        self.videos.insert(0, video)
        self.salvar()
        return video
    
    def listar(self, limite=10):
        return self.videos[:limite]
    
    def remover(self, video_id):
        self.videos = [v for v in self.videos if v.get('id') != video_id]
        self.salvar()
''',

    "modules/cache.py": '''import json
import os
from datetime import datetime

class CacheDiario:
    def __init__(self, arquivo="cache_tendencias.json"):
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
''',

    "modules/video_generator.py": '''import streamlit as st
import requests
import os
import time
from datetime import datetime

class SnapGenVideoGenerator:
    def __init__(self, api_key=None, email=None, password=None, galeria=None, creditos=None):
        self.api_key = api_key
        self.email = email
        self.password = password
        self.galeria = galeria
        self.creditos = creditos
        self.base_url = "https://api.snapgen.ai"
    
    def gerar_video(self, prompt, licenca, duracao=6, resolucao="480p", estilo="Realista", modelo="SnapGen"):
        if not self.api_key and not (self.email and self.password):
            return {"erro": "Credenciais SnapGen não configuradas"}
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Créditos diários esgotados. Volte amanhã!"}
        
        try:
            headers = {"Content-Type": "application/json"}
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.email and self.password:
                auth_response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"email": self.email, "password": self.password},
                    timeout=10
                )
                if auth_response.status_code == 200:
                    token = auth_response.json().get("token")
                    headers["Authorization"] = f"Bearer {token}"
                else:
                    return {"erro": f"Falha na autenticação: {auth_response.text}"}
            
            payload = {
                "prompt": prompt,
                "duration": duracao,
                "aspect_ratio": "9:16",
                "style": estilo,
                "model": modelo,
                "resolution": resolucao
            }
            
            st.info(f"🎬 Iniciando geração com SnapGen...")
            st.caption(f"⏱️ Duração: {duracao}s | 📐 9:16 | 📺 {resolucao}")
            
            endpoints = [
                f"{self.base_url}/generate",
                f"{self.base_url}/v1/generate",
                f"{self.base_url}/video/generate"
            ]
            
            response = None
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=60
                    )
                    if response.status_code == 200:
                        break
                except:
                    continue
            
            if response is None:
                return {"erro": "Nenhum endpoint disponível"}
            
            if response.status_code == 200:
                data = response.json()
                
                if "video_url" in data or "url" in data:
                    video_url = data.get("video_url") or data.get("url")
                    
                    video_response = requests.get(video_url, timeout=30)
                    if video_response.status_code == 200:
                        filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        with open(filename, "wb") as f:
                            f.write(video_response.content)
                        
                        video_info = {
                            "url": filename,
                            "prompt": prompt,
                            "duracao": duracao,
                            "resolucao": resolucao,
                            "estilo": estilo,
                            "modelo": modelo,
                            "status": "concluido"
                        }
                        
                        self.galeria.adicionar(video_info)
                        st.success("✅ Vídeo gerado com sucesso!")
                        return video_info
                    else:
                        return {"erro": f"Erro ao baixar vídeo: {video_response.status_code}"}
                else:
                    return {"erro": f"Erro: {data}"}
            else:
                return {"erro": f"Erro na geração: {response.text}"}
                
        except Exception as e:
            return {"erro": f"Erro na geração: {str(e)}"}
''',

    "modules/dashboard.py": '''import streamlit as st
import pandas as pd
from urllib.parse import quote
from datetime import datetime

PRODUTOS_SUGESTAO = [
    {"Produto": "casaco", "Categoria": "Moda", "Evento": "Férias Escolares", "Potencial": "🟢 Alto", "Pins": "3400 pins", "Crescimento": "+45%", "Views": "5.8M", "Resultados": "Histórico"},
    {"Produto": "blusa de lã", "Categoria": "Moda", "Evento": "Férias Escolares", "Potencial": "🟢 Alto", "Pins": "2800 pins", "Crescimento": "+38%", "Views": "4.2M", "Resultados": "Histórico"},
    {"Produto": "bota", "Categoria": "Moda", "Evento": "Férias Escolares", "Potencial": "🟡 Médio", "Pins": "1500 pins", "Crescimento": "+20%", "Views": "2.8M", "Resultados": "Histórico"},
    {"Produto": "cachecol", "Categoria": "Moda", "Evento": "Férias Escolares", "Potencial": "🟡 Médio", "Pins": "1200 pins", "Crescimento": "+15%", "Views": "1.9M", "Resultados": "Histórico"},
    {"Produto": "cobertor", "Categoria": "Casa", "Evento": "Férias Escolares", "Potencial": "🟡 Médio", "Pins": "950 pins", "Crescimento": "+12%", "Views": "1.5M", "Resultados": "Histórico"},
    {"Produto": "meia", "Categoria": "Moda", "Evento": "Férias Escolares", "Potencial": "🟡 Médio", "Pins": "800 pins", "Crescimento": "+10%", "Views": "1.1M", "Resultados": "Histórico"},
    {"Produto": "luva", "Categoria": "Moda", "Evento": "Férias Escolares", "Potencial": "🔴 Baixo", "Pins": "500 pins", "Crescimento": "+8%", "Views": "0.6M", "Resultados": "Histórico"},
    {"Produto": "jaqueta", "Categoria": "Moda", "Evento": "Férias Escolares", "Potencial": "🔴 Baixo", "Pins": "450 pins", "Crescimento": "+5%", "Views": "0.5M", "Resultados": "Histórico"}
]

def render_dashboard():
    st.title("📊 Minerador de Produtos")
    st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    st.markdown("## 📊 Visão Geral do Mês")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("""
        **Inverno no auge! Casacos e blusas de lã são os mais procurados. Aproveite as férias para conteúdo de viagens e looks de inverno.**
        """)
    with col2:
        st.markdown("""
        **Destaques:**
        - ✅ Produto em alta: **casaco** (Moda)
        - ✨ Crescimento médio: 19.1%
        - 🏠 Foco principal: Férias Escolares
        """)
    with col3:
        st.markdown("""
        **Melhor oportunidade:**
        - 🟢 Produtos com status Alto potencial
        """)
    
    st.markdown("---")
    
    st.markdown("## 🎯 Sugestões de Produtos para este Mês")
    
    df = pd.DataFrame(PRODUTOS_SUGESTAO)
    df["Buscar na Shopee"] = df["Produto"].apply(lambda x: f"https://shopee.com.br/search?keyword={quote(x)}")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Produto": "Produto",
            "Categoria": "Categoria",
            "Evento": "Evento Relacionado",
            "Potencial": "Potencial",
            "Pins": "Pins no Pinterest",
            "Crescimento": "Crescimento",
            "Views": "Visualizações TikTok",
            "Resultados": "Resultados",
            "Buscar na Shopee": st.column_config.LinkColumn("Buscar na Shopee", validate=False)
        }
    )
    
    st.caption("3 de 3 consultas SerpApi usadas hoje")
    
    st.markdown("---")
    
    st.markdown("## 💡 Insights Estratégicos")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏆 Produto com Maior Potencial")
        with st.container(border=True):
            st.markdown("### casaco")
            st.markdown("""
            - **Categoria:** Moda
            - **Pinterest:** 3400 pins
            - **Crescimento:** +45%
            - **TikTok:** 5.8M visualizações
            """)
            st.success("🚀 **Ação:** Crie conteúdo URGENTE sobre este produto!")
    
    with col2:
        st.markdown("### 📈 Tendência Mais Viral")
        with st.container(border=True):
            st.markdown("### casaco")
            st.markdown("""
            - **3400 pins no Pinterest**
            - **Crescimento de +45%**
            """)
            st.info("💡 **Dica:** Produto com alto engajamento nas redes sociais. Aproveite o momento para criar conteúdo patrocinado!")
    
    st.markdown("---")
    
    st.markdown("## 📌 Legenda de Potencial")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🟢 Alto**
        - Baixa concorrência, alta demanda
        """)
    with col2:
        st.markdown("""
        **🟡 Médio**
        - Concorrência moderada
        """)
    with col3:
        st.markdown("""
        **🔴 Baixo**
        - Mercado concorrido
        """)
    
    st.caption("Mais de 200 resultados no Google Shopping")
    
    return df
''',

    "modules/products.py": '''import streamlit as st
import pandas as pd

def render_products(df):
    st.markdown("## 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Produtos em alta baseados em tendências de mercado e datas comemorativas")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Produto": "Produto",
            "Categoria": "Categoria",
            "Evento": "Evento Relacionado",
            "Potencial": "Potencial",
            "Pins": "Pins no Pinterest",
            "Crescimento": "Crescimento",
            "Views": "Visualizações TikTok",
            "Resultados": "Resultados",
            "Buscar na Shopee": st.column_config.LinkColumn("Buscar na Shopee", validate=False)
        }
    )
''',

    "modules/calendar.py": '''import streamlit as st
from datetime import datetime

def render_calendar():
    st.markdown("## 📅 Calendário de Conteúdo Estratégico")
    st.caption("Selecione um mês para ver sugestões de produtos e insights")
    
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_selecionado = st.selectbox("Selecione o mês:", meses, index=datetime.now().month - 1)
    
    if mes_selecionado:
        st.markdown(f"### 📌 Eventos - {mes_selecionado}")
        
        eventos = {
            "01-01": {"nome": "Ano Novo", "produtos": ["decoração", "roupa branca", "espumante"]},
            "02-14": {"nome": "Dia dos Namorados", "produtos": ["perfume", "jantar", "kit romântico"]},
            "03-08": {"nome": "Dia da Mulher", "produtos": ["flores", "perfumes", "kits de beleza"]},
            "05-13": {"nome": "Dia das Mães", "produtos": ["perfume", "bolsa", "vestido"]},
            "06-12": {"nome": "Dia dos Namorados", "produtos": ["perfume", "vinho", "jantar"]},
            "07-09": {"nome": "Férias Escolares", "produtos": ["casaco", "blusa de lã", "bota"]},
            "08-14": {"nome": "Dia dos Pais", "produtos": ["ferramentas", "relógio", "cinto"]},
            "10-12": {"nome": "Dia das Crianças", "produtos": ["brinquedo", "boneca", "carrinho"]},
            "10-31": {"nome": "Halloween", "produtos": ["fantasia", "decoração", "doces"]},
            "11-25": {"nome": "Black Friday", "produtos": ["eletrônicos", "celular", "smartwatch"]},
            "12-25": {"nome": "Natal", "produtos": ["presentes", "árvore", "decoração"]},
            "12-31": {"nome": "Réveillon", "produtos": ["roupa branca", "espumante"]}
        }
        
        eventos_mes = {k: v for k, v in eventos.items() if k.startswith(f"{meses.index(mes_selecionado)+1:02d}")}
        
        if eventos_mes:
            col1, col2 = st.columns([1, 1])
            for i, (data, evento) in enumerate(eventos_mes.items()):
                with (col1 if i % 2 == 0 else col2):
                    with st.container(border=True):
                        dia = data.split("-")[1]
                        st.markdown(f"**📅 {dia}** - {evento['nome']}")
                        st.caption(f"📦 Produtos sugeridos: {', '.join(evento['produtos'][:3])}")
                        st.caption(f"⏰ Prepare-se com 7 dias de antecedência")
        else:
            st.info("📭 Nenhum evento programado para este mês.")
'''
}

# ============================================================
# CRIAR ARQUIVOS
# ============================================================
def criar_arquivos():
    for caminho, conteudo in ARQUIVOS.items():
        # Cria as pastas se não existirem
        pasta = os.path.dirname(caminho)
        if pasta and not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"📁 Pasta criada: {pasta}")
        
        # Escreve o arquivo
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"📄 Arquivo criado: {caminho}")

if __name__ == "__main__":
    print("🚀 Criando estrutura de arquivos...")
    criar_arquivos()
    print("\n✅ Estrutura criada com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Crie a pasta .streamlit/")
    print("2. Crie o arquivo .streamlit/secrets.toml")
    print("3. Adicione suas chaves no secrets.toml")
    print("4. Execute: streamlit run marketplace.app.py")
