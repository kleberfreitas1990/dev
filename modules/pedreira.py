
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# ============================================================
# CONFIGURAÇÃO E DADOS
# ============================================================
FILE_PEDIDOS = "pedidos_pedreira.json"

def carregar_pedidos():
    if os.path.exists(FILE_PEDIDOS):
        with open(FILE_PEDIDOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_pedidos(pedidos):
    with open(FILE_PEDIDOS, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, indent=4, ensure_ascii=False)

# ============================================================
# INTERFACE DO SOLICITANTE
# ============================================================
def tela_solicitante():
    st.subheader("📋 Nova Solicitação")
    
    with st.form("form_solicitacao"):
        empresa = st.selectbox("Qual Pedreira?", ["Pedreira A", "Pedreira B", "Pedreira C", "Pedreira Central"])
        produto = st.text_input("Insira o Produto")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        
        submitted = st.form_submit_button("GRAVAR")
        
        if submitted:
            if produto:
                usuario_nome = st.session_state.get("usuario_nome", "Solicitante")
                novo_pedido = {
                    "id": len(carregar_pedidos()) + 1,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "solicitante": usuario_nome,
                    "empresa": empresa,
                    "produto": produto,
                    "quantidade": quantidade,
                    "status": "Pendente",
                    "setor": "Atendimento",
                    "estoque": "Verificando"
                }
                pedidos = carregar_pedidos()
                pedidos.append(novo_pedido)
                salvar_pedidos(pedidos)
                st.success("✅ Pedido gravado com sucesso!")
            else:
                st.error("❌ Por favor, insira o nome do produto.")

    st.divider()
    st.subheader("📊 Acompanhar Status")
    pedidos = carregar_pedidos()
    if pedidos:
        df = pd.DataFrame(pedidos)
        st.table(df[["id", "data", "empresa", "produto", "quantidade", "status"]])
    else:
        st.info("Nenhum pedido realizado ainda.")

# ============================================================
# INTERFACE DO ATENDENTE (SENHA)
# ============================================================
def tela_atendente():
    st.subheader("🔑 Área do Atendente")
    
    # Se for admin, já libera. Se não, pede a senha do fluxo.
    is_admin = st.session_state.get("is_admin", False)
    acesso_liberado = False
    
    if is_admin:
        st.success("Acesso de Administrador Detectado")
        acesso_liberado = True
    else:
        senha = st.text_input("Insira a Senha", type="password")
        if senha == "1234":
            st.success("Acesso Liberado")
            acesso_liberado = True
        elif senha:
            st.error("Senha Incorreta")

    if acesso_liberado:
        
        pedidos = carregar_pedidos()
        if not pedidos:
            st.info("Não há pedidos para processar.")
            return

        st.write("### Pedidos Pendentes")
        for i, p in enumerate(pedidos):
            if p["status"] == "Pendente":
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{p['produto']}** ({p['quantidade']}) - {p['empresa']}")
                with col2:
                    if st.button("Enviar p/ Almoxarifado", key=f"alm_{i}"):
                        pedidos[i]["status"] = "Em Análise"
                        pedidos[i]["setor"] = "Almoxarifado"
                        salvar_pedidos(pedidos)
                        st.rerun()
                with col3:
                    if st.button("Enviar p/ Compras", key=f"comp_{i}"):
                        pedidos[i]["status"] = "Aguardando Compra"
                        pedidos[i]["setor"] = "Compras"
                        salvar_pedidos(pedidos)
                        st.rerun()
    elif senha:
        st.error("Senha Incorreta")

# ============================================================
# PAINÉIS DE STATUS (ALMOXARIFADO / COMPRAS)
# ============================================================
def tela_setores():
    col1, col2 = st.columns(2)
    
    pedidos = carregar_pedidos()
    
    with col1:
        st.subheader("📦 Setor Almoxarifado")
        alm_pedidos = [p for p in pedidos if p["setor"] == "Almoxarifado"]
        if alm_pedidos:
            for p in alm_pedidos:
                with st.expander(f"Pedido #{p['id']} - {p['produto']}"):
                    st.write(f"Qtd: {p['quantidade']}")
                    tem_estoque = st.radio("Tem Estoque?", ["Sim", "Não"], key=f"est_{p['id']}")
                    if st.button("Confirmar", key=f"conf_alm_{p['id']}"):
                        p["estoque"] = tem_estoque
                        p["status"] = "Finalizado (Estoque)" if tem_estoque == "Sim" else "Falta no Estoque"
                        salvar_pedidos(pedidos)
                        st.rerun()
        else:
            st.write("Nenhum pedido no Almoxarifado.")

    with col2:
        st.subheader("💰 Setor Compras")
        comp_pedidos = [p for p in pedidos if p["setor"] == "Compras"]
        if comp_pedidos:
            for p in comp_pedidos:
                with st.expander(f"Pedido #{p['id']} - {p['produto']}"):
                    st.write(f"Qtd: {p['quantidade']}")
                    if st.button("Marcar como Comprado", key=f"buy_{p['id']}"):
                        p["status"] = "Comprado"
                        salvar_pedidos(pedidos)
                        st.rerun()
        else:
            st.write("Nenhum pedido em Compras.")

# ============================================================
# RENDERIZAÇÃO PRINCIPAL
# ============================================================
def render_pedreira():
    st.title("🏗️ Fluxo de Pedidos - Pedreira")
    
    menu = ["Solicitante", "Atendente", "Setores (Almoxarifado/Compras)"]
    choice = st.sidebar.selectbox("Perfil de Acesso", menu)
    
    if choice == "Solicitante":
        tela_solicitante()
    elif choice == "Atendente":
        tela_atendente()
    else:
        tela_setores()
