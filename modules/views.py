import streamlit as st
import pandas as pd
import random
from datetime import datetime
from urllib.parse import quote
import json

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

# Importa para verificar data do cache
from modules.produtos_dinamicos import carregar_cache_produtos

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
    st.caption("Produtos em tendência descobertos automaticamente")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        categoria_filtro = st.selectbox(
            "Filtrar por categoria:",
            ["Todas", "moda", "eletrônico", "beleza", "casa", "infantil", "esporte"],
            index=0
        )
    with col2:
        quantidade = st.selectbox("Quantidade:", [5, 10, 15, 20], index=1)
    
    with st.spinner("🔍 Descobrindo produtos..."):
        categoria = None if categoria_filtro == "Todas" else categoria_filtro
        produtos_descobrir = descobrir_produtos_grade(categoria=categoria, quantidade=quantidade)
    
    if not produtos_descobrir:
        st.info("📭 Nenhum produto encontrado na grade de descoberta.")
        return
    
    dados_tabela = []
    for item in produtos_descobrir:
        produto = item.get("produto", "").capitalize()
        score = item.get("score", 0)
        categoria = item.get("categoria", "Geral").capitalize()
        motivo = item.get("motivo", "📊 Produto em tendência no mercado atual")
        
        status = "🔥 Alta" if score >= 8 else "📈 Média" if score >= 6 else "📊 Baixa"
        
        dados_palavra = obter_palavra_chave(produto)
        palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
        
        dados_tabela.append({
            "Produto": produto,
            "Categoria": categoria,
            "Score": f"{score}/10",
            "Status": status,
            "Palavra-chave": palavra_chave,
            "Motivo": motivo[:80] + "..."
        })
    
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True, hide_index=True)

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
    cores = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE"]
    
    cols = st.columns(6)
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 6]:
            cor = cores[i % len(cores)]
            nome = apoiador.get("nome", "Apoiador")
            ordem = apoiador.get("ordem", 999)
            coroinha = apoiador.get("coroinha", "👑")
            
            with st.container(border=True):
                st.markdown(f'<div style="text-align: center; font-size: 28px; margin: -8px 0 2px 0;">{coroinha}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center; font-weight: bold; font-size: 13px; margin: 0;">{nome}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center; font-size: 10px; color: #888; margin: 0;">#{ordem}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background: {cor}; height: 3px; border-radius: 2px; margin: 4px 0 2px 0;"></div>', unsafe_allow_html=True)

# ============================================================
# INSIGHTS ESTRATÉGICOS
# ============================================================
def render_insights_estrategicos(produtos_input):
    """Renderiza insights estratégicos"""
    st.markdown("## 💡 Insights Estratégicos")
    st.caption("Análise de mercado baseada em dados reais")
    
    # Padroniza produtos para lista
    produtos_lista = []
    if isinstance(produtos_input, dict):
        for termo, dados in produtos_input.items():
            item = dados.copy()
            item["_termo"] = termo
            produtos_lista.append(item)
    elif isinstance(produtos_input, list):
        produtos_lista = produtos_input
    
    if not produtos_lista:
        st.info("📭 Nenhum dado disponível para insights.")
        return

    st.markdown("---")
    st.markdown("### 🏆 Top 3 Produtos do Mês")
    
    top3 = sorted(produtos_lista, key=lambda x: x.get("Score", 0), reverse=True)[:3]
    cols = st.columns(3)
    for i, item in enumerate(top3):
        with cols[i]:
            produto_nome = item.get("Produto", item.get("_termo", "N/A"))
            score = item.get("Score", 0)
            cor = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            st.metric(label=f"{['🥇', '🥈', '🥉'][i]} {produto_nome}", value=f"{score}/100", delta=f"{cor} {item.get('Tendencia', '➡️ Estável')}")
    
    dados_top3 = []
    for item in top3:
        p_nome = item.get("Produto", item.get("_termo", "N/A"))
        dados_palavra = obter_palavra_chave(p_nome)
        dados_top3.append({
            "Produto": p_nome, 
            "Score": f"{item.get('Score', 0)}/100", 
            "Tendência": item.get('Tendencia', '➡️ Estável'),
            "Preço Médio": item.get('Preco_Medio', 'N/A'), 
            "Buscas Est.": f"{item.get('Buscas_Estimadas_Mes', 0):,}",
            "Palavra-chave": dados_palavra.get("palavra", p_nome)
        })
    st.dataframe(pd.DataFrame(dados_top3), use_container_width=True, hide_index=True)

# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
def render_dashboard():
    """Renderiza o dashboard principal"""
    cache = carregar_cache_produtos()
    status_cache = {"data": cache.get("data", "Desconhecida")} if cache else {"data": "Sem cache"}
    hoje = datetime.now().date().isoformat()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("🔌 " + ("✅" if st.secrets.get("SERPER_API_KEY") else "❌"))
    with col2:
        st.markdown("🎫 10/10")
    with col3:
        st.markdown(f"👤 {st.session_state.get('licenca_usuario', '')[:8]}...")
    with col4:
        if status_cache['data'] == hoje:
            st.success(f"📅 {status_cache['data']}")
        else:
            st.warning(f"📅 {status_cache['data']}")
    with col5:
        try:
            from modules.serper import obter_stats_serper
            stats = obter_stats_serper()
            st.markdown(f"📡 {stats.get('usadas_hoje', 0)}/{stats.get('limite_diario', 20)}")
        except:
            st.markdown("📡 N/A")
    
    st.markdown("---")
    st.title("📊 Minerador de Produtos")
    st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    st.markdown("## 📊 Visão Geral do Mês")
    
    # Obtém produtos (pode ser dict ou list)
    produtos_dict = gerar_top10_produtos(forcar_atualizacao=True)
    
    # Padroniza para lista
    produtos_lista = []
    if isinstance(produtos_dict, dict):
        for termo, dados in produtos_dict.items():
            item = dados.copy()
            item["_termo"] = termo
            produtos_lista.append(item)
    elif isinstance(produtos_dict, list):
        produtos_lista = produtos_raw = produtos_dict
    
    if produtos_lista:
        top1 = produtos_lista[0]
        score_medio = sum([p.get("Score", 0) for p in produtos_lista]) / len(produtos_lista)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 20px; border-radius: 10px; margin-bottom: 16px; text-align: center;">
            <span style="font-size: 18px; font-weight: bold;">🔥 {top1.get('Produto', 'Produto')} em alta!</span>
            <span style="font-size: 15px; margin-left: 10px;">Com score {top1.get('Score', 0)}/100 e tendência {top1.get('Tendencia', 'Crescente')}.</span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(label="🔥 Produto em Alta", value=top1.get("Produto", "N/A"), delta=top1.get("Categoria", "Geral"))
            with m2:
                st.metric(label="📈 Score Médio", value=f"{score_medio:.1f}", delta="Forte")
            with m3:
                categorias = [p.get("Categoria", "Geral") for p in produtos_lista]
                cat_freq = max(set(categorias), key=categorias.count) if categorias else "Geral"
                st.metric(label="🎯 Categoria em Alta", value=cat_freq)
        
        with col2:
            with st.container(border=True):
                st.markdown("**💡 Dica de Hoje**")
                st.caption(f"Foque em vídeos curtos para o produto {top1.get('Produto', 'em destaque')}. O engajamento está alto!")

        st.markdown("---")
        render_insights_estrategicos(produtos_lista)
        st.markdown("---")
        render_grade_descoberta()
    else:
        st.info("📭 Nenhum dado disponível no momento.")

def render_painel_apoiadores_detalhado():
    """Painel detalhado para aba de apoiadores"""
    st.markdown("## 👑 Comunidade de Apoiadores")
    render_apoiadores_compactos()
    st.markdown("---")
    st.markdown("### 💡 Como se tornar um apoiador?")
    st.write("Apoiadores ajudam a manter o projeto ativo e recebem benefícios exclusivos.")

__all__ = ['render_dashboard', 'render_status_usuario', 'render_painel_apoiadores_detalhado', 'render_grade_descoberta']
