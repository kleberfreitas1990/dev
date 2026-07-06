import streamlit as st
import time
from modules.models import SistemaLicencas, ADMIN_LICENCA, LICENCA_TRIAL

def verificar_login():
    """Função de login com validação de licença"""
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos")
        st.markdown("### 🔐 Acesso ao Sistema")
        
        # Mostra planos disponíveis
        with st.expander("📋 Planos Disponíveis"):
            sistema = SistemaLicencas()
            planos = sistema.dados["config"]["planos"]
            for key, plano in planos.items():
                st.markdown(f"""
                **{plano['nome']}**
                - 💰 R$ {plano['preco']:.2f}
                - 📅 {plano['dias']} dias
                - 👑 Royalties: {"✅" if plano['royalties'] else "❌"}
                - 🔄 Repasse: {"✅" if plano['repasse'] else "❌"}
                """)
        
        licenca = st.text_input("Digite sua Licença de Acesso:", type="password")
        
        if st.button("🔓 Entrar", type="primary", use_container_width=True):
            sistema = SistemaLicencas()
            resultado = sistema.validar_licenca(licenca)
            
            if resultado["valido"]:
                st.session_state.logado = True
                st.session_state.licenca_usuario = licenca
                st.session_state.usuario_nome = resultado.get("usuario", "")
                st.session_state.plano = resultado.get("plano", "")
                st.session_state.royalties = resultado.get("royalties", False)
                st.session_state.repasse = resultado.get("repasse", False)
                st.session_state.is_apoiador = resultado.get("is_apoiador", False)
                st.session_state.is_admin = resultado.get("is_admin", False)
                
                st.success(f"✅ Bem-vindo, {resultado.get('usuario', 'Usuário')}!")
                st.caption(f"📋 Plano: {resultado.get('plano', '')} | Expira: {resultado.get('data_expiracao', '')}")
                if resultado.get("is_admin", False):
                    st.success("🔑 **ACESSO DE ADMINISTRADOR** - Você pode gerenciar licenças!")
                if resultado.get("is_apoiador", False):
                    st.success("👑 **VOCÊ É UM APOIADOR!**")
                
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {resultado.get('motivo', 'Licença inválida')}")
        
        st.markdown("---")
        st.caption("🔒 Sistema protegido por licença. Contate o suporte para obter acesso.")
        st.stop()
    
    return st.session_state.get('licenca_usuario', LICENCA_TRIAL)
