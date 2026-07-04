import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import json
import os
import warnings

# ============================================================
# SUPRIMIR WARNINGS
# ============================================================
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTES
# ============================================================
CHAVE_TESTE = "TESTE-AFILIADO-2026"
ARQUIVO_CACHE = "cache_tendencias.json"

# ============================================================
# CONFIGURACAO DAS APIS
# ============================================================
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================
# DADOS HISTORICOS POR MES (APENAS PARA SUGESTAO)
# ============================================================
DADOS_HISTORICOS = {
    1: {
        "tendencias": ["smartwatch", "fone bluetooth", "material escolar", "mochila", "tenis", 
                       "caderno", "caneta", "estojo", "mochila escolar", "luminaria de mesa"],
        "eventos": ["Volta às Aulas", "Ano Novo"],
        "sazonal": "Verão"
    },
    2: {
        "tendencias": ["fantasia", "biquini", "sungas", "protetor solar", "fone", 
                       "carnaval", "glitter", "maquiagem", "chinelo", "caixa de som"],
        "eventos": ["Carnaval"],
        "sazonal": "Verão"
    },
    3: {
        "tendencias": ["kit praia", "canga", "chapeu", "oculos sol", "smartwatch",
                       "vestido", "sandalia", "protetor solar", "toalha", "bolsa praia"],
        "eventos": ["Dia da Mulher", "Outono"],
        "sazonal": "Outono"
    },
    4: {
        "tendencias": ["ovo pascoa", "chocolate", "cesta", "fone", "smartwatch",
                       "brinquedo", "pelucia", "jogo", "boneca", "carrinho"],
        "eventos": ["Páscoa", "Tiradentes"],
        "sazonal": "Outono"
    },
    5: {
        "tendencias": ["dia das maes", "perfume", "bolsa", "vestido", "smartwatch",
                       "flores", "kit beleza", "caneca", "cartao presente", "bijuteria"],
        "eventos": ["Dia das Mães", "Dia do Trabalho"],
        "sazonal": "Outono"
    },
    6: {
        "tendencias": ["dia dos namorados", "perfume", "vinho", "chocolate", "fone",
                       "kit jantar", "lingerie", "presente romantico", "jantar", "flores"],
        "eventos": ["Dia dos Namorados", "Festa Junina"],
        "sazonal": "Inverno"
    },
    7: {
        "tendencias": ["casaco", "bota", "cachecol", "fone", "smartwatch",
                       "blusa de la", "jaqueta", "cobertor", "meia", "luva"],
        "eventos": ["Férias Escolares"],
        "sazonal": "Inverno"
    },
    8: {
        "tendencias": ["dia dos pais", "relogio", "cinto", "ferramenta", "smartwatch",
                       "camisa", "perfume masculino", "kit churrasco", "caneca", "carteira"],
        "eventos": ["Dia dos Pais", "Volta às Aulas"],
        "sazonal": "Inverno"
    },
    9: {
        "tendencias": ["camisa", "calca", "vestido", "tenis", "smartwatch",
                       "blusa", "jaqueta jeans", "sapato social", "mochila", "bolsa"],
        "eventos": ["Independência do Brasil", "Primavera"],
        "sazonal": "Primavera"
    },
    10: {
        "tendencias": ["fantasia halloween", "decoracao", "brinquedo", "fone", "smartwatch",
                       "maquiagem", "doces", "abobora", "mascara", "livro infantil"],
        "eventos": ["Dia das Crianças", "Halloween"],
        "sazonal": "Primavera"
    },
    11: {
        "tendencias": ["black friday", "eletronico", "celular", "tv", "smartwatch",
                       "notebook", "fone", "caixa de som", "carregador", "power bank"],
        "eventos": ["Black Friday", "Cyber Monday"],
        "sazonal": "Primavera"
    },
    12: {
        "tendencias": ["natal", "presente", "arvore", "decoracao", "smartwatch",
                       "brinquedo", "perfume", "kit beleza", "vinho", "espumante"],
        "eventos": ["Natal", "Réveillon"],
        "sazonal": "Verão"
    }
}

# ============================================================
# FUNCOES DE API (APENAS QUANDO USUARIO CLICAR)
# ============================================================
class GoogleShoppingAPI:
    def __init__(self):
        self.api_key = SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
    
    def buscar_produtos(self, termo, limite=5):
        if not self.api_key:
            return []
        
        try:
            params = {
                "q": termo,
                "tbm": "shop",
                "api_key": self.api_key,
                "gl": "br",
                "hl": "pt",
                "num": limite,
                "location": "Brazil",
                "device": "desktop"
            }
            
            resp = requests.get(self.base_url, params=params, timeout=15)
            data = resp.json()
            
            produtos = []
            for item in data.get("shopping_results", [])[:limite]:
                preco_str = item.get("price", "R$ 0").replace("R$", "").replace(",", ".").strip()
                try:
                    preco_num = float(preco_str.split()[0]) if preco_str else 0
                except:
                    preco_num = 0
                
                produtos.append({
                    "nome": item.get("title", ""),
                    "preco": item.get("price", "R$ 0"),
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "avaliacao": item.get("rating", None),
                    "reviews": item.get("reviews", 0)
                })
            
            return produtos
        except Exception as e:
            st.error(f"Erro na busca: {e}")
            return []
    
    def buscar_total_resultados(self, termo):
        if not self.api_key:
            return 0
        
        try:
            params = {
                "q": termo,
                "tbm": "shop",
                "api_key": self.api_key,
                "gl": "br",
                "hl": "pt",
                "num": 1
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            data = resp.json()
            return data.get("search_information", {}).get("total_results", 0)
        except:
            return 0

# ============================================================
# FUNCOES DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos - Afiliados")
        st.markdown("### 🔐 Login")
        chave = st.text_input("Digite sua chave de acesso:", type="password")
        if st.button("Entrar", type="primary"):
            if chave == CHAVE_TESTE:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Chave invalida. Tente novamente.")
        st.stop()

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

google_shopping = GoogleShoppingAPI()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    st.markdown("---")
    
    st.markdown("### 🔌 Status da API")
    if SERPAPI_KEY:
        st.success("✅ SerpApi configurada")
        st.caption("Busca apenas quando clicar em 'Buscar'")
    else:
        st.warning("⚠️ SerpApi nao configurada")
    
    st.markdown("---")
    
    st.markdown("### 📌 Como funciona")
    st.caption("1. Sugestões baseadas no mês atual")
    st.caption("2. Clique em 'Buscar' para consultar")
    st.caption("3. Dados reais do Google Shopping")

# ============================================================
# PAINEL PRINCIPAL
# ============================================================
st.title("🛒 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

# ============================================================
# DADOS DO MES ATUAL
# ============================================================
mes_atual = datetime.now().month
dados_mes = DADOS_HISTORICOS.get(mes_atual, DADOS_HISTORICOS[1])

st.markdown(f"""
### 📊 Tendências para {datetime.now().strftime('%B').capitalize()}
**Eventos:** {', '.join(dados_mes['eventos'])} | **Sazonal:** {dados_mes['sazonal']}
""")

st.markdown("---")

# ============================================================
# TABELA DE SUGESTOES (ESTILO PRINT)
# ============================================================
st.markdown("### 🎯 Sugestões de Produtos para este Mês")

# Prepara dados para tabela
dados_tabela = []
for termo in dados_mes["tendencias"]:
    dados_tabela.append({
        "Produto": termo,
        "Categoria": "Geral",
        "Evento": ", ".join(dados_mes['eventos']),
        "Potencial": "Médio",
        "Ação": f"🔍 {termo}"
    })

# Cria DataFrame
df_sugestoes = pd.DataFrame(dados_tabela)

# Exibe tabela
st.dataframe(
    df_sugestoes,
    column_config={
        "Produto": "Produto",
        "Categoria": "Categoria",
        "Evento": "Evento Relacionado",
        "Potencial": "Potencial",
        "Ação": st.column_config.Column(
            "Buscar na Shopee",
            help="Clique para abrir a busca"
        )
    },
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ============================================================
# AREA DE BUSCA (ONDE USA SERPAPI)
# ============================================================
st.markdown("### 🔍 Buscar Produto Específico")

col1, col2 = st.columns([3, 1])
with col1:
    termo_busca = st.text_input(
        "Digite um produto:",
        placeholder="Ex: smartwatch, jelly blush...",
        label_visibility="collapsed",
        key="busca_input"
    )
with col2:
    if st.button("🔍 Buscar", type="primary", use_container_width=True):
        if termo_busca:
            st.session_state.termo_busca = termo_busca
            st.session_state.buscar = True

# Verifica se deve buscar
if st.session_state.get("buscar", False) and st.session_state.get("termo_busca"):
    termo = st.session_state.termo_busca
    
    with st.spinner(f"Buscando '{termo}' no Google Shopping..."):
        produtos = google_shopping.buscar_produtos(termo, 8)
        total = google_shopping.buscar_total_resultados(termo)
        
        st.markdown(f"### 📊 Resultados para '{termo}'")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Resultados", total if total > 0 else "N/A")
        with col2:
            st.metric("Produtos Exibidos", len(produtos))
        
        st.markdown("---")
        
        if produtos:
            # Cria DataFrame com resultados
            df_produtos = pd.DataFrame([{
                "Produto": p.get("nome", "")[:60],
                "Preço": p.get("preco", ""),
                "Loja": p.get("loja", ""),
                "Avaliação": f"⭐ {p.get('avaliacao', 'N/A')} ({p.get('reviews', 0)})" if p.get('avaliacao') else "Sem avaliação",
                "Link": p.get("link", "")
            } for p in produtos])
            
            st.dataframe(
                df_produtos,
                column_config={
                    "Produto": "Produto",
                    "Preço": "Preço",
                    "Loja": "Loja",
                    "Avaliação": "Avaliação",
                    "Link": st.column_config.LinkColumn("Ver Produto")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Nenhum produto encontrado. Tente outro termo.")
    
    # Limpa estado
    st.session_state.buscar = False
    st.session_state.termo_busca = ""

st.markdown("---")

# ============================================================
# DICAS E ESTRATEGIAS
# ============================================================
st.markdown("### 💡 Estratégias para Afiliados")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **📅 Datas Comemorativas**
    
    Aproveite os eventos do mês para criar conteúdo:
    - Posts sobre presentes
    - Vídeos de unboxing
    - Listas de "O que comprar"
    """)

with col2:
    st.success("""
    **🎯 Produtos com Maior Potencial**
    
    Foque em produtos que combinam:
    - Tendência sazonal
    - Baixa concorrência
    - Preço entre R$30-R$150
    - Bom volume de vendas
    """)

st.markdown("---")

# ============================================================
# RODAPE
# ============================================================
st.caption(f"🛒 Minerador de Produtos v2.0 | Sugestões baseadas em dados históricos | Buscas na SerpApi apenas quando clicar")
