import streamlit as st
import time
from modules.models import SistemaLicencas, LICENCA_TRIAL

def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        licenca = st.text_input("Digite sua Licença de Acesso:", type="password")
        
        if st.button("🔓 Entrar", type="primary", use_container_width=True):
            sistema = SistemaLicencas()
            resultado = sistema.validar_licenca(licenca)
            
            if resultado["valido"]:
                st.session_state.logado = True
                st.session_state.licenca_usuario = licenca
                st.session_state.usuario_nome = resultado.get("usuario", "")
                st.session_state.plano = resultado.get("plano", "")
                st.session_state.is_admin = resultado.get("is_admin", False)
                st.session_state.is_apoiador = resultado.get("is_apoiador", False)
                
                st.success(f"✅ Bem-vindo, {resultado.get('usuario', 'Usuário')}!")
                st.caption(f"📋 Plano: {resultado.get('plano', '')}")
                
                if resultado.get("is_admin", False):
                    st.success("🔑 **ACESSO DE ADMINISTRADOR**")
                
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {resultado.get('motivo', 'Licença inválida')}")
        
        st.markdown("---")
        st.caption("🔒 Sistema protegido por licença.")
        st.stop()
    
    return st.session_state.get('licenca_usuario', LICENCA_TRIAL)
