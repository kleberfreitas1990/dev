import streamlit as st
import pandas as pd
from modules.models import SistemaLicencas, carregar_apoiadores, ADMIN_LICENCA

# ============================================================
# PAINEL DE APOIADORES
# ============================================================
def render_painel_apoiadores():
    """Renderiza o painel de apoiadores"""
    
    st.markdown("## 👑 Nossos Apoiadores")
    st.caption("Quem acreditou no projeto desde o início")
    
    apoiadores = carregar_apoiadores()
    
    if apoiadores:
        apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
        
        cols = st.columns(min(len(apoiadores_ordenados), 3))
        
        for i, apoiador in enumerate(apoiadores_ordenados):
            with cols[i % 3]:
                with st.container(border=True):
                    cor = apoiador.get("cor", "#FFD700")
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px 0;">
                        <span style="font-size: 48px;">{apoiador.get('coroinha', '👑')}</span>
                        <h3 style="color: {cor}; margin: 5px 0;">{apoiador.get('nome')}</h3>
                        <p style="color: #888; font-size: 14px;">#{apoiador.get('ordem', 999)} • Apoiador</p>
                        <p style="color: #666; font-size: 12px;">{apoiador.get('plano', 'Fundador')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"**📅 Entrada:** {apoiador.get('data_entrada', '2026-07-01')}")
                    
                    ordem = apoiador.get("ordem", 999)
                    depois = sum(1 for k, d in apoiadores.items() if d.get("ordem", 999) > ordem)
                    
                    if depois > 0 and apoiador.get("repasse_ativo", True):
                        st.success(f"✅ Recebendo repasse de {depois} apoiador(es)")
                        st.caption(f"💰 R${depois * 5.00:.2f} estimado/mês")
                    else:
                        st.info("⏳ Aguardando novos apoiadores")
                    
                    if apoiador.get("ordem") == 1:
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #FFD700, #FFA500); 
                                    color: white; text-align: center; padding: 4px; 
                                    border-radius: 4px; font-weight: bold; font-size: 12px;">
                            🏆 PRIMEIRA(O) APOIADORA
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("📭 Nenhum apoiador cadastrado ainda. Seja o primeiro!")
    
    st.markdown("---")


# ============================================================
# PAINEL DE LICENÇAS (APENAS ADMIN)
# ============================================================
def render_painel_licencas():
    """Renderiza o painel de administração de licenças (apenas admin)"""
    
    # Verifica se o usuário é admin
    is_admin = st.session_state.get("is_admin", False)
    licenca_atual = st.session_state.get("licenca_usuario", "")
    
    if not is_admin and licenca_atual != ADMIN_LICENCA:
        st.warning("🔒 **Acesso restrito a administradores.**")
        st.info("Entre em contato com o suporte para gerenciar licenças.")
        return
    
    st.markdown("## 🔑 Gerenciamento de Licenças")
    st.caption("Crie, gerencie e monitore licenças do sistema")
    
    sistema = SistemaLicencas()
    stats = sistema.obter_estatisticas()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total", stats["total"])
    with col2:
        st.metric("✅ Ativas", stats["ativas"])
    with col3:
        st.metric("⏰ Expiradas", stats["expiradas"])
    with col4:
        st.metric("💰 Receita Mensal", f"R$ {stats['receita_mensal']:.2f}")
    
    st.markdown("---")
    
    # ===== CRIAR NOVA LICENÇA =====
    with st.expander("🆕 Criar Nova Licença", expanded=False):
        st.markdown("### Criar Licença")
        
        col1, col2 = st.columns(2)
        
        with col1:
            novo_usuario = st.text_input("Nome do Usuário", placeholder="Ex: João Silva")
            novo_email = st.text_input("E-mail", placeholder="joao@email.com")
            novo_cpf = st.text_input("CPF (opcional)", placeholder="000.000.000-00")
        
        with col2:
            planos = sistema.dados["config"]["planos"]
            plano_opcoes = {
                k: f"{v['nome']} - R$ {v['preco']:.2f} ({v['dias']} dias)" 
                for k, v in planos.items()
            }
            plano_selecionado = st.selectbox(
                "Plano",
                options=list(plano_opcoes.keys()),
                format_func=lambda x: plano_opcoes[x]
            )
        
        # Checkbox para tornar apoiador
        plano_dados = planos.get(plano_selecionado, {})
        is_apoiador = st.checkbox(
            "👑 Tornar este usuário um APOIADOR (royalties)",
            value=plano_dados.get("royalties", False),
            help="Apoiadores recebem royalties e aparecem no painel de apoiadores"
        )
        
        if st.button("🚀 Gerar Licença", use_container_width=True):
            if not novo_usuario or not novo_email:
                st.error("❌ Preencha nome e e-mail")
            else:
                # Verifica se já existe licença para este email
                licencas = sistema.listar_licencas(apenas_ativas=True)
                for l in licencas:
                    if l["email"] == novo_email:
                        st.error(f"❌ Já existe uma licença ativa para {novo_email}")
                        break
                else:
                    resultado = sistema.gerar_licenca(
                        novo_usuario, 
                        novo_email, 
                        plano_selecionado, 
                        novo_cpf,
                        is_apoiador,
                        st.session_state.get("usuario_nome", "Admin")
                    )
                    
                    if "erro" in resultado:
                        st.error(f"❌ {resultado['erro']}")
                    else:
                        st.success("✅ Licença gerada com sucesso!")
                        
                        st.markdown("#### 📋 Dados da Licença")
                        st.code(f"Código: {resultado['codigo']}", language="text")
                        st.code(f"Plano: {resultado['plano']}", language="text")
                        st.code(f"Validade: {resultado['validade']} dias", language="text")
                        st.code(f"Expira em: {resultado['data_expiracao']}", language="text")
                        
                        if resultado.get('royalties') or is_apoiador:
                            st.success("👑 **ESTA LICENÇA TEM DIREITO A ROYALTIES!**")
                            st.info("O usuário aparecerá no painel de apoiadores.")
                        
                        st.warning("⚠️ Guarde este código! Ele não será exibido novamente.")
                        st.code(f"📋 Código para copiar: {resultado['codigo']}", language="text")
                        
                        if st.button("🔄 Atualizar Apoiadores"):
                            st.rerun()
    
    st.markdown("---")
    
    # ===== LISTA DE LICENÇAS =====
    st.markdown("### 📋 Licenças Ativas")
    
    licencas = sistema.listar_licencas(apenas_ativas=False)
    
    if licencas:
        df_licencas = pd.DataFrame(licencas)
        
        df_licencas["status"] = df_licencas["status"].apply(
            lambda x: "🟢 Ativo" if x == "ativo" else "🔴 Expirado" if x == "expirado" else "⚫ Revogado"
        )
        df_licencas["royalties"] = df_licencas["royalties"].apply(
            lambda x: "👑" if x else "❌"
        )
        df_licencas["is_admin"] = df_licencas["is_admin"].apply(
            lambda x: "🔑" if x else "❌"
        )
        
        st.dataframe(
            df_licencas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "codigo": "Código",
                "usuario": "Usuário",
                "email": "E-mail",
                "plano": "Plano",
                "status": "Status",
                "criacao": "Criação",
                "expiracao": "Expiração",
                "acessos": "Acessos",
                "royalties": "Royalties",
                "is_admin": "Admin"
            }
        )
        
        # ===== AÇÕES POR LICENÇA =====
        st.markdown("### 🔧 Ações por Licença")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            opcoes = [l["codigo"] for l in licencas if l["status"] == "🟢 Ativo" and l["codigo"] != ADMIN_LICENCA]
            if opcoes:
                codigo_acao = st.selectbox(
                    "Selecione uma licença",
                    options=opcoes
                )
            else:
                st.info("Nenhuma licença ativa disponível para ações")
                codigo_acao = None
        
        with col2:
            if codigo_acao:
                acao = st.selectbox(
                    "Ação",
                    options=["Renovar por 30 dias", "Renovar por 90 dias", "Revogar"]
                )
            else:
                acao = "Renovar por 30 dias"
        
        with col3:
            if codigo_acao and st.button("Executar Ação", use_container_width=True):
                if "Renovar" in acao:
                    dias = 30 if "30" in acao else 90
                    resultado = sistema.renovar_licenca(codigo_acao, dias)
                    if "erro" in resultado:
                        st.error(f"❌ {resultado['erro']}")
                    else:
                        st.success(f"✅ Licença renovada! Nova expiração: {resultado['nova_expiracao']}")
                        st.rerun()
                elif "Revogar" in acao:
                    if st.button("Confirmar Revogação", use_container_width=True):
                        resultado = sistema.revogar_licenca(codigo_acao)
                        if "erro" in resultado:
                            st.error(f"❌ {resultado['erro']}")
                        else:
                            st.success(f"✅ Licença {codigo_acao} revogada!")
                            st.rerun()
    else:
        st.info("📭 Nenhuma licença cadastrada ainda.")
    
    st.markdown("---")
    
    # ===== ESTATÍSTICAS AVANÇADAS =====
    with st.expander("📊 Estatísticas Avançadas"):
        st.markdown("### 📊 Análise de Licenças")
        
        planos = {}
        for l in licencas:
            plano = l.get("plano", "Desconhecido")
            planos[plano] = planos.get(plano, 0) + 1
        
        if planos:
            df_planos = pd.DataFrame({
                "Plano": list(planos.keys()),
                "Quantidade": list(planos.values())
            })
            st.bar_chart(df_planos.set_index("Plano"))
        
        # Receita total
        receita_total = sum(
            sistema.dados["config"]["planos"].get(l.get("tipo", ""), {}).get("preco", 0)
            for l in sistema.dados["licencas"].values()
            if l.get("status") == "ativo"
        )
        
        st.metric("💰 Receita Total (mensal)", f"R$ {receita_total:.2f}")


# ============================================================
# RENDERIZAR STATUS DO USUÁRIO
# ============================================================
def render_status_usuario():
    """Renderiza o status do usuário no dashboard"""
    
    st.markdown("### 👤 Seu Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📋 Plano",
            st.session_state.get("plano", "Trial")
        )
    
    with col2:
        st.metric(
            "👑 Apoiador",
            "✅" if st.session_state.get("is_apoiador", False) else "❌"
        )
    
    with col3:
        st.metric(
            "🔑 Admin",
            "✅" if st.session_state.get("is_admin", False) else "❌"
        )
    
    if st.session_state.get("is_admin", False):
        st.info("🔑 **Você tem acesso administrativo.** Use a aba 'Licenças' para gerenciar usuários.")
