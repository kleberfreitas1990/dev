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

    def render_interface_admin(self):
        """Interface administrativa simplificada para gestão de licenças"""
        st.markdown("### 📋 Licenças Ativas")
        
        licencas = self.dados.get("licencas", {})
        if not licencas:
            st.info("📭 Nenhuma licença encontrada.")
            return

        dados_tabela = []
        for codigo, info in licencas.items():
            dados_tabela.append({
                "Código": f"{codigo[:4]}...{codigo[-4:]}" if len(codigo) > 10 else codigo,
                "Usuário": info.get("usuario", "N/A"),
                "Plano": info.get("plano", "N/A"),
                "Status": info.get("status", "N/A"),
                "Tipo": info.get("tipo", "N/A")
            })
        
        st.table(dados_tabela)
        
        with st.expander("➕ Gerar Nova Licença"):
            nome = st.text_input("Nome do Usuário")
            email = st.text_input("E-mail")
            plano = st.selectbox("Plano", ["Básico", "Premium", "Apoiador"])
            is_apo = st.checkbox("É Apoiador?")
            
            if st.button("Gerar Licença"):
                if nome and email:
                    novo_codigo = self.gerar_licenca(nome, email, plano, is_apo)
                    st.success(f"✅ Licença gerada: `{novo_codigo}`")
                    st.info("Copie e envie para o usuário.")
                else:
                    st.error("Preencha nome e e-mail.")

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

# ============================================================
# FUNÇÃO PARA LISTAR APOIADORES POR LICENÇAS
# ============================================================
def listar_apoiadores_por_licencas():
    """
    Retorna lista de apoiadores baseada nas licenças
    """
    sistema = SistemaLicencas()
    apoiadores = []
    
    for codigo, dados in sistema.dados["licencas"].items():
        if dados.get("is_apoiador", False) and dados.get("status") == "ativo":
            apoiadores.append({
                "codigo": codigo,
                "nome": dados.get("usuario", "Apoiador"),
                "email": dados.get("email", ""),
                "plano": dados.get("plano", "Apoiador"),
                "is_apoiador": True
            })
    
    return apoiadores

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'SistemaLicencas',
    'verificar_login',
    'LICENCA_TRIAL',
    'ADMIN_LICENCA',
    'listar_apoiadores_por_licencas'
]
