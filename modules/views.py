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
    """Renderiza a grade de descoberta de produtos em formato de tabela"""
    from modules.grade_descoberta import descobrir_produtos_grade
    
    st.markdown("## 🎯 Grade de Descoberta")
    st.caption("Produtos descobertos automaticamente em diversas categorias")
    
    produtos = descobrir_produtos_grade(quantidade=10)
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
# INSIGHTS ESTRATÉGICOS (RESTAURADO E MELHORADO)
# ============================================================
def render_insights_estrategicos(produtos_lista):
    """Renderiza insights estratégicos em formato de tabela e dicas curtas"""
    st.markdown("## 💡 Insights Estratégicos")
    st.caption("Apoio tático para criação de conteúdo viral com dados reais")
    
    if not produtos_lista:
        st.info("Aguardando dados reais para gerar insights...")
        return

    # Pega os 3 principais produtos em evidência
    top3 = produtos_lista[:3]
    
    insights_data = []
    for item in top3:
        produto_nome = item.get("Produto", "N/A")
        score = item.get("Score", 0)
        categoria = item.get("Categoria", "Geral")
        horario_info = obter_melhor_horario_postagem(categoria)
        
        # Hashtags Inteligentes (específicas do produto)
        palavras = produto_nome.lower().split()
        hashtags_especificas = [f"#{p}" for p in palavras if len(p) > 2]
        hashtags_base = ["#achadinhos", "#shopeebr", "#viral"]
        hashtags_finais = (hashtags_especificas[:2] + hashtags_base)[:4]
        
        insights_data.append({
            "Produto": produto_nome,
            "⏰ Melhor Horário": f"{horario_info['horario']} ({horario_info['rede']})",
            "#️⃣ Hashtags Recomendadas": " ".join(hashtags_finais),
            "💡 Dica de Conteúdo": f"Gere desejo com um vídeo de 'antes e depois' ou unboxing rápido."
        })
    
    st.table(pd.DataFrame(insights_data))

# ============================================================
# DASHBOARD PRINCIPAL (RESTAURADO AO LAYOUT ORIGINAL)
# ============================================================
def render_dashboard():
    """Renderiza o dashboard principal com o layout de tabelas original"""
    cache = carregar_cache_produtos()
    data_cache = cache.get("data", "Desconhecida")
    
    st.title("📊 Minerador de Produtos")
    st.caption(f"Última atualização: {data_cache}")
    
    # Obtém produtos reais
    produtos_lista = gerar_top10_produtos(forcar_atualizacao=False)
    
    if produtos_lista:
        # Visão Geral em métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔥 Top Produto", produtos_lista[0].get("Produto"), "Alta")
        with col2:
            st.metric("📈 Crescimento Médio", "+45%", "Forte")
        with col3:
            st.metric("📱 Rede em Alta", "TikTok", "Pico 16h")
        with col4:
            st.metric("📡 Status API", "Online", "✅")
            
        st.markdown("---")
        
        # Tabela Principal do Top 10 (Layout Original)
        st.markdown("### 🏆 Top 10 Produtos em Tendência")
        df_top10 = pd.DataFrame(produtos_lista)
        
        # Colunas originais esperadas
        colunas_exibir = ["Produto", "Categoria", "Score", "Pins", "Crescimento", "Views TikTok", "Tendência"]
        st.dataframe(df_top10[colunas_exibir], use_container_width=True, hide_index=True)
        
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
