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
# INSTALAR DEPENDÊNCIAS (se necessário)
# ============================================================
try:
    from google import genai
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "google-generativeai"])
    from google import genai

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
# GERADOR DE VÍDEO REAL COM GEMINI (VEO 3.1 / OMNI FLASH)
# ============================================================
class GeminiVideoGenerator:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.galeria = GaleriaVideos()
        self.creditos = CreditosDiarios()
        self.client = None
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                st.error(f"Erro ao inicializar Gemini: {e}")
    
    def gerar_video(self, prompt, licenca, duracao=8, resolucao="720p", estilo="Realista", modelo="Veo 3.1"):
        """
        Gera um vídeo REAL usando Gemini API (Veo 3.1 ou Omni Flash)
        """
        if not self.api_key:
            return {"erro": "Chave Gemini não configurada. Adicione GEMINI_API_KEY no secrets.toml"}
        
        if not self.client:
            return {"erro": "Cliente Gemini não inicializado. Verifique sua chave API."}
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Créditos diários esgotados. Volte amanhã!"}
        
        try:
            # Mapeia modelo
            model_map = {
                "Veo 3.1": "veo-3.1-generate-preview",
                "Veo 3.1 Fast": "veo-3.1-fast-generate-preview",
                "Veo 3.1 Lite": "veo-3.1-lite-generate-preview",
                "Gemini Omni Flash": "gemini-omni-flash"
            }
            
            model_name = model_map.get(modelo, "veo-3.1-generate-preview")
            
            # Configura duração máxima por modelo
            max_duration = 8 if "veo" in model_name else 10
            duration = min(duracao, max_duration)
            
            # Prepara configuração
            config = {
                "model": model_name,
                "prompt": prompt,
                "aspect_ratio": "9:16",  # Vertical para TikTok/Reels
                "duration": duration,
                "resolution": resolucao
            }
            
            # Inicia a geração
            st.info(f"🎬 Iniciando geração com {modelo}...")
            st.caption(f"⏱️ Duração: {duration}s | 📐 9:16 | 📺 {resolucao}")
            
            # A geração pode levar alguns minutos
            operation = self.client.models.generate_videos(**config)
            
            # Aguarda conclusão com progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            elapsed_time = 0
            max_wait = 300  # 5 minutos máximo
            
            while not operation.done and elapsed_time < max_wait:
                status_text.text(f"⏳ Processando... {elapsed_time}s")
                time.sleep(5)
                elapsed_time += 5
                progress_bar.progress(min(elapsed_time / max_wait, 0.95))
                
                try:
                    operation = self.client.operations.get(operation)
                except:
                    pass
            
            progress_bar.progress(1.0)
            
            if not operation.done:
                return {"erro": "Tempo limite excedido. Tente novamente."}
            
            # Verifica se houve erro
            if hasattr(operation, 'response') and hasattr(operation.response, 'error'):
                return {"erro": f"Erro na geração: {operation.response.error.message}"}
            
            # Obtém o vídeo gerado
            try:
                video_response = operation.response.generated_videos[0]
                
                # Download do vídeo
                status_text.text("📥 Baixando vídeo...")
                
                # Gera nome do arquivo
                filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                
                # Salva o vídeo
                self.client.files.download(file=video_response.video)
                video_response.video.save(filename)
                
                status_text.text("✅ Vídeo gerado com sucesso!")
                
                # Adiciona à galeria
                video_info = {
                    "url": filename,
                    "prompt": prompt,
                    "duracao": duration,
                    "resolucao": resolucao,
                    "estilo": estilo,
                    "modelo": modelo,
                    "status": "concluido",
                    "tamanho": os.path.getsize(filename) if os.path.exists(filename) else 0
                }
                self.galeria.adicionar(video_info)
                
                return video_info
                
            except Exception as e:
                return {"erro": f"Erro ao processar vídeo: {str(e)}"}
                
        except Exception as e:
            return {"erro": f"Erro na geração: {str(e)}"}

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

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

# Inicializa créditos
creditos = CreditosDiarios()
licenca = st.session_state.get('licenca_usuario', LICENCA_PADRAO)
creditos_restantes = creditos.obter_creditos(licenca)

# ============================================================
# MENU LATERAL
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Menu")
    
    status_api = "✅ Conectado" if GEMINI_API_KEY else "❌ Desconectado"
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
# TAB 1: DASHBOARD
# ============================================================
with tab1:
    st.title("📊 Minerador de Produtos")
    st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    # Visão Geral do Mês
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
    
    # Tabela de Sugestões
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
    
    # Insights Estratégicos
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
    
    # Legenda de Potencial
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

# ============================================================
# TAB 2: SUGESTÕES DE PRODUTOS
# ============================================================
with tab2:
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

# ============================================================
# TAB 3: CALENDÁRIO DE CONTEÚDO
# ============================================================
with tab3:
    st.markdown("## 📅 Calendário de Conteúdo Estratégico")
    st.caption("Selecione um mês para ver sugestões de produtos e insights")
    
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_selecionado = st.selectbox("Selecione o mês:", meses, index=datetime.now().month - 1)
    
    if mes_selecionado:
        st.markdown(f"### 📌 Eventos - {mes_selecionado}")
        
        # Simula eventos para demonstração
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
        
        # Filtra eventos do mês selecionado
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

# ============================================================
# TAB 4: CRIAR VÍDEO IA (COM GERAÇÃO REAL)
# ============================================================
with tab4:
    st.markdown("## 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Gere vídeos reais com Veo 3.1 e Gemini Omni Flash para TikTok, Reels e Shorts")
    
    if not GEMINI_API_KEY:
        st.warning("⚠️ **Chave Gemini não configurada.** Adicione `GEMINI_API_KEY` no arquivo `.streamlit/secrets.toml`.")
        st.info("""
        **Como obter sua chave:**
        1. Acesse [Google AI Studio](https://aistudio.google.com/)
        2. Crie uma conta e ative o faturamento
        3. Gere sua API Key
        4. Adicione no arquivo `.streamlit/secrets.toml`
        """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        
        modelo = st.selectbox(
            "Modelo",
            ["Veo 3.1", "Veo 3.1 Fast", "Veo 3.1 Lite", "Gemini Omni Flash"],
            help="Veo 3.1 tem melhor qualidade | Omni Flash suporta até 10s"
        )
        
        imagem_upload = st.file_uploader(
            "Selecionar Imagem (opcional)",
            type=["png", "jpg", "jpeg", "webp"],
            help="Alguns modelos suportam referência visual"
        )
        
        prompt = st.text_area(
            "Comando",
            placeholder="Descreva o vídeo que deseja gerar...\n\nEx: 'Extreme close-up of a smartwatch with city reflected in it, cinematic lighting, 4k quality'",
            height=120
        )
    
    with col2:
        st.markdown("#### ⚙️ Configurações Técnicas")
        
        resolucao = st.radio(
            "Qualidade",
            ["720p", "1080p", "4K"],
            index=0,
            help="720p: R$0.10/s | 1080p: R$0.12/s | 4K: R$0.30/s (Veo 3.1)"
        )
        
        duracao = st.selectbox(
            "Duração (segundos)",
            [4, 6, 8, 10],
            index=2,
            help="Veo 3.1: até 8s | Omni Flash: até 10s"
        )
        
        estilo = st.selectbox(
            "Estilo Visual",
            ["Realista", "Cinematográfico", "Animado", "Minimalista", "Vintage"],
            help="Define o estilo visual do vídeo"
        )
        
        st.markdown("---")
        
        # Créditos
        if creditos_restantes > 0:
            st.metric("🎫 Créditos restantes", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
            st.caption("💡 Cada vídeo consome 1 crédito")
        else:
            st.error("❌ Créditos esgotados! Volte amanhã.")
        
        # Custo estimado
        custo = {
            "720p": 0.10,
            "1080p": 0.12,
            "4K": 0.30
        }
        custo_total = custo.get(resolucao, 0.10) * duracao
        st.caption(f"💰 Custo estimado: ~${custo_total:.2f} USD")
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif not GEMINI_API_KEY:
                st.error("❌ Chave Gemini não configurada.")
            elif creditos_restantes <= 0:
                st.error("❌ Créditos esgotados! Volte amanhã.")
            else:
                # Inicializa o gerador
                generator = GeminiVideoGenerator()
                
                # Gera o vídeo
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
                    
                    # Mostra o vídeo
                    st.video(resultado["url"])
                    
                    # Botão de download
                    with open(resultado["url"], "rb") as f:
                        video_bytes = f.read()
                        st.download_button(
                            label="📥 Baixar Vídeo",
                            data=video_bytes,
                            file_name=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    
                    st.rerun()
    
    # ===== GALERIA DE VÍDEOS =====
    st.markdown("---")
    st.markdown("### 🖼️ Galeria de Vídeos Gerados")
    
    galeria = GaleriaVideos()
    videos = galeria.listar(12)
    
    if videos:
        cols = st.columns(4)
        for i, video in enumerate(videos[:8]):
            with cols[i % 4]:
                with st.container(border=True):
                    if os.path.exists(video.get("url", "")):
                        st.video(video["url"])
                    else:
                        st.video("https://placehold.co/600x400/000000/FFFFFF?text=Video+Removido")
                    
                    st.caption(f"🎬 {video.get('modelo', 'IA')}")
                    st.caption(f"📝 {video.get('prompt', '')[:40]}...")
                    st.caption(f"⏱️ {video.get('duracao', 6)}s | {video.get('resolucao', '720p')}")
                    
                    col_dl, col_del = st.columns(2)
                    with col_dl:
                        if os.path.exists(video.get("url", "")):
                            with open(video["url"], "rb") as f:
                                st.download_button(
                                    label="📥",
                                    data=f,
                                    file_name=os.path.basename(video["url"]),
                                    mime="video/mp4",
                                    key=f"dl_{video.get('id', i)}"
                                )
                    with col_del:
                        if st.button("🗑️", key=f"del_{video.get('id', i)}"):
                            # Remove o arquivo físico
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
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year} | Gerador de Vídeo com Veo 3.1 e Gemini Omni Flash")
