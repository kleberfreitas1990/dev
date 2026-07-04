import streamlit as st
from datetime import datetime

def configurar_pagina():
    st.set_page_config(
        page_title="Minerador de Produtos - Afiliados",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def sidebar_menu(creditos_restantes, creditos_diarios, status_api, licenca):
    with st.sidebar:
        st.markdown("### ⚙️ Menu")
        
        st.markdown(f"**🔌 Status API:** {status_api}")
        st.markdown("---")
        
        st.markdown("### 🎫 Créditos")
        st.metric("Disponíveis hoje", f"{creditos_restantes} / {creditos_diarios}")
        
        if creditos_restantes == 0:
            st.warning("⚠️ Créditos esgotados! Volte amanhã.")
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.rerun()
        
        st.caption(f"👤 Licença: {licenca[:10]}...")
