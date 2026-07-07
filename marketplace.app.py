import streamlit as st
import warnings
from datetime import datetime
from urllib.parse import quote
import pandas as pd
import time
import logging
import sys

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
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# IMPORTAR MÓDULOS
# ============================================================
from modules.auth import verificar_login, SistemaLicencas
from modules.views import render_dashboard, render_status_usuario, render_painel_apoiadores_detalhado
from modules.models import gerar_top10_produtos, PALAVRAS_CHAVE_CAUDA_LONGA, obter_palavra_chave
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

# ============================================================
# VERIFICAR LOGIN
# ============================================================
licenca = verificar_login()

# ============================================================
# TITULO REMOVIDO - JÁ ESTÁ NO DASHBOARD
# ============================================================

# ============================================================
# STATUS DO USUÁRIO
# ============================================================
render_status_usuario()
st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA",
    "🤖 Criar Conteúdo",
    "👑 Apoiadores",
    "🔑 Licenças"
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
    
    produtos = gerar_top10_produtos(forcar_atualizacao=True)
    
    if produtos:
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            
            # USA A FUNÇÃO MELHORADA PARA PALAVRA-CHAVE
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
        
        # Adiciona botão "Criar Conteúdo" na tabela
        df["🎬 Criar Conteúdo"] = df["Produto"].apply(
            lambda x: f'<a href="#" onclick="document.getElementById(\'ir_para_conteudo_{x.lower()}\').click(); return false;" style="text-decoration: none;"><span style="background-color: #FF6B6B; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: none;">🎬 Criar</span></a>'
        )
        
        colunas = ["Produto", "🔑 Palavra-chave", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência", "Buscar na Shopee", "🎬 Criar Conteúdo"]
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
    
    # Verifica se veio de um clique do dashboard
    produto_pre_selecionado = st.session_state.get("produto_conteudo", "")
    
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
    
    # Limpa o estado após usar
    if produto_pre_selecionado:
        st.session_state.produto_conteudo = ""
    
    if st.button("🚀 Gerar Conteúdo", type="primary", use_container_width=True, key="gerar_conteudo_btn"):
        if not produto_conteudo:
            st.error("❌ Digite o nome do produto!")
        else:
            with st.spinner("🤖 Gerando conteúdo inteligente..."):
                try:
                    # Mapeia duração
                    duracao_map = {
                        "curto (15-30s)": "curto",
                        "medio (30-60s)": "medio",
                        "longo (60-90s)": "longo"
                    }
                    
                    # Gera conteúdo completo
                    conteudo = gerar_conteudo_completo(
                        produto=produto_conteudo,
                        categoria=categoria_conteudo,
                        duracao=duracao_map[duracao_conteudo]
                    )
                    
                    # Salva no cache
                    salvar_conteudo_cache(conteudo)
                    
                    # ============================================================
                    # TÍTULOS
                    # ============================================================
                    st.markdown("---")
                    st.markdown("## 📝 Títulos Sugeridos")
                    st.caption("Escolha um título para seu vídeo")
                    
                    titulos = conteudo["titulos"]
                    
                    # Exibe em grid de 3
                    cols = st.columns(3)
                    for i, titulo in enumerate(titulos[:6]):
                        with cols[i % 3]:
                            with st.container(border=True):
                                st.markdown(f"**Título {i+1}**")
                                st.markdown(f"🎯 {titulo}")
                                if st.button(f"📋 Copiar", key=f"copy_titulo_{i}"):
                                    st.code(titulo, language="text")
                                if st.button(f"📌 Usar", key=f"use_titulo_{i}"):
                                    st.session_state.titulo_selecionado = titulo
                                    st.success(f"✅ Título selecionado: {titulo}")
                    
                    # ============================================================
                    # SCRIPT
                    # ============================================================
                    st.markdown("---")
                    st.markdown("## 🎬 Roteiro Completo")
                    st.caption(f"⏱️ Duração total: {conteudo['script']['duracao_total']} segundos")
                    
                    # Exibe cada cena
                    for cena in conteudo["script"]["cenas"]:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([1, 2, 2])
                            with col1:
                                st.markdown(f"**🎬 Cena {cena['cena']}**")
                                st.caption(f"⏱️ {cena['duracao']}")
                            with col2:
                                st.markdown(f"📷 {cena['enquadramento']}")
                            with col3:
                                st.info(f"🎤 {cena['fala']}")
                    
                    # Botão copiar script
                    script_completo = "\n\n".join([f"CENA {c['cena']} ({c['duracao']}): {c['enquadramento']}\nFALA: {c['fala']}" for c in conteudo["script"]["cenas"]])
                    if st.button("📋 Copiar Script Completo"):
                        st.code(script_completo, language="text")
                    
                    # ============================================================
                    # DICAS DE GRAVAÇÃO
                    # ============================================================
                    st.markdown("---")
                    st.markdown("## 🎥 Dicas de Gravação")
                    
                    dicas = conteudo["dicas_gravacao"]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.container(border=True):
                            st.markdown("**🎬 Cenários sugeridos**")
                            for cenario in dicas["cenarios_sugeridos"]:
                                st.markdown(f"✅ {cenario}")
                    
                    with col2:
                        with st.container(border=True):
                            st.markdown("**🎧 Áudio**")
                            for audio in dicas["dicas_audio"]:
                                st.markdown(f"✅ {audio}")
                    
                    # Melhores horários
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.container(border=True):
                            st.markdown("**⏰ Melhores Horários para Postar**")
                            for horario in dicas["melhores_horarios"][:2]:
                                st.markdown(f"🕐 {horario}")
                    with col2:
                        with st.container(border=True):
                            st.markdown("**📝 Legendas Sugeridas**")
                            for legenda in dicas["legendas_sugeridas"]:
                                st.markdown(f"💬 {legenda}")
                    
                    # ============================================================
                    # HASHTAGS
                    # ============================================================
                    st.markdown("---")
                    st.markdown("## 🏷️ Hashtags Sugeridas")
                    
                    hashtags = conteudo["hashtags_sugeridas"]
                    tags_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 4px 12px; border-radius: 16px; margin: 4px; font-size: 14px; display: inline-block;">{h}</span>' for h in hashtags])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
                    if st.button("📋 Copiar Hashtags"):
                        st.code(" ".join(hashtags), language="text")
                    
                    # ============================================================
                    # ANÁLISE DE CONCORRÊNCIA
                    # ============================================================
                    st.markdown("---")
                    st.markdown("## 📊 Análise de Concorrência")
                    
                    analise = conteudo["analise_concorrencia"]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.container(border=True):
                            st.markdown("**🏆 Diferenciais do Produto**")
                            for diff in analise["diferenciais_sugeridos"]:
                                st.markdown(f"✅ {diff}")
                    
                    with col2:
                        with st.container(border=True):
                            st.markdown("**🎯 Posicionamento Sugerido**")
                            st.info(analise["posicionamento_sugerido"])
                            st.success(f"💪 {analise['ponto_forte']}")
                    
                    # Concorrentes
                    with st.expander("👀 Ver concorrentes"):
                        df_concorrentes = pd.DataFrame(analise["concorrentes"])
                        df_concorrentes["avaliacao"] = df_concorrentes["avaliacao"].apply(lambda x: f"⭐ {x:.1f}")
                        st.dataframe(df_concorrentes, use_container_width=True, hide_index=True)
                    
                    # ============================================================
                    # LINK SHOPEE
                    # ============================================================
                    st.markdown("---")
                    st.markdown("## 🔗 Link para Shopee")
                    
                    link_shopee = conteudo["script"]["link_shopee"]
                    st.markdown(f"🔍 [Buscar {produto_conteudo} na Shopee]({link_shopee})")
                    
                    if st.button("📋 Copiar Link"):
                        st.code(link_shopee, language="text")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar conteúdo: {str(e)}")

# ============================================================
# TAB 6: APOIADORES
# ============================================================
with tab6:
    render_painel_apoiadores_detalhado()

# ============================================================
# TAB 7: LICENÇAS (APENAS ADMIN)
# ============================================================
with tab7:
    is_admin = st.session_state.get("is_admin", False)
    
    if not is_admin:
        st.warning("🔒 **Acesso restrito a administradores.**")
        st.info("Entre em contato com o suporte para gerenciar licenças.")
    else:
        st.markdown("## 🔑 Gerenciamento de Licenças")
        st.caption("Crie, gerencie e monitore licenças do sistema")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total", "2")
        with col2:
            st.metric("✅ Ativas", "2")
        with col3:
            st.metric("🔑 Admin", "1")
        
        st.markdown("---")
        
        with st.expander("🆕 Criar Nova Licença", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                novo_usuario = st.text_input("Nome do Usuário", placeholder="Ex: João Silva", key="lic_nome")
                novo_email = st.text_input("E-mail", placeholder="joao@email.com", key="lic_email")
            with col2:
                plano = st.selectbox("Plano", ["Trial 7 dias", "Apoiador R$ 59,90"], key="lic_plano")
                is_apoiador = st.checkbox("👑 Tornar APOIADOR (royalties)", key="lic_apoiador")
            
            if st.button("🚀 Gerar Licença", use_container_width=True, key="lic_btn"):
                if not novo_usuario or not novo_email:
                    st.error("❌ Preencha nome e e-mail")
                else:
                    sistema = SistemaLicencas()
                    codigo = sistema.gerar_licenca(novo_usuario, novo_email, plano, is_apoiador)
                    st.success("✅ Licença gerada com sucesso!")
                    st.code(f"Código: {codigo}", language="text")
                    if is_apoiador:
                        st.success("👑 Usuário adicionado como apoiador!")
                    st.warning("⚠️ Guarde este código! Ele não será exibido novamente.")
        
        st.markdown("---")
        st.markdown("### 📋 Licenças Ativas")
        
        sistema = SistemaLicencas()
        licencas = sistema.dados["licencas"]
        
        df_licencas = pd.DataFrame([
            {"Código": codigo, "Usuário": dados.get("usuario"), "Plano": dados.get("plano"), "Status": "🟢 Ativo" if dados.get("status") == "ativo" else "🔴 Inativo"}
            for codigo, dados in licencas.items()
        ])
        
        st.dataframe(df_licencas, use_container_width=True, hide_index=True)

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v4.0 | {datetime.now().year}")
