import streamlit as st
import warnings
from datetime import datetime

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
from modules.serper import buscar_produtos_serper, buscar_total_resultados_serper

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
# DASHBOARD PRINCIPAL
# ============================================================
st.markdown("## 📊 Visão Geral do Mês")
st.markdown("""
**❄️ Inverno no auge!** Casacos e blusas de lã são os mais procurados. 
Aproveite as férias para conteúdo de viagens e looks de inverno.
""")

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
    st.markdown("### 📊 Dashboard Principal")
    
    # Exemplo de uso da Serper
    termo_exemplo = "smartwatch"
    produtos = buscar_produtos_serper(termo_exemplo, 5)
    
    if produtos:
        st.markdown(f"**🔍 Produtos encontrados para '{termo_exemplo}':**")
        for p in produtos[:3]:
            st.markdown(f"- {p.get('nome', '')} - {p.get('preco', '')}")
    else:
        st.info("Nenhum produto encontrado. Verifique sua chave Serper.dev")

with tab2:
    st.markdown("## 📌 Sugestões de Produtos")
    st.info("Sugestões de produtos aqui")

with tab3:
    st.markdown("## 📅 Calendário de Conteúdo")
    st.info("Calendário aqui")

with tab4:
    st.markdown("## 🎬 Criar Vídeo IA")
    st.info("Gerador de vídeos aqui")

with tab5:
    render_painel_apoiadores()

with tab6:
    render_painel_licencas()

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v4.0 | {datetime.now().year}")
