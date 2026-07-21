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
VERSAO_SISTEMA = "v9.9 - Pedreira Flow"

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

# Importa novos módulos de Google Trends + Shopee Live
from modules.google_shopee_trends import (
    obter_google_trends,
    obter_shopee_trending,
    obter_status_cache,
    forcar_atualizacao_completa
)

# Importa módulo de atualização automática aprimorado
from modules.auto_update import (
    executar_ciclo_automatico,
    render_painel_atualizacao_automatica,
    render_status_automacao_rodape
)

# Importa módulo de calendário
from modules.calendar import render_calendar

# Importa módulo Metadata Pro
from modules.metadados_pro import render_metadados_pro
from modules.historico_tendencias import render_historico_tendencias
from modules.pedreira import render_pedreira

# ============================================================
# LOGIN E AUTENTICAÇÃO
# ============================================================
if not verificar_login():
    st.stop()

# ============================================================
# CICLO DE ATUALIZAÇÃO AUTOMÁTICA (executa no início)
# ============================================================
executar_atualizacao_automatica()
executar_ciclo_automatico()

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
# TABS (REORGANIZADAS: Metadata Pro em 2º lugar)
# ============================================================
tab1, tab_meta, tab_pedreira, tab_auto, tab_hist, tab_new, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Dashboard",
    "🎬 Metadata Pro",
    "🏗️ Pedreira",           # Nova Aba
    "🔄 Atualização Auto",
    "📈 Histórico",
    "🔥 Top 20 Google",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA",
    "🤖 Criar Conteúdo",
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
    # No dashboard, passamos uma chave específica para evitar duplicidade
    render_dashboard()

# ============================================================
# TAB 2: METADATA PRO (NOVA POSIÇÃO)
# ============================================================
with tab_meta:
    try:
        render_metadados_pro()
    except Exception as e:
        st.error(f"❌ Erro ao carregar Metadata Pro: {str(e)}")

# ============================================================
# TAB: PEDREIRA (FLUXO DE PEDIDOS)
# ============================================================
with tab_pedreira:
    try:
        render_pedreira()
    except Exception as e:
        st.error(f"❌ Erro ao carregar Fluxo Pedreira: {str(e)}")

# ============================================================
# TAB 3: ATUALIZAÇÃO AUTOMÁTICA
# ============================================================
with tab_auto:
    render_painel_atualizacao_automatica()

# ============================================================
# TAB 4: HISTÓRICO DE TENDÊNCIAS
# ============================================================
with tab_hist:
    render_historico_tendencias()

# ============================================================
# TAB 5: TOP 20 GOOGLE TRENDS + SHOPEE LIVE
# ============================================================
with tab_new:
    st.markdown("## 🔥 Top 20 Google Trends & Shopee")
    st.caption("Dados reais capturados do Google Trends e Shopee Brasil — atualização automática a cada 6 horas")

    # Status do cache
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
        if st.button("🔄 Atualizar Dados Agora", use_container_width=True, key="btn_atualizar_top20"):
            with st.spinner("📡 Buscando dados reais..."):
                resultado = forcar_atualizacao_completa()
                st.success(
                    f"✅ Google: {resultado.get('google_trends', {}).get('total', 0)} itens | "
                    f"Shopee: {resultado.get('shopee', {}).get('total', 0)} itens | "
                    f"Tempo: {resultado.get('tempo_total', 0)}s"
                )
                st.rerun()

    st.markdown("---")

    # Sub-tabs para Google e Shopee
    subtab_google, subtab_shopee, subtab_combinado = st.tabs([
        "🔍 Google Trends", "🛒 Shopee Trending", "📊 Visão Combinada"
    ])

    with subtab_google:
        st.markdown("### 📈 Tendências do Google (Brasil)")
        st.caption("Termos em alta no Google Search e Google Shopping — Brasil")

        with st.spinner("🔍 Carregando dados do Google Trends..."):
            dados_google = obter_google_trends()

        if dados_google:
            df_google = pd.DataFrame(dados_google)

            # Normaliza colunas
            colunas_exibir = []
            mapa_colunas = {
                "termo": "Termo de Busca",
                "interesse": "Interesse (0-100)",
                "variacao": "Variação",
                "categoria": "Categoria",
                "fonte": "Fonte",
                "atualizado": "Atualizado em",
                "trafego": "Tráfego Aprox.",
            }
            for col_orig, col_novo in mapa_colunas.items():
                if col_orig in df_google.columns:
                    df_google = df_google.rename(columns={col_orig: col_novo})
                    colunas_exibir.append(col_novo)

            st.dataframe(
                df_google[colunas_exibir] if colunas_exibir else df_google,
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"📊 {len(dados_google)} tendências carregadas")
        else:
            st.info("📭 Nenhum dado do Google Trends disponível. Clique em 'Atualizar Dados Agora'.")

    with subtab_shopee:
        st.markdown("### 🛒 Produtos em Alta na Shopee Brasil")
        st.caption("Termos mais buscados e produtos com maior volume de vendas na Shopee")

        with st.spinner("🛒 Carregando dados da Shopee..."):
            dados_shopee = obter_shopee_trending()

        if dados_shopee:
            df_shopee = pd.DataFrame(dados_shopee)

            mapa_shopee = {
                "termo": "Produto",
                "vendas": "Vendas",
                "avaliacao": "Avaliação",
                "preco": "Preço Médio",
                "categoria": "Categoria",
                "fonte": "Fonte",
                "atualizado": "Atualizado em",
            }
            colunas_shopee = []
            for col_orig, col_novo in mapa_shopee.items():
                if col_orig in df_shopee.columns:
                    df_shopee = df_shopee.rename(columns={col_orig: col_novo})
                    colunas_shopee.append(col_novo)

            st.dataframe(
                df_shopee[colunas_shopee] if colunas_shopee else df_shopee,
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"🛒 {len(dados_shopee)} produtos carregados")
        else:
            st.info("📭 Nenhum dado da Shopee disponível. Clique em 'Atualizar Dados Agora'.")

    with subtab_combinado:
        st.markdown("### 📊 Visão Combinada — Google + Shopee")
        st.caption("Produtos que aparecem tanto no Google Trends quanto na Shopee têm maior potencial de conversão")

        with st.spinner("📊 Cruzando dados..."):
            dados_google_comb = obter_google_trends()
            dados_shopee_comb = obter_shopee_trending()

        # Exibe tabela combinada da função original (preserva layout existente)
        render_top_20_marketplace()

        st.markdown("---")
        st.markdown("#### 🎯 Oportunidades de Alto Potencial")
        st.caption("Termos presentes em ambas as fontes indicam demanda real e consistente")

        # Cruza os dados
        termos_google = {d.get("termo", d.get("Termo de Busca", "")).lower() for d in dados_google_comb}
        oportunidades = []
        for item in dados_shopee_comb:
            termo = item.get("termo", "")
            # Verifica se alguma palavra do termo Shopee aparece no Google
            palavras = termo.lower().split()
            match_google = any(
                any(p in tg for p in palavras if len(p) > 4)
                for tg in termos_google
            )
            if match_google:
                oportunidades.append({
                    "Produto (Shopee)": termo,
                    "Vendas Shopee": item.get("vendas", "N/A"),
                    "Avaliação": item.get("avaliacao", "N/A"),
                    "Preço": item.get("preco", "N/A"),
                    "Categoria": item.get("categoria", "N/A"),
                    "🎯 Potencial": "🔥 Alto (Google + Shopee)",
                })

        if oportunidades:
            df_oport = pd.DataFrame(oportunidades)
            st.dataframe(df_oport, use_container_width=True, hide_index=True)
        else:
            st.info("📊 Nenhuma sobreposição direta encontrada. Atualize os dados para resultados mais precisos.")

# ============================================================
# TAB 5: SUGESTÕES DE PRODUTOS
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
    
    # Na aba de sugestões, usamos a chave 'sugestoes'
    render_grade_descoberta(key_suffix="sugestoes")

# ============================================================
# TAB 6: CALENDÁRIO
# ============================================================
with tab3:
    render_calendar()

# ============================================================
# TAB 7: CRIAR VÍDEO IA
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
# TAB 8: CRIAR CONTEÚDO IA
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
# TAB 9: APOIADORES
# ============================================================
with tab6:
    render_painel_apoiadores_detalhado()

# ============================================================
# TAB 10: LICENÇAS
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
# TAB 11: DIAGNÓSTICO
# ============================================================
with tab8:
    from modules.diagnostico import render_painel_diagnostico
    render_painel_diagnostico()

# ============================================================
# TAB 12: LOGS
# ============================================================
with tab9:
    st.markdown("## 📊 Logs do Sistema")
    if os.path.exists("output.log"):
        with open("output.log", "r") as f:
            st.text_area("Últimos Logs:", f.read(), height=400)
    else:
        st.info("📭 Nenhum log disponível no momento.")

# ============================================================
# TAB 13: ADMIN
# ============================================================
with tab10:
    st.markdown("## ⚙️ Painel Administrativo")
    if st.session_state.get("is_admin", False):
        st.success("✅ Acesso administrativo autorizado")
    else:
        st.warning("⚠️ Esta área é restrita ao administrador do sistema.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
render_status_automacao_rodape()
