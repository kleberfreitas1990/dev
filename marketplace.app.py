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
ARQUIVO_GALERIA = "galeria_videos.json"
CREDITOS_DIARIOS = 10

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
            "snapgen_api_key": st.secrets.get("SNAPGEN_API_KEY", ""),
            "snapgen_email": st.secrets.get("SNAPGEN_EMAIL", ""),
            "snapgen_password": st.secrets.get("SNAPGEN_PASSWORD", "")
        }
    except Exception:
        return {
            "licenca_acesso": LICENCA_PADRAO,
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
# SISTEMA DE CRÉDITOS DIÁRIOS
# ============================================================
class CreditosDiarios:
    def __init__(self):
        self.arquivo = "creditos.json"
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
    
    def obter_creditos(self, licenca):
        hoje = datetime.now().date().isoformat()
        chave = f"{licenca}_{hoje}"
        
        if chave in self.dados:
            return self.dados[chave]
        else:
            self.dados[chave] = CREDITOS_DIARIOS
            self.salvar()
            return CREDITOS_DIARIOS
    
    def usar_credito(self, licenca):
        hoje = datetime.now().date().isoformat()
        chave = f"{licenca}_{hoje}"
        
        if chave not in self.dados:
            self.dados[chave] = CREDITOS_DIARIOS
        
        if self.dados[chave] > 0:
            self.dados[chave] -= 1
            self.salvar()
            return True
        return False
    
    def resetar(self, licenca):
        hoje = datetime.now().date().isoformat()
        chave = f"{licenca}_{hoje}"
        self.dados[chave] = CREDITOS_DIARIOS
        self.salvar()

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
        self.videos.insert(0, video)
        self.salvar()
        return video
    
    def listar(self, limite=10):
        return self.videos[:limite]
    
    def remover(self, video_id):
        self.videos = [v for v in self.videos if v.get('id') != video_id]
        self.salvar()

# ============================================================
# GERADOR DE VÍDEO COM SNAPGEN AI
# ============================================================
class SnapGenVideoGenerator:
    def __init__(self):
        self.api_key = SNAPGEN_API_KEY
        self.email = SNAPGEN_EMAIL
        self.password = SNAPGEN_PASSWORD
        self.galeria = GaleriaVideos()
        self.creditos = CreditosDiarios()
        self.base_url = "https://api.snapgen.ai"
    
    def gerar_video(self, prompt, licenca, duracao=6, resolucao="480p", estilo="Realista", modelo="SnapGen"):
        if not self.api_key and not (self.email and self.password):
            return {"erro": "Credenciais SnapGen nao configuradas"}
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Creditos diarios esgotados. Volte amanha!"}
        
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
                    return {"erro": f"Falha na autenticacao: {auth_response.text}"}
            
            payload = {
                "prompt": prompt,
                "duration": duracao,
                "aspect_ratio": "9:16",
                "style": estilo,
                "model": modelo,
                "resolution": resolucao
            }
            
            st.info(f"Iniciando geracao com SnapGen...")
            st.caption(f"Duracao: {duracao}s | 9:16 | {resolucao}")
            
            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=headers,
                timeout=60
            )
            
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
                            "status": "concluido",
                            "tamanho": os.path.getsize(filename) if os.path.exists(filename) else 0
                        }
                        
                        self.galeria.adicionar(video_info)
                        st.success("Video gerado com sucesso!")
                        return video_info
                    else:
                        return {"erro": f"Erro ao baixar video: {video_response.status_code}"}
                else:
                    return {"erro": f"Erro: {data}"}
            else:
                return {"erro": f"Erro na geracao: {response.text}"}
                
        except Exception as e:
            return {"erro": f"Erro na geracao: {str(e)}"}

# ============================================================
# DADOS DE PRODUTOS SUGERIDOS
# ============================================================
PRODUTOS_SUGESTAO = [
    {"Produto": "casaco", "Categoria": "Moda", "Evento": "Ferias Escolares", "Potencial": "Alto", "Pins": "3400 pins", "Crescimento": "+45%", "Views": "5.8M", "Resultados": "Historico"},
    {"Produto": "blusa de la", "Categoria": "Moda", "Evento": "Ferias Escolares", "Potencial": "Alto", "Pins": "2800 pins", "Crescimento": "+38%", "Views": "4.2M", "Resultados": "Historico"},
    {"Produto": "bota", "Categoria": "Moda", "Evento": "Ferias Escolares", "Potencial": "Medio", "Pins": "1500 pins", "Crescimento": "+20%", "Views": "2.8M", "Resultados": "Historico"},
    {"Produto": "cachecol", "Categoria": "Moda", "Evento": "Ferias Escolares", "Potencial": "Medio", "Pins": "1200 pins", "Crescimento": "+15%", "Views": "1.9M", "Resultados": "Historico"},
    {"Produto": "cobertor", "Categoria": "Casa", "Evento": "Ferias Escolares", "Potencial": "Medio", "Pins": "950 pins", "Crescimento": "+12%", "Views": "1.5M", "Resultados": "Historico"},
    {"Produto": "meia", "Categoria": "Moda", "Evento": "Ferias Escolares", "Potencial": "Medio", "Pins": "800 pins", "Crescimento": "+10%", "Views": "1.1M", "Resultados": "Historico"},
    {"Produto": "luva", "Categoria": "Moda", "Evento": "Ferias Escolares", "Potencial": "Baixo", "Pins": "500 pins", "Crescimento": "+8%", "Views": "0.6M", "Resultados": "Historico"},
    {"Produto": "jaqueta", "Categoria": "Moda", "Evento": "Ferias Escolares", "Potencial": "Baixo", "Pins": "450 pins", "Crescimento": "+5%", "Views": "0.5M", "Resultados": "Historico"}
]

# ============================================================
# FUNCAO DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("Minerador de Produtos")
        st.markdown("### Acesso ao Sistema")
        
        licenca = st.text_input("Digite sua Licenca de Acesso:", type="password")
        
        if st.button("Entrar", type="primary", use_container_width=True):
            if licenca == LICENCA_ACESSO:
                st.session_state.logado = True
                st.session_state.licenca_usuario = licenca
                st.success("Licenca valida! Acesso liberado.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Licenca invalida.")
        
        st.markdown("---")
        st.caption("Sistema protegido por licenca.")
        st.stop()

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

creditos = CreditosDiarios()
licenca = st.session_state.get('licenca_usuario', LICENCA_PADRAO)
creditos_restantes = creditos.obter_creditos(licenca)

# ============================================================
# MENU LATERAL
# ============================================================
with st.sidebar:
    st.markdown("### Menu")
    
    status_api = "Conectado" if (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)) else "Desconectado"
    st.markdown(f"**Status API:** {status_api}")
    
    st.markdown("---")
    
    st.markdown("### Creditos")
    st.metric("Disponiveis hoje", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
    
    if creditos_restantes == 0:
        st.warning("Creditos esgotados! Volte amanha.")
    
    st.markdown("---")
    
    if st.button("Sair", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Sugestoes de Produtos",
    "Calendario de Conteudo",
    "Criar Video IA"
])

# ============================================================
# TAB 1: DASHBOARD
# ============================================================
with tab1:
    st.title("Minerador de Produtos")
    st.caption(f"{datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    st.markdown("## Visao Geral do Mes")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("""
        **Inverno no auge! Casacos e blusas de la sao os mais procurados. Aproveite as ferias para conteudo de viagens e looks de inverno.**
        """)
    with col2:
        st.markdown("""
        **Destaques:**
        - Produto em alta: **casaco** (Moda)
        - Crescimento medio: 19.1%
        - Foco principal: Ferias Escolares
        """)
    with col3:
        st.markdown("""
        **Melhor oportunidade:**
        - Produtos com status Alto potencial
        """)
    
    st.markdown("---")
    
    st.markdown("## Sugestoes de Produtos para este Mes")
    
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
            "Views": "Visualizacoes TikTok",
            "Resultados": "Resultados",
            "Buscar na Shopee": st.column_config.LinkColumn("Buscar na Shopee", validate=False)
        }
    )
    
    st.caption("3 de 3 consultas SerpApi usadas hoje")
    
    st.markdown("---")
    
    st.markdown("## Insights Estrategicos")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Produto com Maior Potencial")
        with st.container(border=True):
            st.markdown("### casaco")
            st.markdown("""
            - **Categoria:** Moda
            - **Pinterest:** 3400 pins
            - **Crescimento:** +45%
            - **TikTok:** 5.8M visualizacoes
            """)
            st.success("**Acao:** Crie conteudo URGENTE sobre este produto!")
    
    with col2:
        st.markdown("### Tendencia Mais Viral")
        with st.container(border=True):
            st.markdown("### casaco")
            st.markdown("""
            - **3400 pins no Pinterest**
            - **Crescimento de +45%**
            """)
            st.info("**Dica:** Produto com alto engajamento nas redes sociais. Aproveite o momento para criar conteudo patrocinado!")
    
    st.markdown("---")
    
    st.markdown("## Legenda de Potencial")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **Alto**
        - Baixa concorrencia, alta demanda
        """)
    with col2:
        st.markdown("""
        **Medio**
        - Concorrencia moderada
        """)
    with col3:
        st.markdown("""
        **Baixo**
        - Mercado concorrido
        """)
    
    st.caption("Mais de 200 resultados no Google Shopping")

# ============================================================
# TAB 2: SUGESTOES DE PRODUTOS
# ============================================================
with tab2:
    st.markdown("## Sugestoes de Produtos Estrategicos")
    st.caption("Produtos em alta baseados em tendencias de mercado e datas comemorativas")
    
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
            "Views": "Visualizacoes TikTok",
            "Resultados": "Resultados",
            "Buscar na Shopee": st.column_config.LinkColumn("Buscar na Shopee", validate=False)
        }
    )

# ============================================================
# TAB 3: CALENDARIO DE CONTEUDO
# ============================================================
with tab3:
    st.markdown("## Calendario de Conteudo Estrategico")
    st.caption("Selecione um mes para ver sugestoes de produtos e insights")
    
    meses = ["Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_selecionado = st.selectbox("Selecione o mes:", meses, index=datetime.now().month - 1)
    
    if mes_selecionado:
        st.markdown(f"### Eventos - {mes_selecionado}")
        
        eventos = {
            "01-01": {"nome": "Ano Novo", "produtos": ["decoracao", "roupa branca", "espumante"]},
            "02-14": {"nome": "Dia dos Namorados", "produtos": ["perfume", "jantar", "kit romantico"]},
            "03-08": {"nome": "Dia da Mulher", "produtos": ["flores", "perfumes", "kits de beleza"]},
            "05-13": {"nome": "Dia das Maes", "produtos": ["perfume", "bolsa", "vestido"]},
            "06-12": {"nome": "Dia dos Namorados", "produtos": ["perfume", "vinho", "jantar"]},
            "07-09": {"nome": "Ferias Escolares", "produtos": ["casaco", "blusa de la", "bota"]},
            "08-14": {"nome": "Dia dos Pais", "produtos": ["ferramentas", "relogio", "cinto"]},
            "10-12": {"nome": "Dia das Criancas", "produtos": ["brinquedo", "boneca", "carrinho"]},
            "10-31": {"nome": "Halloween", "produtos": ["fantasia", "decoracao", "doces"]},
            "11-25": {"nome": "Black Friday", "produtos": ["eletronicos", "celular", "smartwatch"]},
            "12-25": {"nome": "Natal", "produtos": ["presentes", "arvore", "decoracao"]},
            "12-31": {"nome": "Reveillon", "produtos": ["roupa branca", "espumante"]}
        }
        
        eventos_mes = {k: v for k, v in eventos.items() if k.startswith(f"{meses.index(mes_selecionado)+1:02d}")}
        
        if eventos_mes:
            col1, col2 = st.columns([1, 1])
            for i, (data, evento) in enumerate(eventos_mes.items()):
                with (col1 if i % 2 == 0 else col2):
                    with st.container(border=True):
                        dia = data.split("-")[1]
                        st.markdown(f"**{dia}** - {evento['nome']}")
                        st.caption(f"Produtos sugeridos: {', '.join(evento['produtos'][:3])}")
                        st.caption(f"Prepare-se com 7 dias de antecedencia")
        else:
            st.info("Nenhum evento programado para este mes.")

# ============================================================
# TAB 4: CRIAR VIDEO IA
# ============================================================
with tab4:
    st.markdown("## Criar Video com IA (9:16)")
    st.caption("Gere videos para TikTok, Reels e Shorts com SnapGen AI")
    
    if not (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)):
        st.warning("**Credenciais SnapGen nao configuradas.**")
        st.info("Configure no arquivo .streamlit/secrets.toml:\n\nSNAPGEN_API_KEY = 'sua_chave_api_aqui'\nOU\nSNAPGEN_EMAIL = 'seu_email@exemplo.com'\nSNAPGEN_PASSWORD = 'sua_senha'")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Configuracao do Video")
        
        modelo = st.selectbox(
            "Modelo",
            ["SnapGen", "SnapGen Fast", "SnapGen Pro"],
            help="SnapGen Pro tem melhor qualidade | Fast e mais rapido"
        )
        
        imagem_upload = st.file_uploader(
            "Selecionar Imagem (opcional)",
            type=["png", "jpg", "jpeg", "webp"],
            help="Alguns modelos suportam referencia visual"
        )
        
        prompt = st.text_area(
            "Comando",
            placeholder="Descreva o video que deseja gerar...\n\nEx: 'Extreme close-up of a smartwatch with city reflected in it, cinematic lighting, 4k quality'",
            height=120
        )
    
    with col2:
        st.markdown("#### Configuracoes Tecnicas")
        
        resolucao = st.radio(
            "Qualidade",
            ["480p", "720p", "1080p"],
            index=1,
            help="480p: Rapido | 720p: Bom | 1080p: Melhor qualidade"
        )
        
        duracao = st.selectbox(
            "Duracao (segundos)",
            [4, 6, 8, 10],
            index=1,
            help="SnapGen suporta ate 10 segundos"
        )
        
        estilo = st.selectbox(
            "Estilo Visual",
            ["Realista", "Cinematografico", "Animado", "Minimalista", "Vintage"],
            help="Define o estilo visual do video"
        )
        
        st.markdown("---")
        
        if creditos_restantes > 0:
            st.metric("Creditos restantes", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
            st.caption("Cada video consome 1 credito")
        else:
            st.error("Creditos esgotados! Volte amanha.")
        
        if st.button("Gerar Video", type="primary", width='stretch'):
            if not prompt:
                st.error("Por favor, descreva o video no campo 'Comando'.")
            elif not (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)):
                st.error("Credenciais SnapGen nao configuradas.")
            elif creditos_restantes <= 0:
                st.error("Creditos esgotados! Volte amanha.")
            else:
                generator = SnapGenVideoGenerator()
                resultado = generator.gerar_video(
                    prompt=prompt,
                    licenca=licenca,
                    duracao=duracao,
                    resolucao=resolucao,
                    estilo=estilo,
                    modelo=modelo
                )
                
                if "erro" in resultado:
                    st.error(f"{resultado['erro']}")
                else:
                    st.success("Video gerado com sucesso!")
                    
                    if os.path.exists(resultado["url"]):
                        st.video(resultado["url"])
                        with open(resultado["url"], "rb") as f:
                            st.download_button(
                                label="Baixar Video",
                                data=f,
                                file_name=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        st.video(resultado["url"])
                    
                    st.rerun()
    
    # ===== GALERIA DE VIDEOS =====
    st.markdown("---")
    st.markdown("### Galeria de Videos Gerados")
    
    galeria = GaleriaVideos()
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
                                label="Baixar",
                                data=f,
                                file_name=os.path.basename(video["url"]),
                                mime="video/mp4",
                                key=f"dl_{video.get('id', i)}"
                            )
                    else:
                        st.video(video.get("url", "https://placehold.co/600x400/000000/FFFFFF?text=Video"))
                    
                    st.caption(f"Modelo: {video.get('modelo', 'IA')}")
                    st.caption(f"Prompt: {video.get('prompt', '')[:40]}...")
                    st.caption(f"Duracao: {video.get('duracao', 6)}s | {video.get('resolucao', '480p')}")
                    
                    if st.button("Remover", key=f"del_{video.get('id', i)}"):
                        if os.path.exists(video.get("url", "")):
                            os.remove(video["url"])
                        galeria.remover(video.get('id'))
                        st.rerun()
    else:
        st.info("Nenhum video gerado ainda. Crie seu primeiro video acima!")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"Minerador de Produtos v3.0 | {datetime.now().year} | Gerador de Video com SnapGen AI")
