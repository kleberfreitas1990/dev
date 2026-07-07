import streamlit as st
import time
import json
import os
from datetime import datetime

# ============================================================
# CONSTANTES
# ============================================================
LICENCA_TRIAL = "TESTE-AFILIADO-2026"
ADMIN_LICENCA = "ADMIN-2026-KLEBER"
ARQUIVO_LICENCAS = "licencas.json"

# ============================================================
# CLASSE SISTEMA DE LICENÇAS
# ============================================================
class SistemaLicencas:
    def __init__(self):
        self.arquivo = ARQUIVO_LICENCAS
        self.dados = self.carregar()
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._criar_estrutura_padrao()
        return self._criar_estrutura_padrao()
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, ensure_ascii=False, indent=2)
    
    def _criar_estrutura_padrao(self):
        return {
            "licencas": {
                LICENCA_TRIAL: {
                    "tipo": "trial",
                    "status": "ativo",
                    "usuario": "Usuário Trial",
                    "plano": "Trial 7 dias",
                    "is_admin": False,
                    "is_apoiador": False
                },
                ADMIN_LICENCA: {
                    "tipo": "admin",
                    "status": "ativo",
                    "usuario": "Administrador",
                    "plano": "Administrador",
                    "is_admin": True,
                    "is_apoiador": False
                }
            }
        }
    
    def validar_licenca(self, codigo):
        licenca = self.dados["licencas"].get(codigo)
        if not licenca:
            return {"valido": False, "motivo": "Licença não encontrada"}
        if licenca.get("status") != "ativo":
            return {"valido": False, "motivo": f"Licença {licenca.get('status')}"}
        
        return {
            "valido": True,
            "usuario": licenca.get("usuario"),
            "plano": licenca.get("plano"),
            "is_admin": licenca.get("is_admin", False),
            "is_apoiador": licenca.get("is_apoiador", False)
        }
    
    def is_admin(self, codigo):
        licenca = self.dados["licencas"].get(codigo)
        return licenca.get("is_admin", False) if licenca else False
    
    def gerar_licenca(self, usuario, email, plano, is_apoiador=False):
        import uuid
        codigo = f"LIC-{uuid.uuid4().hex[:8].upper()}"
        
        self.dados["licencas"][codigo] = {
            "tipo": "apoiador" if is_apoiador else "basico",
            "status": "ativo",
            "usuario": usuario,
            "email": email,
            "plano": plano,
            "is_admin": False,
            "is_apoiador": is_apoiador,
            "data_criacao": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.salvar()
        return codigo
    
    def revogar_licenca(self, codigo):
        licenca = self.dados["licencas"].get(codigo)
        if not licenca:
            return {"erro": "Licença não encontrada"}
        if codigo == ADMIN_LICENCA:
            return {"erro": "Não é possível revogar a licença de administrador"}
        licenca["status"] = "revogado"
        self.salvar()
        return {"sucesso": True, "codigo": codigo}

# ============================================================
# FUNÇÃO DE LOGIN
# ============================================================
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
