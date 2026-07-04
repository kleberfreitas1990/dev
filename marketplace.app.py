import streamlit as st
import warnings

# ============================================================
# IMPORTAR MÓDULOS
# ============================================================
from modules.layout import configurar_pagina, sidebar_menu
from modules.auth import verificar_login
from modules.dashboard import render_dashboard
from modules.products import render_products
from modules.calendar import render_calendar
from modules.video_generator import render_video_generator

# ============================================================
# SISTEMAS COMPARTILHADOS
# ============================================================
from modules.video_generator import GaleriaVideos, CreditosDiarios

# ============================================================
# SUPRIMIR WARNINGS
# ============================================================
warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
configurar_pagina()

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
creditos_restantes = creditos.obter_creditos(licenca)
CREDITOS_DIARIOS = 10

# ============================================================
# STATUS DA API
# ============================================================
status_api = "✅ Conectado" if (SNAPGEN_API_KEY or (SNAPGEN_EMAIL and SNAPGEN_PASSWORD)) else "❌ Desconectado"

# ============================================================
# MENU LATERAL
# ============================================================
sidebar_menu(creditos_restantes, CREDITOS_DIARIOS, status_api, licenca)

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
    render_video_generator(
        creditos=creditos,
        licenca=licenca,
        creditos_restantes=creditos_restantes,
        creditos_diarios=CREDITOS_DIARIOS,
        galeria=galeria,
        snapgen_api_key=SNAPGEN_API_KEY,
        snapgen_email=SNAPGEN_EMAIL,
        snapgen_password=SNAPGEN_PASSWORD
    )

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v3.0 | {datetime.now().year} | Gerador de Vídeo com SnapGen AI")
