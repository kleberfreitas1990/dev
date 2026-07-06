import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

from modules.models import (
    DADOS_COMPLETOS,
    PALAVRAS_CHAVE_CAUDA_LONGA,
    gerar_top10_produtos,
    gerar_sugestoes_diarias,
    BUSCAS_DIARIAS,
    carregar_apoiadores,
    adicionar_apoiador,
    remover_apoiador,
    SistemaLicencas
)
from modules.serper import buscar_produtos_serper

def render_apoiadores_ovais():
    """Renderiza os apoiadores em formato de ovais coloridos"""
    
    apoiadores = carregar_apoiadores()
    
    if not apoiadores:
        st.caption("📭 Nenhum apoiador ainda. Seja o primeiro!")
        return
    
    # Ordena por ordem de entrada
    apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
    
    # Cores pré-definidas para os ovais
    cores = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE",
        "#FD79A8", "#00B894", "#E17055", "#6C5CE7",
        "#FDCB6E", "#E17055", "#00CEC9", "#6C5CE7"
    ]
    
    st.markdown("### 👑 Apoiadores do Projeto")
    
    # Criar uma linha com todos os ovais
    html_ovais = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">'
    
    is_admin = st.session_state.get("is_admin", False)
    
    for i, apoiador in enumerate(apoiadores_ordenados):
        cor = cores[i % len(cores)]
        nome = apoiador.get("nome", "Apoiador")
        ordem = apoiador.get("ordem", 999)
        coroinha = apoiador.get("coroinha", "👑")
        
        # Encontra a chave do apoiador para remoção
        chave_apoiador = None
        for k, v in carregar_apoiadores().items():
            if v.get("nome") == nome and v.get("ordem") == ordem:
                chave_apoiador = k
                break
        
        # Adiciona o oval com cor diferente
        html_ovais += f'''
        <div style="
            background: {cor};
            color: white;
            padding: 6px 16px;
            border-radius: 50px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 2px solid rgba(255,255,255,0.3);
            cursor: default;
        ">
            <span>{coroinha}</span>
            <span>{nome}</span>
            <span style="font-size: 10px; opacity: 0.8;">#{ordem}</span>
        </div>
        '''
    
    html_ovais += '</div>'
    
    st.markdown(html_ovais, unsafe_allow_html=True)
    
    # ===== BOTÃO PARA REMOVER (APENAS ADMIN) =====
    if is_admin and apoiadores_ordenados:
        st.markdown("---")
        st.markdown("#### 🗑️ Gerenciar Apoiadores")
        
        # Seleciona um apoiador para remover
        nomes_apoiadores = [a.get("nome") for a in apoiadores_ordenados]
        apoiador_remover = st.selectbox(
            "Selecione um apoiador para remover:",
            options=nomes_apoiadores,
            key="remover_apoiador_select"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🗑️ Remover Apoiador", use_container_width=True, key="remover_apoiador_btn"):
                if apoiador_remover:
                    # Encontra a chave do apoiador
                    chave_remover = None
                    for k, v in carregar_apoiadores().items():
                        if v.get("nome") == apoiador_remover:
                            chave_remover = k
                            break
                    
                    if chave_remover:
                        # Remove o apoiador
                        if remover_apoiador(chave_remover):
                            # Revoga a licença associada
                            sistema = SistemaLicencas()
                            for codigo, dados in sistema.dados["licencas"].items():
                                if dados.get("usuario") == apoiador_remover:
                                    sistema.revogar_licenca(codigo)
                                    break
                            st.success(f"✅ {apoiador_remover} removido com sucesso!")
                            st.info("🔑 Licença revogada")
                            st.rerun()
        with col2:
            st.caption("⚠️ Remover um apoiador também revoga sua licença de acesso")

def render_painel_apoiadores_detalhado():
    """Renderiza o painel de apoiadores detalhado (para a Tab)"""
    
    st.markdown("## 👑 Gerenciar Apoiadores")
    st.caption("Lista completa de apoiadores do projeto")
    
    apoiadores = carregar_apoiadores()
    
    if not apoiadores:
        st.info("📭 Nenhum apoiador cadastrado ainda.")
    else:
        # Ordena por ordem de entrada
        apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
        
        # Exibe em cards (4 por linha)
        cols = st.columns(4)
        
        for i, apoiador in enumerate(apoiadores_ordenados):
            with cols[i % 4]:
                with st.container(border=True):
                    cor = apoiador.get("cor", "#FFD700")
                    
                    st.markdown(f"""
                    <div style="text-align: center; padding: 8px 0;">
                        <span style="font-size: 32px;">{apoiador.get('coroinha', '👑')}</span>
                        <h4 style="color: {cor}; margin: 2px 0; font-size: 16px;">{apoiador.get('nome')}</h4>
                        <p style="color: #888; font-size: 11px; margin: 0;">#{apoiador.get('ordem', 999)} • Apoiador</p>
                        <p style="color: #666; font-size: 10px; margin: 0;">{apoiador.get('plano', 'Apoiador')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.caption(f"📅 {apoiador.get('data_entrada', '2026-07-01')}")
    
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
    
    produtos = gerar_sugestoes_diarias()
    
    if produtos:
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            dados_palavra = PALAVRAS_CHAVE_CAUDA_LONGA.get(produto, {})
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
        
        top10 = gerar_top10_produtos()
        df_top10 = pd.DataFrame(top10)
        colunas_top10 = ["Produto", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Variação", "Tendência"]
        df_top10 = df_top10[colunas_top10]
        
        st.markdown(
            df_top10.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # ===== INSIGHTS ESTRATÉGICOS =====
    st.markdown("## 💡 Insights Estratégicos - Top 3")
    
    if produtos:
        top3 = sorted(produtos, key=lambda x: x.get("Score", 0), reverse=True)[:3]
        cols = st.columns(3)
        
        for i, item in enumerate(top3):
            with cols[i]:
                produto = item.get("Produto", "").lower()
                dados_palavra = PALAVRAS_CHAVE_CAUDA_LONGA.get(produto, {})
                palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
                hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])
                
                with st.container(border=True):
                    st.markdown(f"### 🥇 {item.get('Produto', '')}")
                    st.markdown(f"""
                    - **Categoria:** {item.get('Categoria', 'Geral')}
                    - **Score:** {item.get('Score', 0)}/10
                    - **Pins:** {item.get('Pins', '0')}
                    - **Crescimento:** {item.get('Crescimento', '+0%')}
                    - **Views TikTok:** {item.get('Views TikTok', '0M')}
                    - **Tendência:** {item.get('Tendência', '➡️ Estável')}
                    """)
                    st.info(f"🔑 **Palavra-chave:** {palavra_chave}")
                    
                    st.markdown("**🏷️ Hashtags sugeridas:**")
                    tags_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 2px 8px; border-radius: 12px; margin: 2px; font-size: 12px;">{h}</span>' for h in hashtags])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                    st.success("🚀 **Ação:** Crie conteúdo sobre este produto!")
    
    st.markdown("---")
    
    # ===== APOIADORES EM OVAIS COLORIDOS =====
    render_apoiadores_ovais()
    
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
