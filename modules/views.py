import streamlit as st
import pandas as pd
import random
from datetime import datetime
from urllib.parse import quote
import json

# Importa do auth.py
from modules.auth import SistemaLicencas
from modules.models import (
    obter_palavra_chave,
    gerar_top10_produtos,
    carregar_apoiadores
)

# Importa para verificar data do cache
from modules.produtos_dinamicos import carregar_cache_produtos, obter_melhor_horario_postagem

# ============================================================
# STATUS DO USUÁRIO
# ============================================================
def render_status_usuario():
    """Renderiza o status do usuário"""
    if 'licenca_usuario' in st.session_state:
        st.sidebar.success(f"Sessão Ativa: {st.session_state['licenca_usuario'][:8]}...")

# ============================================================
# GRADE DE DESCOBERTA
# ============================================================
def render_grade_descoberta():
    """Renderiza a grade de descoberta de produtos"""
    from modules.grade_descoberta import descobrir_produtos_grade
    
    st.markdown("## 🎯 Grade de Descoberta")
    st.caption("Produtos descobertos automaticamente em diversas categorias")
    
    produtos = descobrir_produtos_grade(quantidade=8)
    if not produtos:
        st.info("Buscando novos produtos...")
        return

    dados_tabela = []
    for item in produtos:
        dados_tabela.append({
            "Produto": item.get("produto", "").capitalize(),
            "Categoria": item.get("categoria", "Geral").capitalize(),
            "Score": f"{item.get('score', 0)}/10",
            "Tendência": item.get("tendencia", "🚀 Alta"),
            "Motivo": item.get("motivo", "📊 Em alta")
        })
    
    st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, hide_index=True)

# ============================================================
# INSIGHTS ESTRATÉGICOS DINÂMICOS
# ============================================================
def render_insights_estrategicos(produtos_lista):
    """Renderiza insights estratégicos baseados em produtos reais"""
    st.markdown("## 💡 Insights Estratégicos")
    st.caption("Apoio tático para criação de conteúdo viral")
    
    if not produtos_lista:
        st.info("Aguardando dados reais para gerar insights...")
        return

    # Pega os 3 principais produtos em evidência
    top3 = produtos_lista[:3]
    
    cols = st.columns(3)
    for i, item in enumerate(top3):
        with cols[i]:
            produto_nome = item.get("Produto", "N/A")
            score = item.get("Score", 0)
            categoria = item.get("Categoria", "Geral")
            horario_info = obter_melhor_horario_postagem(categoria)
            
            with st.container(border=True):
                st.markdown(f"### 🔥 {produto_nome}")
                st.markdown(f"**📈 Score:** {score}/100")
                st.markdown(f"**⏰ Postar às:** {horario_info['horario']} ({horario_info['rede']})")
                
                # Hashtags dinâmicas baseadas na categoria
                hashtags = ["#achadinhos", f"#{categoria.lower()}", "#shopeebr", "#tendencia2026", "#viral"]
                st.markdown(f"**#️⃣ Hashtags:** `{' '.join(hashtags[:3])}`")
                
                st.markdown("**💡 Dica:** Foque em um vídeo 'unboxing' ou 'resolvendo um problema' com este produto.")

# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
def render_dashboard():
    """Renderiza o dashboard principal"""
    cache = carregar_cache_produtos()
    data_cache = cache.get("data", "Desconhecida")
    
    st.title("📊 Minerador de Produtos")
    st.caption(f"Última atualização: {data_cache}")
    
    # Obtém produtos reais
    produtos_lista = gerar_top10_produtos(forcar_atualizacao=False)
    
    if produtos_lista:
        # Visão Geral
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Top Produto", produtos_lista[0].get("Produto"), "🔥 Alta")
        with col2:
            st.metric("Melhor Rede", "TikTok", "📱 15h-17h")
        with col3:
            st.metric("Volume de Buscas", "Real-Time", "✅")
            
        st.markdown("---")
        render_insights_estrategicos(produtos_lista)
        st.markdown("---")
        render_grade_descoberta()
    else:
        st.warning("⚠️ Dados reais não carregados. Verifique sua conexão com o servidor Selenium.")

def render_painel_apoiadores_detalhado():
    """Painel detalhado para aba de apoiadores"""
    st.markdown("## 👑 Comunidade de Apoiadores")
    apoiadores = carregar_apoiadores()
    if apoiadores:
        for id, dados in apoiadores.items():
            st.write(f"{dados.get('coroinha', '👑')} **{dados.get('nome', 'Apoiador')}**")

__all__ = ['render_dashboard', 'render_status_usuario', 'render_painel_apoiadores_detalhado', 'render_grade_descoberta']
