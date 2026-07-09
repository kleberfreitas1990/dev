import streamlit as st
import pandas as pd
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
        if codigo in self.dados["licencas"]:
            if codigo == ADMIN_LICENCA:
                return {"erro": "Não é possível revogar o administrador principal"}
            self.dados["licencas"][codigo]["status"] = "revogado"
            self.salvar()
            return {"sucesso": True}
        return {"erro": "Licença não encontrada"}

    def remover_licenca(self, codigo):
        if codigo in self.dados["licencas"]:
            if codigo == ADMIN_LICENCA:
                return {"erro": "Não é possível remover o administrador principal"}
            del self.dados["licencas"][codigo]
            self.salvar()
            return {"sucesso": True}
        return {"erro": "Licença não encontrada"}

    def renovar_licenca(self, codigo, novo_plano=None, novo_status="ativo"):
        if codigo in self.dados["licencas"]:
            self.dados["licencas"][codigo]["status"] = novo_status
            if novo_plano:
                self.dados["licencas"][codigo]["plano"] = novo_plano
            self.salvar()
            return {"sucesso": True}
        return {"erro": "Licença não encontrada"}

    def render_interface_admin(self):
        """Interface administrativa completa para gestão de licenças"""
        st.markdown("### 📋 Gestão de Licenças")
        
        licencas = self.dados.get("licencas", {})
        
        # --- TABELA DE LICENÇAS ---
        dados_tabela = []
        for codigo, info in licencas.items():
            dados_tabela.append({
                "Código": codigo,
                "Usuário": info.get("usuario", "N/A"),
                "Plano": info.get("plano", "N/A"),
                "Status": info.get("status", "N/A"),
                "Tipo": info.get("tipo", "N/A")
            })
        
        if dados_tabela:
            df = pd.DataFrame(dados_tabela)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nenhuma licença encontrada.")

        st.markdown("---")
        
        # --- AÇÕES EM LICENÇAS EXISTENTES ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔄 Renovar / Editar")
            codigos_lista = list(licencas.keys())
            if codigos_lista:
                cod_selecionado = st.selectbox("Selecione a licença para editar:", codigos_lista)
                info_atual = licencas[cod_selecionado]
                
                st.info(f"Editando: **{info_atual.get('usuario')}** ({info_atual.get('plano')})")
                
                novo_plano = st.selectbox("Novo Plano:", ["Básico", "Premium", "Apoiador", "Trial"], 
                                        index=["Básico", "Premium", "Apoiador", "Trial"].index(info_atual.get('plano', 'Básico')) if info_atual.get('plano') in ["Básico", "Premium", "Apoiador", "Trial"] else 0)
                
                novo_status = st.selectbox("Novo Status:", ["ativo", "revogado", "expirado"],
                                         index=["ativo", "revogado", "expirado"].index(info_atual.get('status', 'ativo')) if info_atual.get('status') in ["ativo", "revogado", "expirado"] else 0)
                
                if st.button("💾 Salvar Alterações", use_container_width=True):
                    res = self.renovar_licenca(cod_selecionado, novo_plano, novo_status)
                    if "sucesso" in res:
                        st.success("✅ Licença atualizada!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {res.get('erro')}")

        with col2:
            st.markdown("#### 🗑️ Remover Licença")
            if codigos_lista:
                cod_remover = st.selectbox("Selecione a licença para REMOVER:", codigos_lista, key="remove_select")
                st.warning(f"Cuidado: Isso apagará permanentemente a licença de **{licencas[cod_remover].get('usuario')}**.")
                
                if st.button("🗑️ REMOVER PERMANENTEMENTE", use_container_width=True, type="primary"):
                    if cod_remover == ADMIN_LICENCA:
                        st.error("❌ Não é possível remover o administrador!")
                    else:
                        res = self.remover_licenca(cod_remover)
                        if "sucesso" in res:
                            st.success("✅ Licença removida!")
                            st.rerun()
                        else:
                            st.error(f"❌ Erro: {res.get('erro')}")

        st.markdown("---")
        
        # --- GERAR NOVA LICENÇA ---
        with st.expander("➕ Gerar Nova Licença", expanded=False):
            st.markdown("### Criar Novo Acesso")
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome do Usuário", key="new_nome")
                email = st.text_input("E-mail", key="new_email")
            with c2:
                plano = st.selectbox("Plano", ["Básico", "Premium", "Apoiador"], key="new_plano")
                is_apo = st.checkbox("É Apoiador?", key="new_is_apo")
            
            if st.button("🚀 Gerar e Ativar Licença", use_container_width=True):
                if nome and email:
                    novo_codigo = self.gerar_licenca(nome, email, plano, is_apo)
                    st.success(f"✅ Licença gerada: `{novo_codigo}`")
                    st.info("Copie o código acima e envie para o usuário.")
                else:
                    st.error("❌ Preencha nome e e-mail para gerar.")

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
