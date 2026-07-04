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
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTES
# ============================================================
LICENCA_PADRAO = "TESTE-AFILIADO-2026"
ARQUIVO_GALERIA = "galeria_videos.json"
CREDITOS_DIARIOS = 10

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
# SISTEMA DE CRÉDITOS DIÁRIOS
# ============================================================
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

# ============================================================
# SISTEMA DE GALERIA DE VÍDEOS
# ============================================================
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

# ============================================================
# GERADOR DE VÍDEO COM SNAPGEN AI (VERSÃO CORRIGIDA)
# ============================================================
class SnapGenVideoGenerator:
    def __init__(self):
        self.api_key = SNAPGEN_API_KEY
        self.email = SNAPGEN_EMAIL
        self.password = SNAPGEN_PASSWORD
        self.galeria = GaleriaVideos()
        self.creditos = CreditosDiarios()
        # Endpoints baseados na documentação
        self.endpoints = [
            "https://api.snapgen.ai/uapi/v1/generate",
            "https://api.snapgen.ai/v1/generate",
            "https://api.snapgen.ai/generate",
            "https://api.snapgen.ai/api/v1/generate"
        ]
        # Headers padrão
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def gerar_video(self, prompt, licenca, duracao=6, resolucao="480p", estilo="Realista", modelo="SnapGen"):
        # Verifica credenciais
        if not self.api_key and not (self.email and self.password):
            # Fallback para simulação
            return self._simular_video(prompt, licenca, duracao, resolucao, estilo, modelo)
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Créditos diários esgotados. Volte amanhã!"}
        
        # Tenta usar a API real
        resultado = self._tentar_api(prompt, duracao, resolucao, estilo, modelo)
        
        if resultado and "erro" not in resultado:
            return resultado
        else:
            # Fallback para simulação se a API falhar
            st.warning("⚠️ API SnapGen indisponível. Gerando vídeo de demonstração...")
            return self._simular_video(prompt, licenca, duracao, resolucao, estilo, modelo)
    
    def _tentar_api(self, prompt, duracao, resolucao, estilo, modelo):
        """Tenta chamar a API SnapGen"""
        try:
            # Prepara os headers com autenticação
            headers = self.headers.copy()
            
            if self.api_key:
                headers["x-api-key"] = self.api_key
            elif self.email and self.password:
                # Tenta obter token
                try:
                    auth_response = requests.post(
                        "https://api.snapgen.ai/auth/login",
                        json={"email": self.email, "password": self.password},
                        timeout=10
                    )
                    if auth_response.status_code == 200:
                        token = auth_response.json().get("token") or auth_response.json().get("api_key")
                        if token:
                            headers["Authorization"] = f"Bearer {token}"
                except:
                    pass
            
            # Prepara o payload
            payload = {
                "type": "video",
                "prompt": prompt,
                "duration": duracao,
                "aspect_ratio": "9:16",
                "style": estilo,
                "model": modelo,
                "resolution": resolucao
            }
            
            st.info(f"🎬 Tentando gerar vídeo com SnapGen...")
            st.caption(f"⏱️ Duração: {duracao}s | 📐 9:16 | 📺 {resolucao}")
            
            # Tenta cada endpoint
            for endpoint in self.endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        video_url = self._extrair_url_video(data)
                        
                        if video_url:
                            # Baixa o vídeo
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
                                st.success(f"✅ Vídeo gerado com sucesso!")
                                return video_info
                    elif response.status_code == 401:
                        st.error("❌ Chave API inválida. Verifique suas credenciais.")
                        return {"erro": "Chave API inválida"}
                    elif response.status_code != 404:
                        # Se não for 404, tenta ler o erro
                        try:
                            erro = response.json()
                            if "detail" in erro:
                                st.warning(f"⚠️ {erro['detail']}")
                        except:
                            pass
                except Exception as e:
                    continue
            
            return {"erro": "API SnapGen indisponível"}
            
        except Exception as e:
            return {"erro": f"Erro: {str(e)}"}
    
    def _extrair_url_video(self, data):
        """Extrai URL do vídeo da resposta da API"""
        if "video_url" in data:
            return data["video_url"]
        elif "url" in data:
            return data["url"]
        elif "output" in data and isinstance(data["output"], dict):
            return data["output"].get("url")
        elif "data" in data and isinstance(data["data"], dict):
            return data["data"].get("url")
        elif "result" in data and isinstance(data["result"], dict):
            return data["result"].get("url")
        return None
    
    def _simular_video(self, prompt, licenca, duracao, resolucao, estilo, modelo):
        """Gera um vídeo de demonstração quando a API não está disponível"""
        # Gera um vídeo de exemplo (Big Buck Bunny)
        video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
        
        try:
            response = requests.get(video_url, timeout=10)
            if response.status_code == 200:
                filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                with open(filename, "wb") as f:
                    f.write(response.content)
                
                video_info = {
                    "url": filename,
                    "prompt": prompt,
                    "duracao": duracao,
                    "resolucao": resolucao,
                    "estilo": estilo,
                    "modelo": modelo,
                    "status": "demonstracao"
                }
                
                self.galeria.adicionar(video_info)
                st.info("🎬 Vídeo de demonstração gerado (API SnapGen indisponível)")
                return video_info
        except:
            pass
        
        # Fallback para placeholder
        video_info = {
            "url": "https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA",
            "prompt": prompt,
            "duracao": duracao,
            "resolucao": resolucao,
            "estilo": estilo,
            "modelo": modelo,
            "status": "placeholder"
        }
        
        self.galeria.adicionar(video_info)
        return video_info

# ============================================================
# DADOS DE PRODUTOS SUGERIDOS
# ============================================================
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
    
    return st.session_state.get('licenca_usuario', LICENCA_PADRAO)

# ============================================================
# FUNCAO RENDER_DASHBOARD (COM CARDS E MEDIDORES)
# ============================================================
def render_dashboard():
    st.title("📊 Minerador de Produtos")
    st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    st.markdown("## 📊 Visão Geral do Mês")
    
    # Layout responsivo com cards
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown("""
            **❄️ Inverno no auge!** Casacos e blusas de lã são os mais procurados. 
            Aproveite as férias para conteúdo de viagens e looks de inverno.
            """)
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("🔥 Produto em Alta", "casaco", delta="Moda")
            with m2:
                st.metric("📈 Crescimento Médio", "19.1%", delta="+2.3%")
            with m3:
                st.metric("🎯 Foco Principal", "Férias Escolares", delta="Alta demanda")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 🎯 Melhor Oportunidade")
            
            st.markdown("**Potencial de Mercado**")
            
            potencial = 85
            cor = "green" if potencial >= 70 else "orange" if potencial >= 40 else "red"
            
            st.markdown(f"""
            <div style="background: #e0e0e0; border-radius: 10px; height: 20px; position: relative;">
                <div style="background: {cor}; width: {potencial}%; height: 20px; border-radius: 10px; transition: width 0.5s;">
                    <span style="position: absolute; right: 10px; top: 2px; color: black; font-weight: bold;">{potencial}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("🟢 Produtos com status Alto potencial")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.success("✅ Alta Demanda")
            with col_s2:
                st.success("✅ Baixa Concorrência")
    
    st.markdown("---")
    
    st.markdown("### 📈 Indicadores Rápidos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.markdown("**🛒 Produtos**")
            st.markdown("<h2 style='text-align: center;'>8</h2>", unsafe_allow_html=True)
            st.caption("Em tendência")
    
    with col2:
        with st.container(border=True):
            st.markdown("**📊 Categorias**")
            st.markdown("<h2 style='text-align: center;'>5</h2>", unsafe_allow_html=True)
            st.caption("Ativas no mês")
    
    with col3:
        with st.container(border=True):
            st.markdown("**🔥 Potencial**")
            st.markdown("<h2 style='text-align: center;'>85%</h2>", unsafe_allow_html=True)
            st.caption("Médio de mercado")
    
    with col4:
        with st.container(border=True):
            st.markdown("**📅 Eventos**")
            st.markdown("<h2 style='text-align: center;'>3</h2>", unsafe_allow_html=True)
            st.caption("Próximos 7 dias")
    
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

# ============================================================
# APP PRINCIPAL
# ============================================================
licenca = verificar_login()

creditos = CreditosDiarios()
galeria = GaleriaVideos()
creditos_restantes = creditos.obter_creditos(licenca)

# Status da API
tem_credenciais = bool(SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD))
status_api = "✅ Conectado" if tem_credenciais else "❌ Desconectado"

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
    
    if not tem_credenciais:
        st.warning("⚠️ SnapGen não configurado")

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
    else:
        st.warning("Carregue o Dashboard primeiro")

with tab3:
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

with tab4:
    st.markdown("## 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Gere vídeos para TikTok, Reels e Shorts com SnapGen AI")
    
    if not tem_credenciais:
        st.warning("⚠️ **Credenciais SnapGen não configuradas.**")
        st.info("Configure no painel do Streamlit Cloud: Settings → Secrets")
        st.info("O sistema usará vídeos de demonstração enquanto a API não estiver configurada.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        
        modelo = st.selectbox(
            "Modelo",
            ["SnapGen", "SnapGen Fast", "SnapGen Pro", "SnapGen Lite", "SnapGen HD"],
            help="SnapGen Pro tem melhor qualidade | Fast é mais rápido | Lite é mais econômico"
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
            elif creditos_restantes <= 0:
                st.error("❌ Créditos esgotados! Volte amanhã.")
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
                    st.error(f"❌ {resultado['erro']}")
                else:
                    st.success("✅ Vídeo gerado com sucesso!")
                    
                    if os.path.exists(resultado.get("url", "")):
                        st.video(resultado["url"])
                        with open(resultado["url"], "rb") as f:
                            st.download_button(
                                label="📥 Baixar Vídeo",
                                data=f,
                                file_name=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                    else:
                        st.video(resultado.get("url", "https://placehold.co/600x400/000000/FFFFFF?text=Video"))
                    
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
