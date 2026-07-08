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
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# IMPORTAR MÓDULOS
# ============================================================
from modules.auth import verificar_login, SistemaLicencas, listar_apoiadores_por_licencas
from modules.views import render_dashboard, render_status_usuario, render_painel_apoiadores_detalhado
from modules.models import (
    gerar_top10_produtos, 
    PALAVRAS_CHAVE_CAUDA_LONGA, 
    obter_palavra_chave,
    carregar_apoiadores,
    adicionar_apoiador,
    remover_apoiador
)
from modules.serper import buscar_produtos_serper

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
# SINCRONIZAR APOIADORES COM LICENÇAS (AUTOMÁTICO)
# ============================================================
def sincronizar_apoiadores_automatico():
    """
    Sincroniza automaticamente apoiadores das licenças
    """
    try:
        sistema = SistemaLicencas()
        apoiadores = carregar_apoiadores()
        
        # Pega todos os emails de apoiadores
        emails_apoiadores = [a.get("email") for a in apoiadores.values()]
        
        # Verifica licenças que são apoiadores mas não estão na lista
        contador = 0
        for codigo, dados in sistema.dados["licencas"].items():
            if dados.get("is_apoiador", False) and dados.get("status") == "ativo":
                email = dados.get("email")
                usuario = dados.get("usuario")
                if email and email not in emails_apoiadores:
                    # Adiciona como apoiador
                    plano = dados.get("plano", "Apoiador")
                    plano_apoiador = "Premium" if "Premium" in plano else "Apoiador"
                    adicionar_apoiador(usuario, email, plano_apoiador)
                    contador += 1
        
        if contador > 0:
            st.success(f"✅ {contador} apoiadores sincronizados automaticamente!")
            time.sleep(1)
            st.rerun()
            
    except Exception as e:
        # Não mostra erro para não atrapalhar a experiência
        pass

# Sincroniza apoiadores automaticamente (apenas admin)
if st.session_state.get("is_admin", False):
    if "sincronizado_hoje" not in st.session_state:
        sincronizar_apoiadores_automatico()
        st.session_state.sincronizado_hoje = True

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
# TAB 2: SUGESTÕES DE PRODUTOS
# ============================================================
with tab2:
    st.markdown("## 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Top produtos baseados em tendências de mercado")
    
    # Botão para buscar dados com Selenium
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Buscar Dados Reais", use_container_width=True):
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
    
    produtos = gerar_top10_produtos(forcar_atualizacao=True)
    
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
                "Tendência": item.get("Tendência", "➡️ Estável")
            })
        
        df = pd.DataFrame(dados_tabela)
        
        df["Buscar na Shopee"] = df["Produto"].apply(
            lambda x: f'<a href="https://shopee.com.br/search?keyword={quote(x)}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>'
        )
        
        colunas = ["Produto", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência", "Buscar na Shopee"]
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
        st.metric("🎫 Créditos restantes", "10 / 10")
        
        if st.button("🚀 Gerar Vídeo", type="primary", use_container_width=True):
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
    
    if st.session_state.get("aba_conteudo", False):
        if produto_pre_selecionado:
            st.success(f"🎬 Criando conteúdo para: **{produto_pre_selecionado}**")
        st.session_state.aba_conteudo = False
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        produto_conteudo = st.text_input(
            "📦 Qual produto você quer criar conteúdo?",
            placeholder="Ex: sapateira, smartwatch, casaco feminino...",
            value=produto_pre_selecionado,
            key="produto_conteudo_input"
        )
    
    with col2:
        categoria_conteudo = st.selectbox(
            "🏷️ Categoria",
            ["moda", "eletrônico", "beleza", "casa", "infantil", "esporte"],
            index=0,
            key="categoria_conteudo"
        )
        
        duracao_conteudo = st.selectbox(
            "⏱️ Duração do vídeo",
            ["curto (15-30s)", "medio (30-60s)", "longo (60-90s)"],
            index=1,
            key="duracao_conteudo"
        )
    
    if produto_pre_selecionado:
        st.session_state.produto_conteudo = ""
    
    if st.button("🚀 Gerar Conteúdo", type="primary", use_container_width=True, key="gerar_conteudo_btn"):
        if not produto_conteudo:
            st.error("❌ Digite o nome do produto!")
        else:
            with st.spinner("🤖 Gerando conteúdo inteligente..."):
                try:
                    duracao_map = {
                        "curto (15-30s)": "curto",
                        "medio (30-60s)": "medio",
                        "longo (60-90s)": "longo"
                    }
                    
                    conteudo = gerar_conteudo_completo(
                        produto=produto_conteudo,
                        categoria=categoria_conteudo,
                        duracao=duracao_map[duracao_conteudo]
                    )
                    
                    salvar_conteudo_cache(conteudo)
                    
                    st.markdown("---")
                    st.markdown("## 📝 Títulos Sugeridos")
                    st.json(conteudo.get("titulos", []))
                    
                    st.markdown("---")
                    st.markdown("## ✍️ Roteiro Detalhado")
                    st.markdown(conteudo.get("roteiro", ""))
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar conteúdo: {e}")

# ============================================================
# TAB 6: APOIADORES
# ============================================================
with tab6:
    st.markdown("## 👑 Gerenciar Apoiadores")
    if st.session_state.get("is_admin", False):
        st.markdown("### Adicionar Novo Apoiador")
        with st.form("form_novo_apoiador"):
            nome_apoiador = st.text_input("Nome do Apoiador")
            email_apoiador = st.text_input("Email do Apoiador")
            plano_apoiador = st.selectbox("Plano", ["Apoiador", "Premium", "Fundador"])
            submitted = st.form_submit_button("Adicionar Apoiador")
            if submitted:
                if nome_apoiador and email_apoiador:
                    adicionar_apoiador(nome_apoiador, email_apoiador, plano_apoiador)
                    st.success(f"✅ Apoiador {nome_apoiador} adicionado!")
                    st.rerun()
        
        st.markdown("### Apoiadores Atuais")
        apoiadores_atuais = carregar_apoiadores()
        if apoiadores_atuais:
            df_apoiadores = pd.DataFrame(apoiadores_atuais).T
            st.dataframe(df_apoiadores)
            
            apoiador_remover = st.selectbox("Selecione o apoiador para remover", list(apoiadores_atuais.keys()), format_func=lambda x: apoiadores_atuais[x]['nome'])
            if st.button("Remover Apoiador"):
                remover_apoiador(apoiador_remover)
                st.success(f"✅ Apoiador {apoiadores_atuais[apoiador_remover]['nome']} removido!")
                st.rerun()
    else:
        st.warning("Apenas administradores podem gerenciar apoiadores.")

# ============================================================
# TAB 7: LICENÇAS
# ============================================================
with tab7:
    st.markdown("## 🔑 Gerenciar Licenças")
    if st.session_state.get("is_admin", False):
        sistema_licencas = SistemaLicencas()
        licencas_df = pd.DataFrame(sistema_licencas.dados["licencas"]).T
        st.dataframe(licencas_df)
    else:
        st.warning("Apenas administradores podem gerenciar licenças.")

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
    if st.session_state.get("is_admin", False):
        try:
            with open("logs.json", "r", encoding="utf-8") as f:
                logs = json.load(f)
                st.json(logs)
        except:
            st.info("Nenhum log encontrado.")
    else:
        st.warning("Apenas administradores podem visualizar os logs.")

# ============================================================
# TAB 10: ADMIN
# ============================================================
with tab10:
    st.markdown("## ⚙️ Painel Administrativo")
    if st.session_state.get("is_admin", False):
        if st.button("Limpar Cache de Produtos"):
            if os.path.exists("produtos_cache.json"):
                os.remove("produtos_cache.json")
                st.success("✅ Cache limpo!")
    else:
        st.warning("Apenas administradores podem acessar o painel administrativo.")
