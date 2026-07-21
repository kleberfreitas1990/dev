import math
import streamlit as st
import pandas as pd
import random
from datetime import datetime
from urllib.parse import quote
import os

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
    obter_indicadores_horario
)

# Importa para verificar data do cache e dados dinâmicos
from modules.produtos_dinamicos import verificar_data_cache, obter_produtos_dinamicos

# Tenta importar serper, se falhar usa fallback
try:
    from modules.serper import buscar_produtos_serper
    SERPER_DISPONIVEL = True
except ImportError:
    SERPER_DISPONIVEL = False
    def buscar_produtos_serper(termo, limite=5):
        return []

def _normalizar_score_exibicao(valor) -> float:
    """Converte pontuações externas para a escala segura de 0 a 10."""
    try:
        score = float(valor)
    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(score):
        return 0.0
    return max(0.0, min(score, 10.0))


def _formatar_score(score: float) -> str:
    """Exibe inteiros sem casas decimais, mantendo precisão quando necessária."""
    return f"{score:g}"


# ============================================================
# STATUS DO USUÁRIO (REMOVIDO)
# ============================================================
def render_status_usuario():
    """Renderiza o status do usuário - REMOVIDO"""
    pass

# ============================================================
# SIDEBAR DE CATEGORIAS DINÂMICAS
# ============================================================
def render_sidebar_categorias(key_suffix: str = "") -> str:
    """
    Renderiza a barra lateral com categorias dinâmicas extraídas dos dados reais.
    Retorna a categoria selecionada pelo usuário (ou 'Todas' para sem filtro).
    """
    st.sidebar.markdown("## 🏷️ Filtrar por Categoria")
    st.sidebar.caption("Categorias extraídas dos termos em alta")

    # Coleta categorias de todas as fontes ativas
    try:
        todos_produtos = obter_produtos_dinamicos(forcar_atualizacao=False)
        categorias_dinamicas = sorted({
            dados.get("categoria", "Marketplace")
            for dados in todos_produtos.values()
            if isinstance(dados, dict) and dados.get("categoria")
        })
    except Exception:
        categorias_dinamicas = []

    # Complementa com categorias fixas se necessário
    categorias_fixas = [
        "Eletrônicos", "Moda", "Casa", "Beleza",
        "Games", "Livros", "Brinquedos", "Saúde",
        "Eletrodomésticos", "Veículos", "Marketplace"
    ]
    todas_categorias = sorted(set(categorias_dinamicas + categorias_fixas))
    opcoes = ["Todas as Categorias"] + todas_categorias

    # Contagem de produtos por categoria
    contagem: dict = {}
    try:
        for dados in todos_produtos.values():
            if isinstance(dados, dict):
                cat = dados.get("categoria", "Marketplace")
                contagem[cat] = contagem.get(cat, 0) + 1
    except Exception:
        pass

    # Selectbox de categorias com chave única
    categoria_sel = st.sidebar.selectbox(
        "Categoria",
        opcoes,
        index=0,
        key=f"sidebar_categoria_filtro_{key_suffix}",
        label_visibility="collapsed",
    )

    # Exibe contagem da categoria selecionada
    if categoria_sel != "Todas as Categorias":
        total_cat = contagem.get(categoria_sel, 0)
        st.sidebar.metric(
            f"📦 {categoria_sel}",
            f"{total_cat} produto{'s' if total_cat != 1 else ''}",
        )

    st.sidebar.markdown("---")

    # Painel de status das fontes
    st.sidebar.markdown("### 📶 Status das Fontes")
    try:
        from modules.mercadolivre_scraper import obter_status_cache_ml
        status_ml = obter_status_cache_ml()
        icone_ml = "✅" if status_ml.get("valido") else "⚠️"
        st.sidebar.markdown(
            f"{icone_ml} **Mercado Livre** — {status_ml.get('total', 0)} itens  \n"
            f"<small>{status_ml.get('data_formatada', 'N/A')}</small>",
            unsafe_allow_html=True,
        )
    except Exception:
        st.sidebar.markdown("⚠️ **Mercado Livre** — indisponível")

    try:
        from modules.google_shopee_trends import obter_status_cache
        status_geral = obter_status_cache()
        s_google = status_geral.get("google_trends", {})
        s_shopee = status_geral.get("shopee", {})
        icone_g = "✅" if s_google.get("valido") else "⚠️"
        icone_s = "✅" if s_shopee.get("valido") else "⚠️"
        st.sidebar.markdown(
            f"{icone_g} **Google Trends** — {s_google.get('total', 0)} itens  \n"
            f"{icone_s} **Shopee** — {s_shopee.get('total', 0)} itens"
        )
    except Exception:
        st.sidebar.markdown("⚠️ **Google/Shopee** — indisponível")

    st.sidebar.markdown("---")

    # Botão de atualização rápida
    if st.sidebar.button(
        "🔄 Atualizar Fontes",
        use_container_width=True,
        key=f"sidebar_btn_atualizar_{key_suffix}",
    ):
        with st.sidebar:
            with st.spinner("📡 Atualizando..."):
                try:
                    produtos_atualizados = obter_produtos_dinamicos(forcar_atualizacao=True)
                    st.session_state["ultima_atualizacao_auto"] = datetime.now()
                    st.session_state["ultima_atualizacao_google_shopee"] = datetime.now()
                    st.success(f"✅ {len(produtos_atualizados)} produtos atualizados!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {e}")

    return categoria_sel if categoria_sel != "Todas as Categorias" else None


# ============================================================
# GRADE DE DESCOBERTA - SOMENTE TABELA
# ============================================================
def render_grade_descoberta(key_suffix: str = "main"):
    """
    Renderiza a grade de descoberta de produtos em formato de tabela,
    com suporte a filtro de categoria via sidebar dinâmica.
    """
    st.markdown("## 🎯 Grade de Descoberta de Produtos")
    st.caption("Produtos em tendência descobertos automaticamente — Dados reais ML, Shopee, Amazon e Google Trends")

    # Sidebar de categorias dinâmicas com chave única
    categoria_filtro = render_sidebar_categorias(key_suffix=key_suffix)

    # Controles de quantidade e fonte
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 1])
    with col_ctrl1:
        quantidade = st.select_slider(
            "📦 Quantidade de produtos",
            options=[10, 15, 20, 25, 30],
            value=20,
            key=f"grade_quantidade_slider_{key_suffix}",
        )
    with col_ctrl2:
        fonte_filtro = st.selectbox(
            "📶 Filtrar por Fonte",
            ["Todas as Fontes", "Shopee Live", "Amazon Bestsellers", "Mercado Livre Trends", "Shopee Real-Time Scraping"],
            key=f"grade_fonte_filtro_{key_suffix}",
        )
    with col_ctrl3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "🔄",
            help="Recarregar grade",
            key=f"grade_btn_reload_{key_suffix}",
        ):
            st.rerun()

    # ============================================================
    # BUSCA PRODUTOS
    # ============================================================
    with st.spinner("🔍 Descobrindo produtos..."):
        produtos_descobrir = descobrir_produtos_grade(
            categoria=categoria_filtro,
            quantidade=quantidade if fonte_filtro == "Todas as Fontes" else quantidade * 2,
        )

    # Aplica filtro de fonte
    if fonte_filtro != "Todas as Fontes":
        produtos_descobrir = [
            p for p in produtos_descobrir
            if p.get("fonte", "") == fonte_filtro
        ][:quantidade]

    if not produtos_descobrir:
        st.info("💭 Nenhum produto encontrado para os filtros selecionados.")
        return

    # ============================================================
    # EXIBE EM TABELA
    # ============================================================
    label_cat = f" — Categoria: **{categoria_filtro}**" if categoria_filtro else ""
    label_fonte = f" | Fonte: **{fonte_filtro}**" if fonte_filtro != "Todas as Fontes" else ""
    st.markdown(f"### 📦 {len(produtos_descobrir)} produtos descobertos{label_cat}{label_fonte}")

    # Cria DataFrame
    dados_tabela = []
    for item in produtos_descobrir:
        produto = item.get("produto", "").capitalize()
        score = _normalizar_score_exibicao(item.get("score", 0))
        cat_item = item.get("categoria", "Geral").capitalize()
        motivo = item.get("motivo", "📊 Produto em tendência no mercado")
        indicadores = item.get("indicadores", {})
        fonte_item = item.get("fonte", "")

        # Status de score com badge colorido
        if score >= 9:
            status = "🔥 Explosivo"
        elif score >= 8:
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

        # Link de busca na Shopee
        link_shopee = f"https://shopee.com.br/search?keyword={quote(produto)}"

        dados_tabela.append({
            "Produto": produto,
            "Link Shopee": link_shopee,
            "Fonte": fonte_item,
            "Score": score,
            "Status": status,
            "Palavra-chave": palavra_chave,
            "Hashtags": " ".join(hashtags),
            "Melhor Horário": horario,
            "Intensidade %": intensidade,
            "Motivo": motivo[:80] + "...",
        })

    df = pd.DataFrame(dados_tabela)

    # Exibe tabela com st.dataframe e barras de progresso
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Produto": st.column_config.TextColumn("Produto", width="medium"),
            "Link Shopee": st.column_config.LinkColumn(
                "🛒 Shopee",
                help="Buscar produto na Shopee",
                validate="^https://shopee\\.com\\.br/.*",
                display_text="Buscar",
                width="small",
            ),
            "Fonte": st.column_config.TextColumn("Fonte", width="small"),
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=10,
                format="%d/10",
                width="small",
            ),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Palavra-chave": st.column_config.TextColumn("Palavra-chave", width="large"),
            "Hashtags": st.column_config.TextColumn("Hashtags", width="medium"),
            "Melhor Horário": st.column_config.TextColumn("Melhor Horário", width="small"),
            "Intensidade %": st.column_config.ProgressColumn(
                "Intensidade",
                min_value=0,
                max_value=100,
                format="%d%%",
                width="small",
            ),
            "Motivo": st.column_config.TextColumn("Motivo", width="large"),
        },
    )

# ============================================================
# APOIADORES EM CARDS PEQUENOS
# ============================================================
def render_apoiadores_compactos():
    """Renderiza os apoiadores em cards pequenos com coroa centralizada"""
    
    from modules.auth import listar_apoiadores_por_licencas
    apoiadores_lista = listar_apoiadores_por_licencas()
    
    # Converter lista para o formato esperado pelo dicionário de apoiadores
    apoiadores = {}
    for i, apo in enumerate(apoiadores_lista):
        apoiadores[apo['codigo']] = {
            "nome": apo['nome'],
            "ordem": i + 1,
            "coroinha": "👑",
            "repasse_ativo": True
        }
    
    if not apoiadores:
        st.info("📭 Nenhum apoiador ativo encontrado nas licenças.")
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
# INSIGHTS ESTRATÉGICOS - SEM TENDÊNCIAS DE MERCADO
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
# DASHBOARD PRINCIPAL
# ============================================================
def render_dashboard():
    """Renderiza o dashboard principal"""
    
    # Status do topo removido a pedido do usuário
    pass
    
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.title("📊 Minerador de Produtos")
        st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    with col_refresh:
        # Botão removido - Atualização agora é 100% automática a cada 12 horas
        st.empty()
    
    # ============================================================
    # VISÃO GERAL DO MÊS - COMPLETA
    # ============================================================
    st.markdown("## 📊 Visão Geral do Mês")
    
    # Forçar dados v5.0 - Sincronizado com a busca real
    from modules.produtos_dinamicos import obter_produtos_marketplace_v49
    # Na v9.3, garantimos que o cache seja lido corretamente
    produtos_top_base = obter_produtos_marketplace_v49(forcar_atualizacao=False)
    
    # Converter para formato de lista para o Top 10
    produtos_top = []
    for nome, dados in produtos_top_base.items():
        item = dados.copy()
        item["Produto"] = nome
        item["Crescimento"] = f"+{dados.get('crescimento', 0)}%"
        item["Categoria"] = dados.get("categoria", "Geral")
        item["Evento"] = dados.get("evento", "Tendência")
        item["Score"] = _normalizar_score_exibicao(dados.get("score", 0))
        item["Fonte"] = dados.get("fonte", "Shopee")
        produtos_top.append(item)
    
    produtos_top = sorted(produtos_top, key=lambda x: x.get("Score", 0), reverse=True)[:10]
    produtos_sugestoes = produtos_top[:5]
    
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
        
        # LINHA 1: MENSAGEM DESTAQUE
        if top1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 16px;
                text-align: center;
            ">
                <span style="font-size: 18px; font-weight: bold;">🔥 {top1.get('Produto', 'Produto')} em alta!</span>
                <span style="font-size: 15px; margin-left: 10px;">
                    Com score {top1.get('Score', 0)}/10 e {top1.get('Crescimento', '+0%')} de crescimento.
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # LINHA 2: MÉTRICAS + OPORTUNIDADE
        col1, col2 = st.columns([2, 1])
        with col1:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(
                    label="🔥 Produto em Alta",
                    value=top1.get("Produto", "N/A") if top1 else "N/A",
                    delta=top1.get("Categoria", "Moda") if top1 else "N/A",
                )
            with m2:
                delta_crescimento = crescimento_medio - 5
                st.metric(
                    label="📈 Crescimento Médio",
                    value=f"{crescimento_medio:.1f}%",
                    delta=f"{delta_crescimento:+.1f}% vs base",
                    delta_color="normal",
                )
            with m3:
                st.metric(
                    label="🎯 Categoria em Alta",
                    value=categoria_mais_freq,
                    delta=evento_mais_freq,
                )

        with col2:
            with st.container(border=True):
                st.markdown("### 🎯 Melhor Oportunidade")
                melhor_score = max(produtos_top, key=lambda x: x.get("Score", 0)) if produtos_top else None
                if melhor_score:
                    cresc_val = float(
                        melhor_score.get("Crescimento", "+0%")
                        .replace("+", "").replace("%", "")
                    )
                    score_val = _normalizar_score_exibicao(melhor_score.get("Score", 0))
                    st.markdown(f"**{melhor_score.get('Produto', 'N/A')}**")
                    st.progress(
                        score_val / 10.0,
                        text=f"⭐ Score: {_formatar_score(score_val)}/10",
                    )
                    cor_cresc = "normal" if cresc_val >= 0 else "inverse"
                    st.metric(
                        label="Crescimento",
                        value=f"{cresc_val:.1f}%",
                        delta=f"{cresc_val - crescimento_medio:+.1f}% vs média",
                        delta_color=cor_cresc,
                    )
                else:
                    st.info("📊 Aguardando dados...")

        # LINHA 3: RANKING DE CRESCIMENTO PERCENTUAL (TOP 5) — COMPACTO
        st.markdown("---")
        st.markdown("### 📈 Top 5 Crescimento Real")
        
        top5_cresc = sorted(
            produtos_top,
            key=lambda x: float(x.get("Crescimento", "+0%").replace("+", "").replace("%", "")),
            reverse=True,
        )[:5]
        
        # Exibição compacta em colunas horizontais
        cols_cresc = st.columns(5)
        for i, prod in enumerate(top5_cresc):
            with cols_cresc[i]:
                cresc = float(prod.get("Crescimento", "+0%").replace("+", "").replace("%", ""))
                score_p = prod.get("Score", 0)
                nome_p = prod.get("Produto", "N/A")
                medalha = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                
                with st.container(border=True):
                    st.markdown(f"**{medalha} {nome_p[:15]}...**")
                    st.metric("Crescimento", f"+{cresc:.0f}%", delta=f"⭐ {score_p}")
                    st.progress(max(0.0, min(cresc / 200.0, 1.0)))
    else:
        st.info("📊 Buscando dados de mercado...")

    st.markdown("---")
    
    # ===== INSIGHTS ESTRATÉGICOS =====
    if produtos_sugestoes:
        render_insights_estrategicos(produtos_sugestoes)
    
    st.markdown("---")
    
    # ===== GRADES UNIFICADAS COM SUB-ABAS =====
    render_grades_unificadas()
    
    st.markdown("---")
    
    # ===== APOIADORES COMPACTOS =====
    render_apoiadores_compactos()

# ============================================================
# PAINEL DE APOIADORES DETALHADO
# ============================================================
def render_painel_apoiadores_detalhado():
    """Renderiza o painel completo de gestão de apoiadores"""
    st.markdown("## 👑 Gestão de Apoiadores")
    st.caption("Controle completo da rede de apoio e repasses")
    
    from modules.auth import listar_apoiadores_por_licencas
    apoiadores_lista = listar_apoiadores_por_licencas()
    
    # Converter lista
    apoiadores = {}
    for i, apo in enumerate(apoiadores_lista):
        apoiadores[apo['codigo']] = {
            "nome": apo['nome'],
            "ordem": i + 1,
            "data_entrada": datetime.now().strftime("%Y-%m-%d"),
            "repasse_ativo": True
        }
    
    if not apoiadores:
        st.info("📭 Nenhum apoiador ativo encontrado nas licenças.")
    else:
        apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
        
        # Exibição em cards
        cores = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
        cols = st.columns(4)
        for i, apoiador in enumerate(apoiadores_ordenados):
            with cols[i % 4]:
                cor = cores[i % len(cores)]
                nome = apoiador.get("nome", "Apoiador")
                ordem = apoiador.get("ordem", 999)
                with st.container(border=True):
                    st.markdown(f"**{nome}** (#{ordem})")
                    st.caption(f"📅 {apoiador.get('data_entrada', '2026-07-01')}")
                    depois = sum(1 for k, d in apoiadores.items() if d.get("ordem", 999) > ordem)
                    if depois > 0:
                        st.success(f"⬇️ R${depois * 5.00:.2f}/mês")

# ============================================================
# NOVA SEÇÃO: TOP 20 GOOGLE
# ============================================================
def render_top_20_marketplace():
    """
    Renderiza uma nova grade exclusiva com os 20 produtos reais de marketplace
    """
    st.markdown("## 🔥 Top 20 Google (Shopping & Trends)")
    st.caption("Dados brutos de alto giro pesquisados diretamente na Shopee Brasil - Julho 2026")
    
    from modules.produtos_dinamicos import obter_produtos_marketplace_v49
    produtos_dict = obter_produtos_marketplace_v49()
    
    produtos_reais = []
    for nome, dados in produtos_dict.items():
        produtos_reais.append({
            "produto": nome,
            "categoria": dados.get("categoria", "Geral"),
            "score": dados.get("score", 0),
            "motivo": dados.get("evento", "Tendência de Mercado")
        })
    
    dados_tabela = []
    for item in produtos_reais:
        dados_palavra = obter_palavra_chave(item["produto"])
        dados_tabela.append({
            "Produto": item["produto"],
            "Categoria": item["categoria"],
            "Score": f"{item['score']}/10",
            "Palavra-chave": dados_palavra.get("palavra", f"{item['produto']}"),
            "Motivo Estratégico": item["motivo"]
        })
    
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True, hide_index=True)
# ============================================================
# GRADES UNIFICADAS COM SUB-ABAS (substitui as grades duplicadas)
# ============================================================
def render_grades_unificadas():
    """
    Renderiza todas as grades do Dashboard em uma única seção com sub-abas.
    Cada aba tem link de busca na Shopee e o botão "Buscar Dados Reais" é restrito ao admin.
    
    Sub-abas:
    - 🎯 Descoberta (grade principal)
    - 🏆 Top 10 Tendências
    - 🔥 Top 20 Google + Shopee
    - 📌 Sugestões Estratégicas
    """
    is_admin = st.session_state.get("is_admin", False)
    
    st.markdown("## 📊 Grades de Produtos")
    
    # Botão "Buscar Dados Reais" — apenas admin
    if is_admin:
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn2:
            if st.button("🔄 Buscar Dados Reais", use_container_width=True, key="btn_buscar_reais_unificado"):
                try:
                    from modules.selenium_client import capturar_buscas_selenium
                    with st.spinner("📡 Acessando marketplaces em tempo real..."):
                        termos = capturar_buscas_selenium()
                        if termos:
                            st.success(f"✅ {len(termos)} termos capturados com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Não foi possível capturar dados em tempo real.")
                except ImportError:
                    st.error("❌ Módulo Selenium indisponível.")
    
    # Sub-abas das grades
    sub_grade1, sub_grade2, sub_grade3, sub_grade4 = st.tabs([
        "🎯 Descoberta",
        "🏆 Top 10 Tendências",
        "🔥 Top 20 Google + Shopee",
        "📌 Sugestões Estratégicas",
    ])
    
    # ---- ABA 1: DESCOBERTA ----
    with sub_grade1:
        render_grade_descoberta(key_suffix="unificado_descoberta")
    
    # ---- ABA 2: TOP 10 TENDÊNCIAS ----
    with sub_grade2:
        st.markdown("### 🏆 Top 10 Produtos em Tendência")
        st.caption("Ranking completo baseado em score e dados de mercado")
        
        top10 = gerar_top10_produtos(forcar_atualizacao=False)
        if top10:
            df_top10 = pd.DataFrame(top10)
            colunas_top10 = [
                "Produto", "Fonte", "Categoria", "Evento",
                "Potencial", "Score", "Pins", "Crescimento",
                "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência",
                "Atualizado",
            ]
            # Filtrar colunas existentes
            colunas_presentes = [c for c in colunas_top10 if c in df_top10.columns]
            df_top10 = df_top10[colunas_presentes]
            
            # Converte Score para numérico
            if "Score" in df_top10.columns:
                df_top10["Score Num"] = (
                    pd.to_numeric(df_top10["Score"], errors="coerce")
                    .fillna(0)
                    .clip(lower=0, upper=10)
                )
            
            # Extrai crescimento numérico
            if "Crescimento" in df_top10.columns:
                df_top10["Cresc. %"] = (
                    df_top10["Crescimento"]
                    .str.replace("+", "", regex=False)
                    .str.replace("%", "", regex=False)
                    .pipe(pd.to_numeric, errors="coerce")
                    .fillna(0)
                )
            
            st.dataframe(
                df_top10,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Produto": st.column_config.TextColumn("Produto", width="medium"),
                    "Fonte": st.column_config.TextColumn("Fonte", width="small"),
                    "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                    "Evento": st.column_config.TextColumn("Evento", width="medium"),
                    "Potencial": st.column_config.TextColumn("Potencial", width="small"),
                    "Score": st.column_config.TextColumn("Score", width="small"),
                    "Score Num": st.column_config.ProgressColumn(
                        "⭐ Score",
                        min_value=0,
                        max_value=10,
                        format="%d/10",
                        width="small",
                    ),
                    "Pins": st.column_config.TextColumn("Pins", width="small"),
                    "Crescimento": st.column_config.TextColumn("Crescimento", width="small"),
                    "Cresc. %": st.column_config.ProgressColumn(
                        "📈 Crescimento",
                        min_value=0,
                        max_value=200,
                        format="+%d%%",
                        width="small",
                    ),
                    "Views TikTok": st.column_config.TextColumn("Views TikTok", width="small"),
                    "Buscas no Mês": st.column_config.TextColumn("Buscas/Mês", width="small"),
                    "Resultados ML": st.column_config.TextColumn("Resultados ML", width="small"),
                    "Tendência": st.column_config.TextColumn("Tendência", width="small"),
                    "Atualizado": st.column_config.TextColumn("Atualizado", width="small"),
                },
            )
        else:
            st.info("📊 Aguardando dados de tendências...")
    
    # ---- ABA 3: TOP 20 GOOGLE + SHOPEE ----
    with sub_grade3:
        st.markdown("### 🔥 Top 20 Google Trends & Shopee")
        st.caption("Dados reais capturados do Google Trends e Shopee Brasil — atualização automática a cada 6 horas")
        
        # Status do cache
        try:
            from modules.google_shopee_trends import obter_status_cache, forcar_atualizacao_completa
            status_cache = obter_status_cache()
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                g_status = status_cache.get("google_trends", {})
                icone_g = "✅" if g_status.get("valido") else "⚠️"
                st.metric(f"{icone_g} Google Trends", f"{g_status.get('total', 0)} itens",
                          delta=g_status.get("data_formatada", "N/A"))
            with col_s2:
                s_status = status_cache.get("shopee", {})
                icone_s = "✅" if s_status.get("valido") else "⚠️"
                st.metric(f"{icone_s} Shopee", f"{s_status.get('total', 0)} itens",
                          delta=s_status.get("data_formatada", "N/A"))
            with col_s3:
                # Botão de update — apenas admin
                if is_admin:
                    if st.button("🔄 Atualizar Dados Agora", use_container_width=True, key="btn_atualizar_top20_unificado"):
                        with st.spinner("📡 Buscando dados reais..."):
                            resultado = forcar_atualizacao_completa()
                            st.success(
                                f"✅ Google: {resultado.get('google_trends', {}).get('total', 0)} itens | "
                                f"Shopee: {resultado.get('shopee', {}).get('total', 0)} itens | "
                                f"Tempo: {resultado.get('tempo_total', 0)}s"
                            )
                            st.rerun()
                else:
                    st.empty()
        except Exception:
            pass
        
        st.markdown("---")
        
        # Tabela Top 20 com link Shopee
        _render_top20_com_shopee()
    
    # ---- ABA 4: SUGESTÕES ESTRATÉGICAS ----
    with sub_grade4:
        st.markdown("### 📌 Sugestões de Produtos Estratégicos")
        st.caption("Produtos com alto potencial de conversão baseados em tendências reais")
        
        # Grade de sugestões (com key_suffix diferente para evitar conflito)
        render_grade_descoberta(key_suffix="unificado_sugestoes")


def _render_top20_com_shopee():
    """
    Renderiza o Top 20 Marketplace com link de busca na Shopee para cada produto.
    """
    from modules.produtos_dinamicos import obter_produtos_marketplace_v49
    produtos_dict = obter_produtos_marketplace_v49()
    
    dados_tabela = []
    for nome, dados in produtos_dict.items():
        dados_palavra = obter_palavra_chave(nome)
        link_shopee = f"https://shopee.com.br/search?keyword={quote(nome)}"
        dados_tabela.append({
            "Produto": nome,
            "Link Shopee": link_shopee,
            "Categoria": dados.get("categoria", "Geral"),
            "Score": f"{dados.get('score', 0)}/10",
            "Palavra-chave": dados_palavra.get("palavra", nome),
            "Motivo Estratégico": dados.get("evento", "Tendência de Mercado"),
        })
    
    df = pd.DataFrame(dados_tabela)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Produto": st.column_config.TextColumn("Produto", width="medium"),
            "Link Shopee": st.column_config.LinkColumn(
                "🛒 Shopee",
                help="Buscar produto na Shopee",
                validate="^https://shopee\\.com\\.br/.*",
                display_text="Buscar",
                width="small",
            ),
            "Categoria": st.column_config.TextColumn("Categoria", width="small"),
            "Score": st.column_config.TextColumn("Score", width="small"),
            "Palavra-chave": st.column_config.TextColumn("Palavra-chave", width="large"),
            "Motivo Estratégico": st.column_config.TextColumn("Motivo", width="large"),
        },
    )
    st.caption(f"📊 {len(dados_tabela)} produtos")
