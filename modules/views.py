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
# APOIADORES EM CARDS PEQUENOS (RESTAURADO)
# ============================================================
def render_apoiadores_compactos():
    """Renderiza os apoiadores em cards pequenos com coroa centralizada"""
    apoiadores = carregar_apoiadores()
    if not apoiadores:
        return
    
    st.markdown("### 👑 Apoiadores do Projeto")
    apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
    cores = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE"]
    
    cols = st.columns(6)
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 6]:
            cor = cores[i % len(cores)]
            nome = apoiador.get("nome", "Apoiador")
            coroinha = apoiador.get("coroinha", "👑")
            
            with st.container(border=True):
                st.markdown(f'<div style="text-align: center; font-size: 24px;">{coroinha}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center; font-weight: bold; font-size: 12px;">{nome}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background: {cor}; height: 3px; border-radius: 2px; margin-top: 4px;"></div>', unsafe_allow_html=True)

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
    produtos = descobrir_produtos_grade(quantidade=10)
    if produtos:
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
# INSIGHTS ESTRATÉGICOS
# ============================================================
def render_insights_estrategicos(produtos_lista):
    """Renderiza insights estratégicos com hashtags inteligentes"""
    st.markdown("## 💡 Insights Estratégicos")
    if not produtos_lista: return

    top3 = produtos_lista[:3]
    insights_data = []
    for item in top3:
        produto_nome = item.get("Produto", "N/A")
        categoria = item.get("Categoria", "Geral")
        horario_info = obter_melhor_horario_postagem(categoria)
        
        # Hashtags Inteligentes
        palavras = produto_nome.lower().split()
        hashtags_especificas = [f"#{p}" for p in palavras if len(p) > 2]
        hashtags_finais = (hashtags_especificas[:2] + ["#achadinhos", "#shopeebr"])[:4]
        
        insights_data.append({
            "Produto": produto_nome,
            "⏰ Melhor Horário": f"{horario_info['horario']} ({horario_info['rede']})",
            "#️⃣ Hashtags": " ".join(hashtags_finais),
            "💡 Dica": f"Foque em vídeos rápidos de unboxing ou demonstração."
        })
    st.table(pd.DataFrame(insights_data))

# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
def render_dashboard():
    """Renderiza o dashboard principal restaurado"""
    # Apoiadores no TOPO
    render_apoiadores_compactos()
    st.markdown("---")
    
    st.title("📊 Minerador de Produtos")
    
    produtos_lista = gerar_top10_produtos(forcar_atualizacao=False)
    if produtos_lista:
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("🔥 Top Produto", produtos_lista[0].get("Produto"))
        with col2: st.metric("📈 Crescimento", "+45%")
        with col3: st.metric("📱 Rede", "TikTok")
            
        st.markdown("### 🏆 Top 10 Produtos em Tendência")
        df_top10 = pd.DataFrame(produtos_lista)
        colunas = ["Produto", "Categoria", "Score", "Pins", "Crescimento", "Views TikTok", "Tendência"]
        st.dataframe(df_top10[colunas], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        render_insights_estrategicos(produtos_lista)
        st.markdown("---")
        render_grade_descoberta()

def render_painel_apoiadores_detalhado():
    """Painel detalhado para aba de apoiadores"""
    st.markdown("## 👑 Comunidade de Apoiadores")
    render_apoiadores_compactos()

__all__ = ['render_dashboard', 'render_status_usuario', 'render_painel_apoiadores_detalhado', 'render_grade_descoberta']
