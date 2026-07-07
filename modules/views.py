import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# Importa do auth.py (SistemaLicencas está aqui)
from modules.auth import SistemaLicencas
from modules.models import (
    PALAVRAS_CHAVE_CAUDA_LONGA,
    obter_palavra_chave,
    gerar_top10_produtos,
    gerar_sugestoes_diarias,
    BUSCAS_DIARIAS,
    carregar_apoiadores,
    adicionar_apoiador,
    remover_apoiador
)

# Tenta importar serper, se falhar usa fallback
try:
    from modules.serper import buscar_produtos_serper
    SERPER_DISPONIVEL = True
except ImportError:
    SERPER_DISPONIVEL = False
    def buscar_produtos_serper(termo, limite=5):
        return []

# ============================================================
# STATUS DO USUÁRIO (REMOVIDO)
# ============================================================
def render_status_usuario():
    """Renderiza o status do usuário - REMOVIDO"""
    pass

# ============================================================
# APOIADORES EM CARDS PEQUENOS (COM COROA CENTRALIZADA)
# ============================================================
def render_apoiadores_compactos():
    """Renderiza os apoiadores em cards pequenos com coroa centralizada"""
    
    apoiadores = carregar_apoiadores()
    
    if not apoiadores:
        return
    
    # Título da seção
    st.markdown("### 👑 Apoiadores do Projeto")
    st.caption("Pessoas que acreditam e apoiam este projeto")
    
    # Ordena por ordem de entrada
    apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
    
    # Cores para os cards
    cores = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE",
        "#FD79A8", "#00B894", "#E17055", "#6C5CE7"
    ]
    
    # Exibe em cards pequenos (6 por linha)
    cols = st.columns(6)
    
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 6]:
            cor = cores[i % len(cores)]
            nome = apoiador.get("nome", "Apoiador")
            ordem = apoiador.get("ordem", 999)
            coroinha = apoiador.get("coroinha", "👑")
            
            with st.container(border=True):
                # Coroa centralizada no topo
                st.markdown(f"""
                <div style="text-align: center; font-size: 28px; margin: -8px 0 2px 0;">
                    {coroinha}
                </div>
                """, unsafe_allow_html=True)
                
                # Nome centralizado
                st.markdown(f"""
                <div style="text-align: center; font-weight: bold; font-size: 13px; margin: 0;">
                    {nome}
                </div>
                """, unsafe_allow_html=True)
                
                # Número da ordem
                st.markdown(f"""
                <div style="text-align: center; font-size: 10px; color: #888; margin: 0;">
                    #{ordem}
                </div>
                """, unsafe_allow_html=True)
                
                # Barra colorida abaixo
                st.markdown(f"""
                <div style="
                    background: {cor};
                    height: 3px;
                    border-radius: 2px;
                    margin: 4px 0 2px 0;
                ">
                </div>
                """, unsafe_allow_html=True)
                
                # Repasse (se houver)
                depois = sum(1 for k, d in apoiadores.items() if d.get("ordem", 999) > ordem)
                
                if depois > 0 and apoiador.get("repasse_ativo", True):
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 10px; color: #4CAF50; margin: 0;">
                        ⬇️ R${depois * 5.00:.0f}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 10px; color: #888; margin: 0;">
                        ⏳
                    </div>
                    """, unsafe_allow_html=True)

# ============================================================
# INSIGHTS INTERATIVOS
# ============================================================
def render_insights_interativos(produtos):
    """
    Renderiza insights interativos que levam para a tab de conteúdo
    """
    if not produtos:
        return
    
    st.markdown("## 💡 Insights Estratégicos - Top 3")
    
    top3 = sorted(produtos, key=lambda x: x.get("Score", 0), reverse=True)[:3]
    cols = st.columns(3)
    
    for i, item in enumerate(top3):
        with cols[i]:
            produto_nome = item.get("Produto", "")
            
            with st.container(border=True):
                # Emoji do ranking
                emojis = ["🥇", "🥈", "🥉"]
                st.markdown(f"### {emojis[i]} {produto_nome}")
                
                # Métricas resumidas
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Score", f"{item.get('Score', 0)}/10")
                    st.metric("Crescimento", item.get('Crescimento', '+0%'))
                with col2:
                    st.metric("Views TikTok", item.get('Views TikTok', '0M'))
                    st.metric("Pins", item.get('Pins', '0'))
                
                # Palavra-chave
                produto_lower = produto_nome.lower()
                dados_palavra = obter_palavra_chave(produto_lower)
                palavra_chave = dados_palavra.get("palavra", f"{produto_lower} tendência 2026")
                st.info(f"🔑 **Palavra-chave:** {palavra_chave}")
                
                # Hashtags resumidas
                hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:3]
                tags_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 2px 8px; border-radius: 12px; margin: 2px; font-size: 11px;">{h}</span>' for h in hashtags])
                st.markdown(tags_html, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Botão "Criar Conteúdo" - vai para a tab de conteúdo
                if st.button(f"🎬 Criar Conteúdo para {produto_nome}", key=f"insight_{produto_nome}", use_container_width=True):
                    # Salva no session_state para a tab de conteúdo
                    st.session_state.produto_conteudo = produto_nome
                    st.success(f"✅ Redirecionando para criar conteúdo sobre {produto_nome}...")
                    st.rerun()

# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
def render_dashboard():
    """Renderiza o dashboard principal"""
    
    st.title("📊 Minerador de Produtos")
    st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    # Status compacto
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    with col_status1:
        serper_key = st.secrets.get("SERPER_API_KEY", "")
        st.markdown("🔌 " + ("✅" if serper_key else "❌"))
    with col_status2:
        st.markdown("🎫 10/10")
    with col_status3:
        st.markdown(f"👤 {st.session_state.get('licenca_usuario', '')[:8]}...")
    with col_status4:
        if st.button("🚪 Sair", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("## 📊 Visão Geral do Mês")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown("""
            **❄️ Inverno no auge!** Casacos e blusas de lã são os mais procurados. 
            Aproveite as férias para conteúdo de viagens e looks de inverno.
            """)
            
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("🔥 Produto em Alta", "casaco", delta="Moda")
            with m2:
                st.metric("📈 Crescimento Médio", "19.1%", delta="+2.3%")
            with m3:
                st.metric("🎯 Foco Principal", "Férias Escolares", delta="Alta demanda")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 🎯 Melhor Oportunidade")
            
            st.markdown("**Potencial de Mercado**")
            potencial = 85
            cor = "green" if potencial >= 70 else "orange" if potencial >= 40 else "red"
            
            st.markdown(f"""
            <div style="background: #e0e0e0; border-radius: 10px; height: 20px; position: relative;">
                <div style="background: {cor}; width: {potencial}%; height: 20px; border-radius: 10px; transition: width 0.5s;">
                    <span style="position: absolute: right: 10px; top: 2px; color: black; font-weight: bold;">{potencial}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("🟢 Produtos com status Alto potencial")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.success("✅ Alta Demanda")
            with col_s2:
                st.success("✅ Baixa Concorrência")
    
    st.markdown("---")
    
    # ===== TABELA DE PRODUTOS DO DIA =====
    st.markdown("## 🎯 Sugestões de Produtos para Hoje")
    st.caption(f"📊 Top 3 do dia | {BUSCAS_DIARIAS} buscas realizadas")
    
    # FORÇA ATUALIZAÇÃO para buscar dados novos
    produtos = gerar_sugestoes_diarias(forcar_atualizacao=True)
    
    if produtos:
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            
            # USA A FUNÇÃO MELHORADA PARA PALAVRA-CHAVE
            dados_palavra = obter_palavra_chave(produto)
            palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
            
            dados_tabela.append({
                "Produto": item.get("Produto", ""),
                "🔑 Palavra-chave": palavra_chave,
                "Categoria": item.get("Categoria", "Geral"),
                "Evento": item.get("Evento", "Tendência"),
                "Potencial": item.get("Potencial", "🟡 Médio"),
                "Score": item.get("Score", 0),
                "Pins": item.get("Pins", "0"),
                "Crescimento": item.get("Crescimento", "+0%"),
                "Views TikTok": item.get("Views TikTok", "0M"),
                "Buscas no Mês": item.get("Buscas no Mês", "0"),
                "Resultados ML": item.get("Resultados ML", "0"),
                "Tendência": item.get("Tendência", "➡️ Estável")
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>'
        )
        
        colunas = ["Produto", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência", "Buscar na Shopee"]
        df = df[colunas]
        
        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
        
        st.caption(f"{BUSCAS_DIARIAS} de {BUSCAS_DIARIAS} consultas realizadas hoje")
        
        # ===== TOP 10 =====
        st.markdown("---")
        st.markdown("## 🏆 Top 10 Produtos em Tendência")
        st.caption("Ranking completo baseado em score e dados de mercado")
        
        top10 = gerar_top10_produtos(forcar_atualizacao=True)
        if top10:
            df_top10 = pd.DataFrame(top10)
            colunas_top10 = ["Produto", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Variação", "Tendência"]
            df_top10 = df_top10[colunas_top10]
            
            st.markdown(
                df_top10.to_html(escape=False, index=False),
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # ===== INSIGHTS ESTRATÉGICOS INTERATIVOS =====
    if produtos:
        render_insights_interativos(produtos)
    
    st.markdown("---")
    
    # ===== APOIADORES COMPACTOS (ABAIXO DOS INSIGHTS) =====
    render_apoiadores_compactos()
    
    st.markdown("---")
    
    st.markdown("## 📌 Legenda de Tendências")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🚀 Em alta**
        - Crescimento acelerado
        - Alta demanda
        """)
    with col2:
        st.markdown("""
        **📈 Crescendo**
        - Demanda moderada
        - Potencial de crescimento
        """)
    with col3:
        st.markdown("""
        **➡️ Estável**
        - Demanda consistente
        - Mercado maduro
        """)
    
    st.caption("Dados combinados: Shopee Trends + Google Shopping + TikTok")
    
    return df if 'df' in locals() else None

# ============================================================
# PAINEL DE APOIADORES DETALHADO (TAB)
# ============================================================
def render_painel_apoiadores_detalhado():
    """Renderiza o painel de apoiadores detalhado (para a Tab)"""
    
    st.markdown("## 👑 Gerenciar Apoiadores")
    st.caption("Lista completa de apoiadores do projeto")
    
    apoiadores = carregar_apoiadores()
    
    if not apoiadores:
        st.info("📭 Nenhum apoiador cadastrado ainda.")
        return
    
    # Ordena por ordem de entrada
    apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
    
    # Cores para os cards
    cores = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE",
        "#FD79A8", "#00B894", "#E17055", "#6C5CE7"
    ]
    
    # Exibe os apoiadores em cards (4 por linha)
    cols = st.columns(4)
    
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 4]:
            cor = cores[i % len(cores)]
            nome = apoiador.get("nome", "Apoiador")
            ordem = apoiador.get("ordem", 999)
            coroinha = apoiador.get("coroinha", "👑")
            data_entrada = apoiador.get("data_entrada", "2026-07-01")
            plano = apoiador.get("plano", "Apoiador")
            
            # Chave para remoção
            chave_apoiador = None
            for k, v in carregar_apoiadores().items():
                if v.get("nome") == nome and v.get("ordem") == ordem:
                    chave_apoiador = k
                    break
            
            with st.container(border=True):
                # Cabeçalho com cor
                st.markdown(f"""
                <div style="
                    background: {cor};
                    color: white;
                    padding: 8px 12px;
                    border-radius: 8px 8px 0 0;
                    margin: -12px -12px 10px -12px;
                    text-align: center;
                    font-weight: bold;
                ">
                    {coroinha} {nome}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**📋 Ordem:** #{ordem}")
                st.markdown(f"**📅 Entrada:** {data_entrada}")
                st.markdown(f"**📌 Plano:** {plano}")
                
                # Verifica repasse
                depois = sum(1 for k, d in apoiadores.items() if d.get("ordem", 999) > ordem)
                
                if depois > 0 and apoiador.get("repasse_ativo", True):
                    st.success(f"⬇️ {depois} apoiador(es) - R${depois * 5.00:.2f}/mês")
                else:
                    st.info("⏳ Aguardando novos apoiadores")
                
                # Botão Remover (apenas admin)
                if st.session_state.get("is_admin", False) and chave_apoiador:
                    if st.button(f"🗑️ Remover", key=f"remove_card_{chave_apoiador}"):
                        if remover_apoiador(chave_apoiador):
                            sistema = SistemaLicencas()
                            for codigo, dados in sistema.dados["licencas"].items():
                                if dados.get("usuario") == nome:
                                    sistema.revogar_licenca(codigo)
                                    break
                            st.success(f"✅ {nome} removido com sucesso!")
                            st.info("🔑 Licença revogada")
                            st.rerun()
    
    st.markdown("---")
    
    # ===== ADICIONAR APOIADOR (APENAS ADMIN) =====
    if st.session_state.get("is_admin", False):
        with st.expander("➕ Adicionar Apoiador", expanded=False):
            st.markdown("### Adicionar Novo Apoiador")
            
            col1, col2 = st.columns(2)
            with col1:
                nome_apo = st.text_input("Nome do Apoiador", placeholder="Ex: João Silva", key="apo_nome")
                email_apo = st.text_input("E-mail", placeholder="joao@email.com", key="apo_email")
            with col2:
                plano_apo = st.selectbox("Plano", ["Fundador", "Apoiador", "Premium"], key="apo_plano")
            
            if st.button("👑 Adicionar Apoiador", use_container_width=True, key="apo_btn"):
                if not nome_apo or not email_apo:
                    st.error("❌ Preencha nome e e-mail")
                else:
                    novo = adicionar_apoiador(nome_apo, email_apo, plano_apo)
                    st.success(f"✅ {nome_apo} adicionado como apoiador!")
                    st.info(f"📋 Ordem: #{novo.get('ordem')}")
                    st.rerun()
    
    st.markdown("---")
    
    # ===== REMOVER APOIADOR (APENAS ADMIN) =====
    if st.session_state.get("is_admin", False) and apoiadores_ordenados:
        st.markdown("### 🗑️ Remover Apoiador")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            nomes_apoiadores = [a.get("nome") for a in apoiadores_ordenados]
            apoiador_remover = st.selectbox(
                "Selecione um apoiador para remover:",
                options=nomes_apoiadores,
                key="remover_apoiador_select"
            )
        
        with col2:
            if st.button("🗑️ Remover", use_container_width=True, key="remover_apoiador_btn"):
                if apoiador_remover:
                    chave_remover = None
                    for k, v in carregar_apoiadores().items():
                        if v.get("nome") == apoiador_remover:
                            chave_remover = k
                            break
                    
                    if chave_remover:
                        if remover_apoiador(chave_remover):
                            sistema = SistemaLicencas()
                            for codigo, dados in sistema.dados["licencas"].items():
                                if dados.get("usuario") == apoiador_remover:
                                    sistema.revogar_licenca(codigo)
                                    break
                            st.success(f"✅ {apoiador_remover} removido com sucesso!")
                            st.info("🔑 Licença revogada")
                            st.rerun()
