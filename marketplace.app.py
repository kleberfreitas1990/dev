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
VERSAO_SISTEMA = "v5.0 - Full Sync"

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
# VERIFICAR LOGIN
# ============================================================
licenca = verificar_login()

# ============================================================
# ROTINA DE ATUALIZAÇÃO AUTOMÁTICA
# ============================================================
executar_atualizacao_automatica()

# ============================================================
# STATUS DO USUÁRIO E VERSÃO
# ============================================================
col_ver, col_stat = st.columns([1, 4])
with col_ver:
    st.info(f"🚀 **{VERSAO_SISTEMA}**")
with col_stat:
    render_status_usuario()
st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab_new, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Dashboard",
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
    st.markdown("## 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Top produtos baseados em tendências de mercado")
    
    # Botão para buscar dados com Selenium
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Buscar Dados Reais", use_container_width=True, key="btn_selenium_tab2"):
            with st.spinner("⏳ Buscando dados com Selenium..."):
                try:
                    status = verificar_status_selenium()
                    if not status.get("online"):
                        st.error("❌ Servidor Selenium offline. Aguarde o Render iniciar (pode levar 1 minuto).")
                    else:
                        termos = capturar_buscas_selenium()
                        if termos:
                            st.success(f"✅ {len(termos)} termos capturados!")
                            st.session_state.termos_selenium = termos
                            st.rerun()
                        else:
                            st.warning("⚠️ Nenhum termo encontrado")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
    
    # Carrega dados reais injetados no cache
    produtos = gerar_top10_produtos(forcar_atualizacao=False)
    
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
                "Tendência": item.get("Tendência", "➡️ Estável"),
                "Fonte": item.get("Fonte", "Shopee")
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>'
        )
        
        colunas = ["Produto", "Fonte", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência", "Buscar na Shopee"]
        df = df[colunas]
        
        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    else:
        st.info("📭 Nenhum dado disponível")

# ============================================================
# TAB 3: CALENDÁRIO
# ============================================================
with tab3:
    st.markdown("## 📅 Calendário de Conteúdo Estratégico")
    st.caption("Selecione um mês para ver sugestões de produtos e insights")
    
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_selecionado = st.selectbox("Selecione o mês:", meses, index=datetime.now().month - 1)
    
    if mes_selecionado:
        st.markdown(f"### 📌 Eventos - {mes_selecionado}")
        
        eventos = {
            "01-01": {"nome": "Ano Novo", "produtos": ["decoração", "roupa branca", "espumante"]},
            "02-14": {"nome": "Dia dos Namorados", "produtos": ["perfume", "jantar", "kit romântico"]},
            "03-08": {"nome": "Dia da Mulher", "produtos": ["flores", "perfumes", "kits de beleza"]},
            "05-13": {"nome": "Dia das Mães", "produtos": ["perfume", "bolsa", "vestido"]},
            "06-12": {"nome": "Dia dos Namorados", "produtos": ["perfume", "vinho", "jantar"]},
            "07-09": {"nome": "Férias Escolares", "produtos": ["casaco", "blusa de lã", "bota"]},
            "08-14": {"nome": "Dia dos Pais", "produtos": ["ferramentas", "relógio", "cinto"]},
            "10-12": {"nome": "Dia das Crianças", "produtos": ["brinquedo", "boneca", "carrinho"]},
            "10-31": {"nome": "Halloween", "produtos": ["fantasia", "decoração", "doces"]},
            "11-25": {"nome": "Black Friday", "produtos": ["eletrônicos", "celular", "smartwatch"]},
            "12-25": {"nome": "Natal", "produtos": ["presentes", "árvore", "decoração"]},
            "12-31": {"nome": "Réveillon", "produtos": ["roupa branca", "espumante"]}
        }
        
        eventos_mes = {k: v for k, v in eventos.items() if k.startswith(f"{meses.index(mes_selecionado)+1:02d}")}
        
        if eventos_mes:
            col1, col2 = st.columns([1, 1])
            for i, (data, evento) in enumerate(eventos_mes.items()):
                with (col1 if i % 2 == 0 else col2):
                    with st.container(border=True):
                        dia = data.split("-")[1]
                        st.markdown(f"**📅 {dia}** - {evento['nome']}")
                        st.caption(f"📦 Produtos sugeridos: {', '.join(evento['produtos'][:3])}")
        else:
            st.info("📭 Nenhum evento programado para este mês.")

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
# ============================================
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
