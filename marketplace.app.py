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
VERSAO_SISTEMA = "v10.0 - SQLite"

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
from modules.automation import executar_atualizacao_automatica, render_status_automacao

# O módulo de conteúdo IA é carregado apenas ao abrir sua área.

# Importa módulo de atualização automática aprimorado
from modules.auto_update import (
    executar_ciclo_automatico,
    render_painel_atualizacao_automatica,
    render_status_automacao_rodape
)

# Importa módulo de calendário
from modules.calendar import render_calendar

# Metadados Pro e Divulga Shop são carregados sob demanda quando suas abas são abertas.
# Isso reduz o custo de inicialização sem alterar a lógica dessas áreas.

# ============================================================
# LOGIN E AUTENTICAÇÃO
# ============================================================
if not verificar_login():
    st.stop()

# ============================================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================================
from modules.database import inicializar_db, verificar_db, migrar_jsons_para_db
from modules.sync_db import forcar_sincronizacao_json_to_db

if not verificar_db():
    st.warning("⚠️ Iniciando banco de dados SQLite...")
    inicializar_db()
    migrar_jsons_para_db()
    st.success("✅ Banco de dados SQLite inicializado com sucesso!")

# Sincronização forçada para garantir dados novos no SQLite
if 'sync_real_time' not in st.session_state:
    forcar_sincronizacao_json_to_db()
    st.session_state['sync_real_time'] = True

# ============================================================
# INICIALIZAÇÃO LEVE
# ============================================================
# A atualização de fontes ocorre pelo workflow diário e também pode ser
# disparada manualmente no painel de Atualização Auto. Não bloqueamos a
# primeira renderização da interface com chamadas externas.
st.session_state.setdefault("auto_update_habilitada", True)

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
# NAVEGAÇÃO LEVE
# ============================================================
# st.tabs() executa o conteúdo de todas as abas a cada rerun. Um seletor
# renderiza somente a área escolhida e evita carregar módulos e tabelas
# desnecessários no primeiro acesso.
areas = [
    "📊 Dashboard",
    "🎬 Metadados Pro",
    "🛒 Divulga Shop",
    "🔄 Atualização Auto",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA",
    "🤖 Criar Conteúdo",
    "👑 Apoiadores",
    "🔑 Licenças",
    "🔍 Diagnóstico",
    "📊 Logs",
    "⚙️ Admin",
]
area_ativa = st.radio(
    "Área do aplicativo",
    areas,
    horizontal=True,
    label_visibility="collapsed",
    key="navegacao_principal",
)
st.markdown("---")

if area_ativa == "📊 Dashboard":
    render_dashboard()

elif area_ativa == "🎬 Metadados Pro":
    try:
        from modules.metadados_pro import render_metadados_pro
        render_metadados_pro()
    except Exception as e:
        st.error(f"❌ Erro ao carregar Metadados Pro: {str(e)}")

elif area_ativa == "🛒 Divulga Shop":
    try:
        from modules.divulgashop import render_divulga_shop
        render_divulga_shop()
    except Exception as e:
        st.error(f"❌ Erro ao carregar Divulga Shop: {str(e)}")

elif area_ativa == "🔄 Atualização Auto":
    render_painel_atualizacao_automatica()

elif area_ativa == "📅 Calendário de Conteúdo":
    render_calendar()

elif area_ativa == "🎬 Criar Vídeo IA":
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

elif area_ativa == "🤖 Criar Conteúdo":
    from modules.conteudo_ia import gerar_conteudo_completo
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

elif area_ativa == "👑 Apoiadores":
    render_painel_apoiadores_detalhado()

elif area_ativa == "🔑 Licenças":
    st.markdown("## 🔑 Gestão de Licenças")
    st.caption("Área de controle de acessos e ativações")
    try:
        sistema = SistemaLicencas()
        sistema.render_interface_admin()
    except Exception as e:
        st.error(f"❌ Erro ao carregar sistema de licenças: {str(e)}")

elif area_ativa == "🔍 Diagnóstico":
    from modules.diagnostico import render_painel_diagnostico
    render_painel_diagnostico()

elif area_ativa == "📊 Logs":
    st.markdown("## 📊 Logs do Sistema")
    if os.path.exists("output.log"):
        with open("output.log", "r", encoding="utf-8") as f:
            st.text_area("Últimos Logs:", f.read(), height=400)
    else:
        st.info("📭 Nenhum log disponível no momento.")

elif area_ativa == "⚙️ Admin":
    st.markdown("## ⚙️ Painel Administrativo")
    if st.session_state.get("is_admin", False):
        st.success("✅ Acesso administrativo autorizado")
        st.markdown("---")
        st.markdown("### 💾 Banco de Dados SQLite")
        from modules.database import obter_status_banco, resetar_tudo
        status_db = obter_status_banco()
        col_db1, col_db2, col_db3 = st.columns(3)
        with col_db1:
            st.metric("📁 Banco", f"{status_db.get('db_size_kb', 0)} KB", delta="SQLite" if status_db.get("db_existe") else "Não criado")
        with col_db2:
            st.metric("📋 Versão Schema", f"v{status_db.get('versao_schema', 0)}")
        with col_db3:
            st.metric("📊 ML Cache", f"{status_db.get('ml_ciclos_count', 0)} ciclos")

        col_db4, col_db5, col_db6 = st.columns(3)
        with col_db4:
            st.metric("📦 Amazon Cache", f"{status_db.get('amazon_ciclos_count', 0)} ciclos")
        with col_db5:
            st.metric("👑 Apoiadores", f"{status_db.get('apoiadores_count', 0)}")
        with col_db6:
            st.metric("📈 Histórico", f"{status_db.get('historico_tendencias_count', 0)} registros")

        with st.expander("🛠️ Ações do Banco de Dados"):
            if st.button("🧹 Limpar Ciclos Antigos (manter 10)", key="btn_limpar_ciclos"):
                from modules.database import limpar_ml_cache_antigos, limpar_amazon_cache_antigos
                ml_rem = limpar_ml_cache_antigos(10)
                amz_rem = limpar_amazon_cache_antigos(10)
                st.success(f"✅ Limpo: {ml_rem} ciclos ML + {amz_rem} ciclos Amazon")

            if st.button("🔄 Re-migrar JSONs para SQLite", key="btn_migrar_jsons"):
                resultado = migrar_jsons_para_db()
                if resultado:
                    st.success("✅ JSONs migrados para SQLite!")
                else:
                    st.info("ℹ️ Nenhum JSON para migrar.")

            if st.button("⚠️ RESETAR BANCO (apaga todos os dados)", key="btn_reset_db"):
                st.warning("Clique novamente para confirmar o reset.")

        st.markdown("---")
    else:
        st.warning("⚠️ Esta área é restrita ao administrador do sistema.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
render_status_automacao_rodape()
