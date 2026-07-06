import streamlit as st
import warnings
from datetime import datetime
from urllib.parse import quote
import pandas as pd
import time

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
from modules.auth import verificar_login
from modules.views import (
    render_dashboard, 
    render_status_usuario, 
    render_painel_apoiadores_detalhado
)
from modules.models import gerar_top10_produtos, PALAVRAS_CHAVE_CAUDA_LONGA
from modules.serper import buscar_produtos_serper

# ============================================================
# VERIFICAR LOGIN
# ============================================================
licenca = verificar_login()

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "📌 Sugestões de Produtos",
    "📅 Calendário de Conteúdo",
    "🎬 Criar Vídeo IA",
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
    
    produtos = gerar_top10_produtos()
    
    if produtos:
        dados_tabela = []
        for item in produtos:
            produto = item.get("Produto", "").lower()
            dados_palavra = PALAVRAS_CHAVE_CAUDA_LONGA.get(produto, {})
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
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
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
# TAB 5: APOIADORES (DETALHADO)
# ============================================================
with tab5:
    render_painel_apoiadores_detalhado()

# ============================================================
# TAB 6: LICENÇAS (APENAS ADMIN)
# ============================================================
with tab6:
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
                    from modules.models import SistemaLicencas
                    sistema = SistemaLicencas()
                    codigo = sistema.gerar_licenca(novo_usuario, novo_email, plano, is_apoiador)
                    st.success("✅ Licença gerada com sucesso!")
                    st.code(f"Código: {codigo}", language="text")
                    if is_apoiador:
                        st.success("👑 Usuário adicionado como apoiador!")
                    st.warning("⚠️ Guarde este código! Ele não será exibido novamente.")
        
        st.markdown("---")
        st.markdown("### 📋 Licenças Ativas")
        
        from modules.models import SistemaLicencas
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
