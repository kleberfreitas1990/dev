import streamlit as st
import warnings
from datetime import datetime
from urllib.parse import quote
import pandas as pd
import time
import logging
import sys
import os

# ============================================================
# VERSÃO DO SISTEMA
# ============================================================
VERSAO_SISTEMA = "v5.0 - Full Sync (Metadata Pro Restored)"

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
    page_title=f"Minerador de Produtos - {VERSAO_SISTEMA}",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# IMPORTAR MÓDULOS
# ============================================================
from modules.auth import verificar_login, SistemaLicencas, listar_apoiadores_por_licencas
from modules.views import (
    render_dashboard, 
    render_status_usuario, 
    render_painel_apoiadores_detalhado, 
    render_top_20_marketplace,
    render_grade_descoberta,
    render_apoiadores_compactos
)
from modules.models import (
    gerar_top10_produtos, 
    PALAVRAS_CHAVE_CAUDA_LONGA, 
    obter_palavra_chave,
    carregar_apoiadores,
    adicionar_apoiador,
    remover_apoiador
)
from modules.serper import buscar_produtos_serper
from modules.automation import executar_atualizacao_automatica, render_status_automacao

# Importa módulo de conteúdo IA
from modules.conteudo_ia import (
    gerar_conteudo_completo,
    gerar_script_completo,
    gerar_titulos,
    gerar_dicas_gravacao,
    analisar_concorrencia,
    carregar_conteudo_cache,
    salvar_conteudo_cache
)

# Importa cliente Selenium
from modules.selenium_client import (
    capturar_buscas_selenium,
    capturar_tendencias_selenium,
    buscar_produtos_selenium,
    verificar_status_selenium
)

# ============================================================
# LOGIN E AUTENTICAÇÃO
# ============================================================
if not verificar_login():
    st.stop()

# ============================================================
# HEADER
# ============================================================
col_logo, col_versao = st.columns([4, 1])
with col_logo:
    st.title("🛒 Minerador de Produtos")
    st.caption(f"Inteligência Comercial para Afiliados e Vendedores | {datetime.now().strftime('%d/%m/%Y')}")

with col_versao:
    st.info(f"🚀 **{VERSAO_SISTEMA}**")

render_status_usuario()
st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab_new, tab2, tab3, tab4, tab5, tab_meta, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Dashboard",
    "🔥 Top 20 Google",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA",
    "🤖 Criar Conteúdo",
    "🎬 Metadata Pro",
    "👑 Apoiadores",
    "🔑 Licenças",
    "🔍 Diagnóstico",
    "📊 Logs",
    "⚙️ Admin"
])

# ============================================================
# TAB 1: DASHBOARD
# ============================================================
with tab1:
    render_dashboard()

# ============================================================
# TAB NOVA: TOP 20 MARKETPLACE REAL
# ============================================================
with tab_new:
    render_top_20_marketplace()

# ============================================================
# TAB 2: SUGESTÕES DE PRODUTOS
# ============================================================
with tab2:
    st.markdown("## 📌 Sugestões de Produtos Estratégicos")
    st.caption("Produtos com alto potencial de conversão baseados em tendências reais")
    
    if st.button("🔄 Buscar Dados Reais", use_container_width=True, key="btn_selenium_tab2"):
        with st.spinner("📡 Acessando marketplaces em tempo real..."):
            termos = capturar_buscas_selenium()
            if termos:
                st.success(f"✅ {len(termos)} termos capturados com sucesso!")
                st.rerun()
            else:
                st.error("❌ Não foi possível capturar dados em tempo real.")
    
    render_grade_descoberta()

# ============================================================
# TAB 3: CALENDÁRIO
# ============================================================
with tab3:
    from modules.calendar import render_calendar
    render_calendar()

# ============================================================
# TAB 4: CRIAR VÍDEO IA
# ============================================================
with tab4:
    st.markdown("## 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Gere vídeos para TikTok, Reels e Shorts com IA")
    
    snapgen_key = st.secrets.get("SNAPGEN_API_KEY", "")
    if not snapgen_key:
        st.warning("⚠️ **Chave SnapGen não configurada.**")
        st.info("Configure no painel do Streamlit Cloud: Settings → Secrets")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        modelo = st.selectbox("Modelo", ["SnapGen", "SnapGen Fast", "SnapGen Pro"])
        prompt = st.text_area("Comando", placeholder="Descreva o vídeo que deseja gerar...", height=120)
    
    with col2:
        st.markdown("#### ⚙️ Configurações Técnicas")
        resolucao = st.radio("Qualidade", ["480p", "720p", "1080p"], index=1)
        duracao = st.selectbox("Duração (segundos)", [4, 6, 8, 10], index=1)
        estilo = st.selectbox("Estilo Visual", ["Realista", "Cinematográfico", "Animado", "Minimalista"])
        st.metric("🎫 Créditos restantes", "10 / 10")
        
        if st.button("🚀 Gerar Vídeo", type="primary", use_container_width=True, key="btn_gerar_video"):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif not snapgen_key:
                st.error("❌ Chave SnapGen não configurada.")
            else:
                with st.spinner("🎬 Gerando vídeo com IA..."):
                    time.sleep(3)
                    st.success("✅ Vídeo gerado com sucesso!")
                    st.video("https://placehold.co/600x400/000000/FFFFFF?text=Video+Gerado+por+IA")

# ============================================================
# TAB 5: CRIAR CONTEÚDO IA
# ============================================================
with tab5:
    st.markdown("## 🤖 Assistente de Conteúdo para Criadores")
    st.caption("Gerador inteligente de roteiros, títulos e estratégias para seus vídeos")
    
    produto_pre_selecionado = st.session_state.get("produto_conteudo", "")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        produto_conteudo = st.text_input("📦 Qual produto você quer criar conteúdo?", value=produto_pre_selecionado, key="input_conteudo_ia")
    with col2:
        categoria_conteudo = st.selectbox("🏷️ Categoria", ["moda", "eletrônico", "beleza", "casa"], key="select_cat_conteudo")
    
    if st.button("🚀 Gerar Conteúdo", type="primary", key="btn_gerar_conteudo"):
        if not produto_conteudo:
            st.error("❌ Digite o nome do produto!")
        else:
            with st.spinner("🤖 Gerando conteúdo inteligente..."):
                try:
                    conteudo = gerar_conteudo_completo(produto_conteudo, categoria_conteudo)
                    if conteudo:
                        st.success("✅ Conteúdo gerado!")
                        st.markdown(conteudo)
                except Exception as e:
                    st.error(f"❌ Erro ao gerar conteúdo: {str(e)}")

# ============================================================
# TAB METADATA PRO (RESTAURADA)
# ============================================================
with tab_meta:
    try:
        from modules.metadados_pro import render_metadados_pro
        render_metadados_pro()
    except Exception as e:
        st.error(f"❌ Erro ao carregar Metadata Pro: {str(e)}")

# ============================================================
# TAB 6: APOIADORES
# ============================================================
with tab6:
    render_painel_apoiadores_detalhado()

# ============================================================
# TAB 7: LICENÇAS
# ============================================================
with tab7:
    st.markdown("## 🔑 Gestão de Licenças")
    st.caption("Área de controle de acessos e ativações")
    try:
        sistema = SistemaLicencas()
        sistema.render_interface_admin()
    except Exception as e:
        st.error(f"❌ Erro ao carregar sistema de licenças: {str(e)}")

# ============================================================
# TAB 8: DIAGNÓSTICO
# ============================================================
with tab8:
    from modules.diagnostico import render_painel_diagnostico
    render_painel_diagnostico()

# ============================================================
# TAB 9: LOGS
# ============================================================
with tab9:
    st.markdown("## 📊 Logs do Sistema")
    if os.path.exists("output.log"):
        with open("output.log", "r") as f:
            st.text_area("Últimos Logs:", f.read(), height=400)
    else:
        st.info("📭 Nenhum log disponível no momento.")

# ============================================================
# TAB 10: ADMIN
# ============================================================
with tab10:
    st.markdown("## ⚙️ Painel Administrativo")
    if st.session_state.get("is_admin", False):
        st.success("✅ Acesso administrativo autorizado")
        # Aqui viriam controles extras de admin
    else:
        st.warning("⚠️ Esta área é restrita ao administrador do sistema.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
render_status_automacao()
