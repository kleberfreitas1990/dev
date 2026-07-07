import streamlit as st
import pandas as pd
import random
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

# Importa grade de descoberta
from modules.grade_descoberta import (
    descobrir_produtos_grade,
    enriquecer_produto,
    get_produtos_sazonais,
    get_produtos_sazonais_com_motivos,
    GRADE_PRODUTOS,
    obter_motivo_busca,
    obter_indicadores_horario,
    obter_historico_buscas
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
# GRADE DE DESCOBERTA - SOMENTE TABELA
# ============================================================
def render_grade_descoberta():
    """
    Renderiza a grade de descoberta de produtos em formato de tabela
    """
    st.markdown("## 🎯 Grade de Descoberta de Produtos")
    st.caption("Produtos em tendência descobertos automaticamente - Análise baseada em dados do Pinterest e Google Trends")
    
    # ============================================================
    # FILTROS
    # ============================================================
    col1, col2 = st.columns([2, 1])
    
    with col1:
        categoria_filtro = st.selectbox(
            "Filtrar por categoria:",
            ["Todas", "moda", "eletrônico", "beleza", "casa", "infantil", "esporte"],
            index=0
        )
    
    with col2:
        quantidade = st.selectbox(
            "Quantidade:",
            [5, 10, 15, 20],
            index=1
        )
    
    # ============================================================
    # BUSCA PRODUTOS
    # ============================================================
    with st.spinner("🔍 Descobrindo produtos..."):
        categoria = None if categoria_filtro == "Todas" else categoria_filtro
        produtos_descobrir = descobrir_produtos_grade(categoria=categoria, quantidade=quantidade)
    
    if not produtos_descobrir:
        st.info("📭 Nenhum produto encontrado na grade de descoberta.")
        return
    
    # ============================================================
    # EXIBE EM TABELA
    # ============================================================
    st.markdown(f"### 📦 {len(produtos_descobrir)} produtos descobertos")
    
    # Cria DataFrame
    dados_tabela = []
    for item in produtos_descobrir:
        produto = item.get("produto", "").capitalize()
        score = item.get("score", 0)
        categoria = item.get("categoria", "Geral").capitalize()
        motivo = item.get("motivo", "📊 Produto em tendência no mercado")
        indicadores = item.get("indicadores", {})
        
        # Status de score
        if score >= 8:
            status = "🔥 Alta"
        elif score >= 6:
            status = "📈 Média"
        else:
            status = "📊 Baixa"
        
        # Palavra-chave e hashtags
        dados_palavra = obter_palavra_chave(produto)
        palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
        hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:3]
        
        # Horário
        horario = indicadores.get("horario", "10h-12h") if indicadores else "10h-12h"
        intensidade = indicadores.get("porcentagem", 50) if indicadores else 50
        
        dados_tabela.append({
            "Produto": produto,
            "Categoria": categoria,
            "Score": f"{score}/10",
            "Status": status,
            "Palavra-chave": palavra_chave,
            "Hashtags": " ".join(hashtags),
            "Melhor Horário": horario,
            "Intensidade": f"{intensidade}%",
            "Motivo": motivo[:80] + "..."
        })
    
    df = pd.DataFrame(dados_tabela)
    
    # Exibe tabela com st.dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Produto": st.column_config.TextColumn("Produto", width="medium"),
            "Categoria": st.column_config.TextColumn("Categoria", width="small"),
            "Score": st.column_config.TextColumn("Score", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Palavra-chave": st.column_config.TextColumn("Palavra-chave", width="large"),
            "Hashtags": st.column_config.TextColumn("Hashtags", width="medium"),
            "Melhor Horário": st.column_config.TextColumn("Melhor Horário", width="small"),
            "Intensidade": st.column_config.TextColumn("Intensidade", width="small"),
            "Motivo": st.column_config.TextColumn("Motivo", width="large"),
        }
    )

# ============================================================
# APOIADORES EM CARDS PEQUENOS
# ============================================================
def render_apoiadores_compactos():
    """Renderiza os apoiadores em cards pequenos com coroa centralizada"""
    
    apoiadores = carregar_apoiadores()
    
    if not apoiadores:
        return
    
    st.markdown("### 👑 Apoiadores do Projeto")
    st.caption("Pessoas que acreditam e apoiam este projeto")
    
    apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
    
    cores = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE",
        "#FD79A8", "#00B894", "#E17055", "#6C5CE7"
    ]
    
    cols = st.columns(6)
    
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 6]:
            cor = cores[i % len(cores)]
            nome = apoiador.get("nome", "Apoiador")
            ordem = apoiador.get("ordem", 999)
            coroinha = apoiador.get("coroinha", "👑")
            
            with st.container(border=True):
                st.markdown(f"""
                <div style="text-align: center; font-size: 28px; margin: -8px 0 2px 0;">
                    {coroinha}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="text-align: center; font-weight: bold; font-size: 13px; margin: 0;">
                    {nome}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="text-align: center; font-size: 10px; color: #888; margin: 0;">
                    #{ordem}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="
                    background: {cor};
                    height: 3px;
                    border-radius: 2px;
                    margin: 4px 0 2px 0;
                ">
                </div>
                """, unsafe_allow_html=True)
                
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
# INSIGHTS ESTRATÉGICOS - SEM PLOTLY
# ============================================================
def render_insights_estrategicos(produtos):
    """
    Renderiza insights estratégicos sem Plotly (usando apenas Streamlit)
    """
    
    st.markdown("## 💡 Insights Estratégicos")
    st.caption("Análise de mercado baseada em dados do Pinterest e Google Trends")
    
    # ============================================================
    # PRODUTOS SAZONAIS - TABELA
    # ============================================================
    sazonais = get_produtos_sazonais_com_motivos()
    
    if sazonais:
        st.markdown("### 📅 Produtos Sazonais do Mês")
        st.caption("Produtos em alta devido à temporada atual")
        
        dados_sazonais = []
        for item in sazonais[:4]:
            produto = item.get("produto", "").capitalize()
            motivo = item.get("motivo", "")
            
            indicadores = obter_indicadores_horario(produto)
            horario = indicadores.get("melhor_horario", "19h-22h") if indicadores else "19h-22h"
            intensidade = indicadores.get("porcentagem", 70) if indicadores else 70
            
            dados_palavra = obter_palavra_chave(produto)
            palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
            hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:2]
            
            dados_sazonais.append({
                "Produto": produto,
                "Motivo": motivo[:60] + "...",
                "Melhor Horário": horario,
                "Intensidade": f"{intensidade}%",
                "Palavra-chave": palavra_chave,
                "Hashtags": " ".join(hashtags)
            })
        
        df_sazonais = pd.DataFrame(dados_sazonais)
        st.dataframe(df_sazonais, use_container_width=True, hide_index=True)
    
    # ============================================================
    # TOP 3 PRODUTOS - TABELA E MÉTRICAS
    # ============================================================
    st.markdown("---")
    st.markdown("### 🏆 Top 3 Produtos do Mês")
    st.caption("Produtos com maior potencial - Use essas informações para criar conteúdo")
    
    if produtos:
        top3 = sorted(produtos, key=lambda x: x.get("Score", 0), reverse=True)[:3]
        
        # ============================================================
        # EXIBE SCORES COMO MÉTRICAS
        # ============================================================
        cols = st.columns(3)
        for i, item in enumerate(top3):
            with cols[i]:
                produto_nome = item.get("Produto", "")
                score = item.get("Score", 0)
                
                # Define cor baseada no score
                if score >= 8:
                    cor = "🟢"
                elif score >= 6:
                    cor = "🟡"
                else:
                    cor = "🔴"
                
                st.metric(
                    label=f"{['🥇', '🥈', '🥉'][i]} {produto_nome}",
                    value=f"{score}/10",
                    delta=f"{cor} {item.get('Crescimento', '+0%')}"
                )
        
        # ============================================================
        # TABELA DOS TOP 3
        # ============================================================
        dados_top3 = []
        for item in top3:
            produto_nome = item.get("Produto", "")
            
            indicadores = obter_indicadores_horario(produto_nome)
            horario = indicadores.get("melhor_horario", "19h-22h") if indicadores else "19h-22h"
            
            dados_palavra = obter_palavra_chave(produto_nome)
            palavra_chave = dados_palavra.get("palavra", f"{produto_nome} tendência 2026")
            hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:3]
            
            dados_top3.append({
                "Produto": produto_nome,
                "Score": f"{item.get('Score', 0)}/10",
                "Crescimento": item.get('Crescimento', '+0%'),
                "Views TikTok": item.get('Views TikTok', '0M'),
                "Pins": item.get('Pins', '0'),
                "Palavra-chave": palavra_chave,
                "Hashtags": " ".join(hashtags),
                "Melhor Horário": horario
            })
        
        df_top3 = pd.DataFrame(dados_top3)
        st.dataframe(df_top3, use_container_width=True, hide_index=True)
    
    # ============================================================
    # TENDÊNCIAS DE MERCADO
    # ============================================================
    st.markdown("---")
    st.markdown("### 📊 Tendências de Mercado")
    st.caption("O que está em alta no Pinterest e Google Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("**📌 Pinterest Trends**")
            st.caption("O que as pessoas estão salvando:")
            st.markdown("""
            - ✅ Looks de inverno + casacos
            - ✅ Organização minimalista
            - ✅ Decoração de Natal
            - ✅ Receitas fitness
            """)
            
            st.markdown("**🔑 Palavras-chave:**")
            st.markdown("`look inverno`, `organização casa`, `decoração natal`, `receitas saudáveis`")
    
    with col2:
        with st.container(border=True):
            st.markdown("**🔍 Google Trends**")
            st.caption("O que as pessoas estão pesquisando:")
            st.markdown("""
            - ✅ "Melhor smartwatch 2026"
            - ✅ "Casaco feminino preço"
            - ✅ "Presentes para mães"
            - ✅ "Brinquedos educativos 2 anos"
            """)
            
            st.markdown("**🏷️ Hashtags em alta:**")
            st.markdown("#smartwatch2026 #modainverno #presentes #brinquedoseducativos")

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
    
    # ============================================================
    # VISÃO GERAL DO MÊS - DINÂMICA
    # ============================================================
    st.markdown("## 📊 Visão Geral do Mês")
    
    produtos_top = gerar_top10_produtos(forcar_atualizacao=False)
    
    if produtos_top:
        top1 = produtos_top[0] if produtos_top else None
        
        scores = [p.get("Score", 0) for p in produtos_top]
        crescimentos = [float(p.get("Crescimento", "+0%").replace("+", "").replace("%", "")) for p in produtos_top]
        
        score_medio = sum(scores) / len(scores) if scores else 0
        crescimento_medio = sum(crescimentos) / len(crescimentos) if crescimentos else 0
        
        categorias = [p.get("Categoria", "Geral") for p in produtos_top]
        categoria_mais_freq = max(set(categorias), key=categorias.count) if categorias else "Geral"
        
        eventos = [p.get("Evento", "Tendência") for p in produtos_top]
        evento_mais_freq = max(set(eventos), key=eventos.count) if eventos else "Tendência"
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.container(border=True):
                if top1:
                    st.markdown(f"""
                    **🔥 {top1.get('Produto', 'Produto')} em alta!** 
                    Com score {top1.get('Score', 0)}/10 e {top1.get('Crescimento', '+0%')} de crescimento, 
                    este é o momento ideal para criar conteúdo sobre este produto.
                    """)
                else:
                    st.markdown("**📊 Análise de mercado em tempo real**")
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric(
                        "🔥 Produto em Alta", 
                        top1.get("Produto", "N/A") if top1 else "N/A",
                        delta=top1.get("Categoria", "Moda") if top1 else "N/A"
                    )
                with m2:
                    st.metric(
                        "📈 Crescimento Médio", 
                        f"{crescimento_medio:.1f}%",
                        delta=f"{crescimento_medio - 5:.1f}%"
                    )
                with m3:
                    st.metric(
                        "🎯 Categoria em Alta", 
                        categoria_mais_freq,
                        delta=evento_mais_freq
                    )
        
        with col2:
            with st.container(border=True):
                st.markdown("### 🎯 Melhor Oportunidade")
                
                melhor_score = max(produtos_top, key=lambda x: x.get("Score", 0)) if produtos_top else None
                
                if melhor_score:
                    produto_nome = melhor_score.get('Produto', 'N/A')
                    
                    indicadores = obter_indicadores_horario(produto_nome)
                    
                    st.markdown(f"**{produto_nome}**")
                    st.caption(f"Score: {melhor_score.get('Score', 0)}/10")
                    
                    if indicadores:
                        st.markdown(f"""
                        <div style="background: #f0f0f0; padding: 4px 8px; border-radius: 6px; margin: 4px 0; font-size: 11px; color: #333; text-align: center;">
                            {indicadores.get('emoji', '🕐')} Melhor horário: <strong>{indicadores.get('melhor_horario', '19h-22h')}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    potencial = melhor_score.get("Score", 0) * 10
                    cor = "green" if potencial >= 70 else "orange" if potencial >= 40 else "red"
                    
                    st.markdown(f"""
                    <div style="margin: 8px 0;">
                        <small>Potencial de Mercado</small>
                        <div style="background: #e0e0e0; border-radius: 10px; height: 20px; position: relative; overflow: hidden;">
                            <div style="background: {cor}; width: {potencial}%; height: 20px; border-radius: 10px; transition: width 0.5s;">
                                <span style="position: absolute; left: 50%; top: 2px; color: {'white' if potencial > 50 else 'black'}; font-weight: bold; font-size: 12px;">{potencial:.0f}%</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.caption(f"🟢 {melhor_score.get('Potencial', 'Médio')} potencial")
                    
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        st.success(f"✅ {melhor_score.get('Score', 0)}/10 Score")
                    with col_s2:
                        st.success(f"📈 {melhor_score.get('Crescimento', '+0%')}")
                else:
                    st.info("📊 Aguardando dados...")
    
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.container(border=True):
                st.markdown("""
                **📊 Análise de mercado em tempo real**
                Buscando os melhores produtos para você criar conteúdo.
                """)
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("🔥 Produto em Alta", "Aguardando", delta="...")
                with m2:
                    st.metric("📈 Crescimento Médio", "0%", delta="0%")
                with m3:
                    st.metric("🎯 Categoria em Alta", "Geral", delta="Tendência")
        
        with col2:
            with st.container(border=True):
                st.markdown("### 🎯 Melhor Oportunidade")
                st.info("📊 Carregando dados...")
                st.caption("🟢 Aguardando análise")
    
    st.markdown("---")
    
    # ============================================================
    # GRADE DE DESCOBERTA (TABELA)
    # ============================================================
    render_grade_descoberta()
    
    st.markdown("---")
    
    # ===== TABELA DE PRODUTOS DO DIA =====
    st.markdown("## 🎯 Sugestões de Produtos para Hoje")
    st.caption(f"📊 Top 3 do dia | {BUSCAS_DIARIAS} buscas realizadas")
    
    produtos = gerar_sugestoes_diarias(forcar_atualizacao=True)
    
    if produtos:
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            
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
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Produto": st.column_config.TextColumn("Produto", width="medium"),
                "🔑 Palavra-chave": st.column_config.TextColumn("Palavra-chave", width="large"),
                "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                "Evento": st.column_config.TextColumn("Evento", width="medium"),
                "Potencial": st.column_config.TextColumn("Potencial", width="small"),
                "Score": st.column_config.NumberColumn("Score", width="small"),
                "Pins": st.column_config.TextColumn("Pins", width="small"),
                "Crescimento": st.column_config.TextColumn("Crescimento", width="small"),
                "Views TikTok": st.column_config.TextColumn("Views TikTok", width="small"),
                "Buscas no Mês": st.column_config.TextColumn("Buscas no Mês", width="small"),
                "Resultados ML": st.column_config.TextColumn("Resultados ML", width="small"),
                "Tendência": st.column_config.TextColumn("Tendência", width="medium"),
            }
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
            
            st.dataframe(
                df_top10,
                use_container_width=True,
                hide_index=True
            )
    
    st.markdown("---")
    
    # ===== INSIGHTS ESTRATÉGICOS =====
    if produtos:
        render_insights_estrategicos(produtos)
    
    st.markdown("---")
    
    # ===== APOIADORES COMPACTOS =====
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
    
    apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
    
    cores = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE",
        "#FD79A8", "#00B894", "#E17055", "#6C5CE7"
    ]
    
    cols = st.columns(4)
    
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 4]:
            cor = cores[i % len(cores)]
            nome = apoiador.get("nome", "Apoiador")
            ordem = apoiador.get("ordem", 999)
            coroinha = apoiador.get("coroinha", "👑")
            data_entrada = apoiador.get("data_entrada", "2026-07-01")
            plano = apoiador.get("plano", "Apoiador")
            
            chave_apoiador = None
            for k, v in carregar_apoiadores().items():
                if v.get("nome") == nome and v.get("ordem") == ordem:
                    chave_apoiador = k
                    break
            
            with st.container(border=True):
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
                
                depois = sum(1 for k, d in apoiadores.items() if d.get("ordem", 999) > ordem)
                
                if depois > 0 and apoiador.get("repasse_ativo", True):
                    st.success(f"⬇️ {depois} apoiador(es) - R${depois * 5.00:.2f}/mês")
                else:
                    st.info("⏳ Aguardando novos apoiadores")
                
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
