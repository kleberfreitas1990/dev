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
from modules.views import render_dashboard, render_status_usuario, render_painel_apoiadores_detalhado
from modules.models import (
    gerar_top10_produtos, 
    gerar_sugestoes_diarias,
    obter_palavra_chave,
    carregar_apoiadores,
    adicionar_apoiador,
    remover_apoiador
)
from modules.selenium_client import capturar_buscas_selenium, verificar_status_selenium

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Dashboard",
    "📌 Sugestões Diárias",
    "📅 Calendário 2026",
    "🎯 Descoberta",
    "🎬 Criar Vídeo IA",
    "👑 Apoiadores",
    "🛠️ Admin",
    "🔍 Diagnóstico",
    "📋 Logs",
    "📈 Resumo Admin"
])

# ============================================================
# TAB 1: DASHBOARD
# ============================================================
with tab1:
    render_dashboard()

# ============================================================
# TAB 2: SUGESTÕES DIÁRIAS
# ============================================================
with tab2:
    st.markdown("## 🎯 Sugestões Diárias de Produtos")
    st.caption("Produtos em tendência para você focar hoje")
    
    with st.spinner("🔍 Buscando sugestões..."):
        sugestoes = gerar_sugestoes_diarias(forcar_atualizacao=False)
    
    if sugestoes:
        for i, item in enumerate(sugestoes):
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"### {i+1}. {item['Produto']}")
                    st.markdown(f"**Score:** {item['Score']}/100 | **Tendência:** {item['Tendência']}")
                    st.markdown(f"**Categoria:** {item['Categoria']}")
                with col2:
                    st.metric("Crescimento", item['Crescimento'])
                    st.metric("Views TikTok", item['Views TikTok'])
                with col3:
                    termo = item['Produto'].lower()
                    url_shopee = f"https://shopee.com.br/search?keyword={quote(termo)}"
                    st.markdown(f'<a href="{url_shopee}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 10px; background-color: #ff4b2b; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">🛒 Ver na Shopee</button></a>', unsafe_allow_html=True)
                    
                    dados_palavra = obter_palavra_chave(termo)
                    palavra_chave = dados_palavra.get("palavra", f"{termo} tendência 2026")
                    url_google = f"https://www.google.com/search?q={quote(palavra_chave)}"
                    st.markdown(f'<a href="{url_google}" target="_blank" style="text-decoration: none; margin-top: 10px;"><button style="width: 100%; padding: 10px; background-color: #4285f4; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">🔍 Ver no Google</button></a>', unsafe_allow_html=True)
            st.markdown("")
    else:
        st.info("📭 Nenhuma sugestão disponível no momento.")

# ============================================================
# TAB 3: CALENDÁRIO
# ============================================================
with tab3:
    st.markdown("## 📅 Calendário de Eventos 2026")
    st.caption("Datas importantes para o mercado de afiliados")
    
    eventos_2026 = {
        "Janeiro": [{"dia": "01", "nome": "Ano Novo"}, {"dia": "06", "nome": "Dia de Reis"}],
        "Fevereiro": [{"dia": "14", "nome": "Valentine's Day (EUA)"}, {"dia": "17", "nome": "Carnaval"}],
        "Março": [{"dia": "08", "nome": "Dia da Mulher"}, {"dia": "15", "nome": "Dia do Consumidor"}],
        "Abril": [{"dia": "05", "nome": "Páscoa"}],
        "Maio": [{"dia": "10", "nome": "Dia das Mães"}],
        "Junho": [{"dia": "12", "nome": "Dia dos Namorados"}],
        "Julho": [{"dia": "20", "nome": "Dia do Amigo"}],
        "Agosto": [{"dia": "09", "nome": "Dia dos Pais"}],
        "Setembro": [{"dia": "15", "nome": "Dia do Cliente"}],
        "Outubro": [{"dia": "12", "nome": "Dia das Crianças"}, {"dia": "31", "nome": "Halloween"}],
        "Novembro": [{"dia": "27", "nome": "Black Friday"}],
        "Dezembro": [{"dia": "25", "nome": "Natal"}]
    }
    
    mes_selecionado = st.selectbox("Selecione o mês:", list(eventos_2026.keys()), index=datetime.now().month - 1)
    
    for evento in eventos_2026[mes_selecionado]:
        dia = evento['dia']
        st.markdown(f"**📅 {dia}** - {evento['nome']}")

# ============================================================
# TAB 4: DESCOBERTA
# ============================================================
with tab4:
    from modules.views import render_grade_descoberta
    render_grade_descoberta()

# ============================================================
# TAB 5: CRIAR VÍDEO IA
# ============================================================
with tab5:
    st.markdown("## 🎬 Criador de Vídeos IA")
    st.caption("Gere scripts e ideias de vídeos para seus produtos")
    
    with st.container(border=True):
        produto_video = st.text_input("Nome do Produto", placeholder="Ex: Air Fryer Oven 12L")
        estilo_video = st.selectbox("Estilo do Vídeo", ["Unboxing", "Review", "Dicas de Uso", "Comparativo"])
        
        if st.button("✨ Gerar Script do Vídeo", use_container_width=True):
            if produto_video:
                with st.spinner("✍️ Escrevendo script..."):
                    time.sleep(2)
                    st.markdown(f"### 📝 Script: {produto_video} ({estilo_video})")
                    st.markdown("""
                    **Cena 1 (0-3s):** Gancho inicial mostrando o produto de forma atraente.
                    **Cena 2 (3-10s):** Mostre o principal benefício do produto.
                    **Cena 3 (10-20s):** Demonstre como usar de forma simples.
                    **Cena 4 (20-30s):** Chamada para ação (CTA) para o link na bio.
                    """)
                    st.info("💡 **Dica:** Use músicas em alta no TikTok para aumentar o alcance!")
            else:
                st.warning("⚠️ Digite o nome do produto primeiro.")

# ============================================================
# TAB 6: APOIADORES
# ============================================================
with tab6:
    render_painel_apoiadores_detalhado()

# ============================================================
# TAB 7: ADMIN
# ============================================================
with tab7:
    if st.session_state.get("is_admin", False):
        st.markdown("## 🛠️ Painel Administrativo")
        
        with st.expander("👑 Gerenciar Apoiadores"):
            render_painel_apoiadores_detalhado()
        
        with st.expander("🔑 Gerenciar Licenças"):
            st.markdown("### Licenças Ativas")
            sistema = SistemaLicencas()
            st.json(sistema.dados["licencas"])
    else:
        st.warning("🔒 Acesso restrito a administradores.")

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
    from modules.logger import render_painel_logs
    render_painel_logs()

# ============================================================
# TAB 10: RESUMO ADMIN
# ============================================================
with tab10:
    if st.session_state.get("is_admin", False):
        from modules.admin_dashboard import render_admin_resumo
        render_admin_resumo()
    else:
        st.warning("🔒 Acesso restrito a administradores.")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v4.0 | {datetime.now().year}")
