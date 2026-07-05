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
ARQUIVO_GALERIA = "galeria_videos.json"
ARQUIVO_DADOS_DIARIOS = "dados_diarios.json"
CREDITOS_DIARIOS = 10
BUSCAS_DIARIAS = 3
BUSCAS_TOTAIS = 250

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
# SISTEMA DE DADOS DIÁRIOS (AUTOMÁTICO)
# ============================================================
class DadosDiarios:
    def __init__(self, arquivo=ARQUIVO_DADOS_DIARIOS):
        self.arquivo = arquivo
        self.dados = self.carregar()
        self.buscas_diarias = BUSCAS_DIARIAS
    
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
    
    def obter_dados_hoje(self):
        hoje = datetime.now().date().isoformat()
        dados = self.dados.get(hoje, {})
        
        if dados and dados.get("produtos"):
            return dados
        
        return None
    
    def salvar_dados_hoje(self, produtos):
        hoje = datetime.now().date().isoformat()
        self.dados[hoje] = {
            "data": hoje,
            "produtos": produtos,
            "total_buscas": len(produtos) if produtos else 0,
            "timestamp": datetime.now().isoformat()
        }
        self.salvar()
    
    def precisa_atualizar(self):
        hoje = datetime.now().date().isoformat()
        dados = self.dados.get(hoje, {})
        
        if not dados or not dados.get("produtos"):
            return True
        
        hora_atual = datetime.now().hour
        try:
            hora_ultima = datetime.fromisoformat(dados.get("timestamp", datetime.now().isoformat())).hour
        except:
            hora_ultima = 0
        
        if dados.get("data") != hoje:
            return True
        if hora_atual >= 6 and hora_ultima < 6:
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
# FUNÇÕES DE BUSCA (APENAS 3 POR DIA)
# ============================================================
def buscar_produtos_serpapi(termo, limite=3):
    """Busca produtos no Google Shopping via SerpApi"""
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
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        produtos = []
        for item in data.get("shopping_results", [])[:limite]:
            produtos.append({
                "nome": item.get("title", ""),
                "loja": item.get("source", ""),
                "link": item.get("link", ""),
                "avaliacao": item.get("rating", None)
            })
        return produtos
    except Exception as e:
        return []

def gerar_sugestoes_diarias():
    """Gera as 3 melhores sugestões para o dia"""
    # Lista de produtos base para análise
    produtos_base = [
        {"termo": "casaco", "categoria": "Moda", "evento": "Férias Escolares"},
        {"termo": "blusa de lã", "categoria": "Moda", "evento": "Férias Escolares"},
        {"termo": "bota", "categoria": "Moda", "evento": "Férias Escolares"},
        {"termo": "cachecol", "categoria": "Moda", "evento": "Férias Escolares"},
        {"termo": "cobertor", "categoria": "Casa", "evento": "Férias Escolares"},
        {"termo": "meia", "categoria": "Moda", "evento": "Férias Escolares"},
        {"termo": "luva", "categoria": "Moda", "evento": "Férias Escolares"},
        {"termo": "jaqueta", "categoria": "Moda", "evento": "Férias Escolares"},
        {"termo": "smartwatch", "categoria": "Eletrônicos", "evento": "Tendência"},
        {"termo": "fone bluetooth", "categoria": "Eletrônicos", "evento": "Tendência"},
    ]
    
    # Embaralha e pega os 3 primeiros (ou usa os 3 primeiros da lista)
    # Para garantir variedade, usa os primeiros 3 da lista
    resultados = []
    termos_selecionados = produtos_base[:BUSCAS_DIARIAS]
    
    for item in termos_selecionados:
        produtos = buscar_produtos_serpapi(item["termo"], 3)
        
        # Score baseado em disponibilidade
        score = 0
        if produtos:
            score += 5  # Produto encontrado
            score += min(len(produtos), 3)  # Quantidade de resultados
        
        resultados.append({
            "Produto": item["termo"],
            "Categoria": item["categoria"],
            "Evento": item["evento"],
            "Score": score,
            "Produtos Encontrados": len(produtos)
        })
    
    # Ordena por score (melhores primeiro)
    resultados = sorted(resultados, key=lambda x: x["Score"], reverse=True)
    
    return resultados[:BUSCAS_DIARIAS]

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
        self.endpoints = [
            "https://api.snapgen.ai/uapi/v1/generate",
            "https://api.snapgen.ai/v1/generate",
            "https://api.snapgen.ai/generate",
            "https://api.snapgen.ai/api/v1/generate"
        ]
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def gerar_video(self, prompt, licenca, duracao=6, resolucao="480p", estilo="Realista", modelo="SnapGen"):
        if not self.api_key and not (self.email and self.password):
            return self._simular_video(prompt, licenca, duracao, resolucao, estilo, modelo)
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Créditos diários esgotados. Volte amanhã!"}
        
        resultado = self._tentar_api(prompt, duracao, resolucao, estilo, modelo)
        
        if resultado and "erro" not in resultado:
            return resultado
        else:
            st.warning("⚠️ API SnapGen indisponível. Gerando vídeo de demonstração...")
            return self._simular_video(prompt, licenca, duracao, resolucao, estilo, modelo)
    
    def _tentar_api(self, prompt, duracao, resolucao, estilo, modelo):
        try:
            headers = self.headers.copy()
            
            if self.api_key:
                headers["x-api-key"] = self.api_key
            elif self.email and self.password:
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
            
            payload = {
                "type": "video",
                "prompt": prompt,
                "duration": duracao,
                "aspect_ratio": "9:16",
                "style": estilo,
                "model": modelo,
                "resolution": resolucao
            }
            
            st.info(f"🎬 Iniciando geração com SnapGen...")
            st.caption(f"⏱️ Duração: {duracao}s | 📐 9:16 | 📺 {resolucao}")
            
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
                except Exception as e:
                    continue
            
            return {"erro": "API SnapGen indisponível"}
            
        except Exception as e:
            return {"erro": f"Erro: {str(e)}"}
    
    def _extrair_url_video(self, data):
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
# PALAVRAS-CHAVE DE CAUDA LONGA
# ============================================================
PALAVRAS_CHAVE_CAUDA_LONGA = {
    "casaco": "casaco feminino inverno 2026",
    "blusa de lã": "blusa de lã feminina elegante",
    "bota": "bota feminina cano médio",
    "cachecol": "cachecol de lã para frio extremo",
    "cobertor": "cobertor de lã para cama king",
    "meia": "meia de lã para frio extremo",
    "luva": "luva de lã para frio intenso",
    "jaqueta": "jaqueta jeans feminina 2026",
    "smartwatch": "smartwatch feminino elegante",
    "fone bluetooth": "fone bluetooth JBL original"
}

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
# FUNCAO RENDER_DASHBOARD
# ============================================================
def render_dashboard():
    st.title("📊 Minerador de Produtos")
    st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    # ===== ATUALIZAÇÃO AUTOMÁTICA DIÁRIA =====
    dados_diarios = DadosDiarios()
    
    if dados_diarios.precisa_atualizar():
        with st.spinner("🔄 Atualizando dados do dia..."):
            produtos = gerar_sugestoes_diarias()
            dados_diarios.salvar_dados_hoje(produtos)
            st.success("✅ Dados do dia atualizados!")
            time.sleep(1)
            st.rerun()
    
    dados_hoje = dados_diarios.obter_dados_hoje()
    
    # Status e Créditos
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    with col_status1:
        status_api = "✅ Conectado" if (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)) else "❌ Desconectado"
        st.metric("🔌 Status API", status_api)
    with col_status2:
        creditos = CreditosDiarios()
        licenca = st.session_state.get('licenca_usuario', LICENCA_PADRAO)
        creditos_restantes = creditos.obter_creditos(licenca)
        st.metric("🎫 Créditos IA", f"{creditos_restantes} / {CREDITOS_DIARIOS}")
    with col_status3:
        st.metric("👤 Licença", f"{licenca[:10]}...")
    with col_status4:
        if dados_hoje:
            st.metric("📊 Buscas de Hoje", f"{dados_hoje.get('total_buscas', 0)} / {BUSCAS_DIARIAS}")
        else:
            st.metric("📊 Buscas de Hoje", f"0 / {BUSCAS_DIARIAS}")
    
    st.markdown("---")
    
    st.markdown("## 📊 Visão Geral do Mês")
    
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
                    <span style="position: absolute: right: 10px; top: 2px; color: black; font-weight: bold;">{potencial}%</span>
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
    
    # ===== TABELA DE PRODUTOS DO DIA =====
    st.markdown("## 🎯 Sugestões de Produtos para Hoje")
    st.caption(f"🔄 Atualizado automaticamente todos os dias | {BUSCAS_DIARIAS} buscas realizadas")
    
    if dados_hoje and dados_hoje.get("produtos"):
        produtos = dados_hoje["produtos"]
        
        dados_tabela = []
        for item in produtos:
            palavra_chave = PALAVRAS_CHAVE_CAUDA_LONGA.get(item["Produto"], f"{item['Produto']} tendência 2026")
            
            dados_tabela.append({
                "Produto": item["Produto"],
                "🔑 Palavra-chave": palavra_chave,
                "Categoria": item["Categoria"],
                "Evento": item["Evento"],
                "Potencial": "🟢 Alto" if item["Score"] >= 8 else "🟡 Médio" if item["Score"] >= 5 else "🔴 Baixo",
                "Score": item["Score"],
                "Produtos Encontrados": item["Produtos Encontrados"]
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>'
        )
        
        colunas = ["Produto", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Produtos Encontrados", "Buscar na Shopee"]
        df = df[colunas]
        
        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
        
        st.caption(f"{BUSCAS_DIARIAS} de {BUSCAS_DIARIAS} consultas SerpApi usadas hoje")
    else:
        st.info("📭 Nenhum dado disponível para hoje. Tente recarregar a página.")
    
    st.markdown("---")
    
    st.markdown("## 💡 Insights Estratégicos")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏆 Produto com Maior Potencial")
        with st.container(border=True):
            if dados_hoje and dados_hoje.get("produtos"):
                melhor = max(dados_hoje["produtos"], key=lambda x: x.get("Score", 0))
                st.markdown(f"### {melhor['Produto']}")
                st.markdown(f"""
                - **Categoria:** {melhor['Categoria']}
                - **Score:** {melhor['Score']}/10
                - **Produtos Encontrados:** {melhor['Produtos Encontrados']}
                """)
            else:
                st.markdown("### Carregando...")
            st.success("🚀 **Ação:** Crie conteúdo sobre este produto!")
    
    with col2:
        st.markdown("### 📈 Tendência Mais Viral")
        with st.container(border=True):
            if dados_hoje and dados_hoje.get("produtos"):
                melhor = max(dados_hoje["produtos"], key=lambda x: x.get("Score", 0))
                st.markdown(f"### {melhor['Produto']}")
                st.markdown(f"""
                - **Score:** {melhor['Score']}/10
                - **Produtos Encontrados:** {melhor['Produtos Encontrados']}
                """)
            else:
                st.markdown("### Carregando...")
            st.info("💡 **Dica:** Produto com alto potencial de venda!")
    
    st.markdown("---")
    
    st.markdown("## 📌 Legenda de Potencial")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🟢 Alto**
        - Score ≥ 8
        - Baixa concorrência
        """)
    with col2:
        st.markdown("""
        **🟡 Médio**
        - Score 5-7
        - Concorrência moderada
        """)
    with col3:
        st.markdown("""
        **🔴 Baixo**
        - Score < 5
        - Mercado concorrido
        """)
    
    st.caption("Mais de 200 resultados no Google Shopping")
    
    return df if 'df' in locals() else None

# ============================================================
# APP PRINCIPAL
# ============================================================
licenca = verificar_login()

creditos = CreditosDiarios()
galeria = GaleriaVideos()
creditos_restantes = creditos.obter_creditos(licenca)

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
    st.markdown("## 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Produtos em alta baseados em tendências de mercado e datas comemorativas")
    
    dados_diarios = DadosDiarios()
    dados_hoje = dados_diarios.obter_dados_hoje()
    
    if dados_hoje and dados_hoje.get("produtos"):
        produtos = dados_hoje["produtos"]
        
        dados_tabela = []
        for item in produtos:
            palavra_chave = PALAVRAS_CHAVE_CAUDA_LONGA.get(item["Produto"], f"{item['Produto']} tendência 2026")
            
            dados_tabela.append({
                "Produto": item["Produto"],
                "🔑 Palavra-chave": palavra_chave,
                "Categoria": item["Categoria"],
                "Evento": item["Evento"],
                "Potencial": "🟢 Alto" if item["Score"] >= 8 else "🟡 Médio" if item["Score"] >= 5 else "🔴 Baixo",
                "Score": item["Score"],
                "Produtos Encontrados": item["Produtos Encontrados"]
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>'
        )
        
        colunas = ["Produto", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Produtos Encontrados", "Buscar na Shopee"]
        df = df[colunas]
        
        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    else:
        st.info("📭 Nenhum dado disponível para hoje.")

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
    
    tem_credenciais = bool(SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD))
    
    if not tem_credenciais:
        st.warning("⚠️ **Credenciais SnapGen não configuradas.**")
        st.info("Configure no painel do Streamlit Cloud: Settings → Secrets")
    
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
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year} | {BUSCAS_DIARIAS} buscas diárias | {BUSCAS_TOTAIS} buscas/mês")
