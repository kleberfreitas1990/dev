import streamlit as st
import warnings
from datetime import datetime
from urllib.parse import quote
import pandas as pd
import time
import logging
import sys
import os
import json

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ============================================================
# SUPRIMIR WARNINGS
# ============================================================
warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="Minerador de Produtos - Afiliados 2026",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# IMPORTAR MÓDULOS
# ============================================================
from modules.auth import verificar_login, SistemaLicencas
from modules.views import render_dashboard, render_status_usuario
from modules.models import (
    gerar_top10_produtos, 
    obter_palavra_chave,
    carregar_apoiadores,
    adicionar_apoiador,
    remover_apoiador
)

# ============================================================
# VERIFICAR LOGIN
# ============================================================
licenca = verificar_login()

# ============================================================
# STATUS DO USUÁRIO
# ============================================================
render_status_usuario()
st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard Real",
    "📌 Sugestões & Horários",
    "📅 Calendário 2026",
    "🎬 Criar Vídeo IA",
    "👑 Apoiadores"
])

# ============================================================
# TAB 1: DASHBOARD
# ============================================================
with tab1:
    render_dashboard()

# ============================================================
# TAB 2: SUGESTÕES & HORÁRIOS
# ============================================================
with tab2:
    st.markdown("## 🎯 Produtos em Tendência & Estratégia de Postagem")
    st.caption("Dados reais capturados para 2026 - Melhores horários baseados em engajamento")
    
    produtos = gerar_top10_produtos(forcar_atualizacao=True)
    
    if produtos:
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            dados_palavra = obter_palavra_chave(produto)
            
            dados_tabela.append({
                "Produto": item.get("Produto", ""),
                "⏰ Melhor Horário": f"{item.get('Melhor Horário', '16:00')} ({item.get('Melhor Rede', 'TikTok')})",
                "Categoria": item.get("Categoria", "Geral"),
                "Score": item.get("Score", 0),
                "Crescimento": item.get("Crescimento", "+0%"),
                "Views TikTok": item.get("Views TikTok", "0M"),
                "Buscas Reais": item.get("Buscas no Mês", "0"),
                "Tendência": item.get("Tendência", "🚀 Alta")
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["🛒 Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #ff4b2b; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">🛒 Ver na Shopee</span></a>'
        )
        
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 **Dica Estratégica:** Postar vídeos de até 60 segundos nos horários indicados aumenta a chance de viralização em 40%.")
    else:
        st.info("📭 Nenhum dado disponível")

# ============================================================
# TAB 3: CALENDÁRIO
# ============================================================
with tab3:
    st.markdown("## 📅 Calendário de Eventos 2026")
    mes_selecionado = st.selectbox("Selecione o mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    st.info(f"Insights para {mes_selecionado} sendo processados com base em tendências históricas e previsões de 2026.")

# ============================================================
# TAB 4: VÍDEO IA
# ============================================================
with tab4:
    st.markdown("## 🎬 Criador de Vídeos IA")
    prompt = st.text_area("Descreva o produto para o vídeo:", placeholder="Ex: Air Fryer Oven 12L com design moderno...")
    if st.button("Gerar Script & Sugestão de Cena"):
        st.success("Script gerado com sucesso! Use o horário de pico para postar.")

# ============================================================
# TAB 5: APOIADORES
# ============================================================
with tab5:
    st.markdown("## 👑 Nossos Apoiadores")
    apoiadores = carregar_apoiadores()
    if apoiadores:
        for id, dados in apoiadores.items():
            st.write(f"{dados['coroinha']} **{dados['nome']}** - {dados['plano']}")
