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
    
    # Se veio da aba de insights, mostra mensagem
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
        
        # Carrega dados atualizados
        sistema = SistemaLicencas()
        apoiadores = carregar_apoiadores()
        
        total_licencas = len(sistema.dados["licencas"])
        ativas = sum(1 for l in sistema.dados["licencas"].values() if l.get("status") == "ativo")
        total_apoiadores = len(apoiadores)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Licenças", total_licencas)
        with col2:
            st.metric("✅ Ativas", ativas)
        with col3:
            st.metric("👑 Apoiadores", total_apoiadores)
        
        st.markdown("---")
        
        # ============================================================
        # CRIAR NOVA LICENÇA (COM SINCRONIZAÇÃO DE APOIADOR)
        # ============================================================
        with st.expander("🆕 Criar Nova Licença", expanded=True):
            st.markdown("### 📝 Dados do Usuário")
            st.caption("Preencha os dados para gerar uma nova licença")
            
            col1, col2 = st.columns(2)
            with col1:
                novo_usuario = st.text_input("👤 Nome do Usuário", placeholder="Ex: João Silva", key="lic_nome")
                novo_email = st.text_input("📧 E-mail", placeholder="joao@email.com", key="lic_email")
            with col2:
                plano = st.selectbox("📋 Plano", ["Trial 7 dias", "Apoiador R$ 59,90", "Premium R$ 99,90"], key="lic_plano")
                is_apoiador = st.checkbox("👑 Tornar APOIADOR (recebe royalties)", key="lic_apoiador")
                
                if is_apoiador:
                    st.info("💡 O apoiador receberá R$ 5,00 por novo apoiador cadastrado após ele.")
            
            if st.button("🚀 Gerar Licença", use_container_width=True, key="lic_btn"):
                if not novo_usuario or not novo_email:
                    st.error("❌ Preencha nome e e-mail!")
                else:
                    try:
                        # 1. Gera a licença
                        sistema = SistemaLicencas()
                        codigo = sistema.gerar_licenca(novo_usuario, novo_email, plano, is_apoiador)
                        
                        # 2. Se for apoiador, adiciona na lista de apoiadores
                        if is_apoiador:
                            # Verifica se já existe
                            apoiadores_existentes = carregar_apoiadores()
                            ja_existe = False
                            for ap in apoiadores_existentes.values():
                                if ap.get("email") == novo_email:
                                    ja_existe = True
                                    break
                            
                            if not ja_existe:
                                # Mapeia plano para tipo de apoiador
                                plano_apoiador = "Premium" if "Premium" in plano else "Apoiador"
                                adicionar_apoiador(
                                    nome=novo_usuario,
                                    email=novo_email,
                                    plano=plano_apoiador
                                )
                                st.success(f"👑 {novo_usuario} adicionado como apoiador!")
                            else:
                                st.info(f"ℹ️ {novo_usuario} já é apoiador.")
                        
                        # 3. Mostra o código
                        st.success("✅ Licença gerada com sucesso!")
                        st.code(f"Código: {codigo}", language="text")
                        st.warning("⚠️ Guarde este código! Ele não será exibido novamente.")
                        
                        # 4. Mostra resumo
                        st.markdown("---")
                        st.markdown("### 📋 Resumo")
                        st.markdown(f"""
                        - **Usuário:** {novo_usuario}
                        - **E-mail:** {novo_email}
                        - **Plano:** {plano}
                        - **Apoiador:** {'✅ Sim' if is_apoiador else '❌ Não'}
                        - **Código:** `{codigo}`
                        """)
                        
                        time.sleep(1)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar licença: {str(e)}")
        
        st.markdown("---")
        
        # ============================================================
        # LISTA DE APOIADORES (INTEGRADA)
        # ============================================================
        st.markdown("## 👑 Apoiadores do Projeto")
        st.caption("Lista de todos os apoiadores cadastrados")
        
        apoiadores = carregar_apoiadores()
        
        if apoiadores:
            # Ordena por ordem
            apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
            
            # Exibe em cards
            cores = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE"]
            
            # Exibe em grid de 4
            cols = st.columns(4)
            for i, apoiador in enumerate(apoiadores_ordenados):
                with cols[i % 4]:
                    cor = cores[i % len(cores)]
                    nome = apoiador.get("nome", "Apoiador")
                    email = apoiador.get("email", "")
                    ordem = apoiador.get("ordem", 999)
                    coroinha = apoiador.get("coroinha", "👑")
                    plano = apoiador.get("plano", "Apoiador")
                    
                    with st.container(border=True):
                        st.markdown(f"""
                        <div style="
                            background: {cor};
                            color: white;
                            padding: 8px 12px;
                            border-radius: 8px 8px 0 0;
                            margin: -12px -12px 10px -12px;
                            text-align: center;
                            font-weight: bold;
                            font-size: 16px;
                        ">
                            {coroinha} {nome}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"**📧** {email}")
                        st.markdown(f"**📋 Ordem:** #{ordem}")
                        st.markdown(f"**📌 Plano:** {plano}")
                        
                        # Verifica repasse
                        depois = sum(1 for a in apoiadores.values() if a.get("ordem", 999) > ordem)
                        if depois > 0 and apoiador.get("repasse_ativo", True):
                            st.success(f"⬇️ {depois} apoiadores - R${depois * 5.00:.2f}/mês")
                        else:
                            st.info("⏳ Aguardando novos apoiadores")
        else:
            st.info("📭 Nenhum apoiador cadastrado ainda.")
        
        st.markdown("---")
        
        # ============================================================
        # LISTA DE LICENÇAS ATIVAS
        # ============================================================
        st.markdown("## 📋 Licenças Ativas")
        st.caption("Todas as licenças geradas no sistema")
        
        sistema = SistemaLicencas()
        licencas = sistema.dados["licencas"]
        
        # Cria DataFrame com todas as licenças
        dados_licencas = []
        for codigo, dados in licencas.items():
            # Verifica se é apoiador
            is_apoiador = dados.get("is_apoiador", False)
            status = dados.get("status", "ativo")
            
            dados_licencas.append({
                "Código": codigo[:12] + "..." if len(codigo) > 12 else codigo,
                "Usuário": dados.get("usuario", "N/A"),
                "E-mail": dados.get("email", "N/A"),
                "Plano": dados.get("plano", "N/A"),
                "👑 Apoiador": "✅ Sim" if is_apoiador else "❌ Não",
                "Status": "🟢 Ativo" if status == "ativo" else "🔴 Inativo"
            })
        
        if dados_licencas:
            df_licencas = pd.DataFrame(dados_licencas)
            st.dataframe(df_licencas, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # ============================================================
        # AÇÕES RÁPIDAS
        # ============================================================
        with st.expander("⚙️ Ações Rápidas"):
            st.markdown("### 🔄 Sincronizar Apoiadores")
            st.caption("Sincroniza manualmente apoiadores com licenças")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Sincronizar Agora", use_container_width=True):
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
                                    adicionar_apoiador(usuario, email, "Apoiador")
                                    contador += 1
                        
                        if contador > 0:
                            st.success(f"✅ {contador} apoiadores sincronizados!")
                        else:
                            st.info("ℹ️ Nenhum apoiador novo para sincronizar.")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro na sincronização: {str(e)}")
            
            with col2:
                if st.button("📋 Verificar Licenças", use_container_width=True):
                    sistema = SistemaLicencas()
                    st.write("### Licenças com flag de apoiador:")
                    encontrou = False
                    for codigo, dados in sistema.dados["licencas"].items():
                        if dados.get("is_apoiador", False):
                            st.write(f"- {codigo}: {dados.get('usuario')} ({dados.get('email')})")
                            encontrou = True
                    if not encontrou:
                        st.info("ℹ️ Nenhuma licença com flag de apoiador encontrada.")
            
            st.markdown("---")
            
            # Botão para limpar cache
            if st.button("🧹 Limpar Cache de Conteúdo", use_container_width=True):
                try:
                    if os.path.exists("conteudo_cache.json"):
                        os.remove("conteudo_cache.json")
                        st.success("✅ Cache de conteúdo limpo!")
                    else:
                        st.info("ℹ️ Nenhum cache encontrado.")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

# ============================================================
# RODAPE
# ============================================================
st.markdown("---")
st.caption(f"🛒 Minerador de Produtos v4.0 | {datetime.now().year}")
