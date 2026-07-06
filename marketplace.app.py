import streamlit as st
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
# IMPORTAR MÓDULOS
# ============================================================
from modules.auth import verificar_login
from modules.views import (
    render_painel_apoiadores,
    render_painel_licencas,
    render_status_usuario
)
from modules.models import LICENCA_TRIAL, ADMIN_LICENCA

# ============================================================
# VERIFICAR LOGIN
# ============================================================
licenca = verificar_login()

# ============================================================
# TITULO DO APP
# ============================================================
st.title("📊 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

# ============================================================
# STATUS DO USUÁRIO
# ============================================================
render_status_usuario()

st.markdown("---")

# ============================================================
# DASHBOARD PRINCIPAL (AQUI ENTRA SEU DASHBOARD EXISTENTE)
# ============================================================
st.markdown("## 📊 Visão Geral do Mês")
st.markdown("""
**❄️ Inverno no auge!** Casacos e blusas de lã são os mais procurados. 
Aproveite as férias para conteúdo de viagens e looks de inverno.
""")

# ... SEU DASHBOARD EXISTENTE AQUI ...

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA",
    "👑 Apoiadores",
    "🔑 Licenças"
])

with tab1:
    # SEU DASHBOARD EXISTENTE
    pass

with tab2:
    st.markdown("## 📌 Sugestões de Produtos")
    # SEU CÓDIGO EXISTENTE
    pass

with tab3:
    st.markdown("## 📅 Calendário de Conteúdo")
    # SEU CÓDIGO EXISTENTE
    pass

with tab4:
    st.markdown("## 🎬 Criar Vídeo IA")
    # SEU CÓDIGO EXISTENTE
    pass

with tab5:
    render_painel_apoiadores()

with tab6:
    render_painel_licencas()

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v4.0 | {datetime.now().year}")
