import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import json
import os
import warnings
import random

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
ARQUIVO_CONSULTAS = "consultas_dia.json"

# ============================================================
# CONFIGURACAO DAS APIS
# ============================================================
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================
# CONTROLE DE CONSULTAS DIARIAS
# ============================================================
class ControleConsultas:
    def __init__(self):
        self.arquivo = ARQUIVO_CONSULTAS
        self.dados = self.carregar()
        self.limite_diario = 3
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, ensure_ascii=False, indent=2)
    
    def consultas_hoje(self):
        hoje = datetime.now().date().isoformat()
        if hoje not in self.dados:
            self.dados[hoje] = {"consultas": 0, "termos": []}
            self.salvar()
        return self.dados[hoje]["consultas"]
    
    def pode_consultar(self):
        return self.consultas_hoje() < self.limite_diario
    
    def registrar_consulta(self, termo):
        hoje = datetime.now().date().isoformat()
        if hoje not in self.dados:
            self.dados[hoje] = {"consultas": 0, "termos": []}
        
        self.dados[hoje]["consultas"] += 1
        self.dados[hoje]["termos"].append({
            "termo": termo,
            "hora": datetime.now().strftime("%H:%M")
        })
        self.salvar()
    
    def get_status(self):
        hoje = datetime.now().date().isoformat()
        if hoje in self.dados:
            return {
                "usadas": self.dados[hoje]["consultas"],
                "limite": self.limite_diario,
                "restam": self.limite_diario - self.dados[hoje]["consultas"],
                "termos": [t["termo"] for t in self.dados[hoje]["termos"]]
            }
        return {
            "usadas": 0,
            "limite": self.limite_diario,
            "restam": self.limite_diario,
            "termos": []
        }

# ============================================================
# DADOS HISTORICOS POR MES (APENAS PARA SUGESTAO)
# ============================================================
DADOS_HISTORICOS = {
    1: {
        "tendencias": [
            {"produto": "material escolar", "categoria": "Papelaria", "potencial": "Alto"},
            {"produto": "mochila escolar", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "smartwatch", "categoria": "Eletrônicos", "potencial": "Médio"},
            {"produto": "fone bluetooth", "categoria": "Eletrônicos", "potencial": "Médio"},
            {"produto": "tenis", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "caderno", "categoria": "Papelaria", "potencial": "Médio"},
            {"produto": "estojo", "categoria": "Papelaria", "potencial": "Médio"},
            {"produto": "luminaria de mesa", "categoria": "Casa", "potencial": "Baixo"}
        ],
        "eventos": ["Volta às Aulas", "Ano Novo"],
        "sazonal": "Verão"
    },
    2: {
        "tendencias": [
            {"produto": "fantasia carnaval", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "biquini", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "protetor solar", "categoria": "Beleza", "potencial": "Alto"},
            {"produto": "caixa de som", "categoria": "Eletrônicos", "potencial": "Médio"},
            {"produto": "chinelo", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "glitter", "categoria": "Beleza", "potencial": "Médio"},
            {"produto": "maquiagem", "categoria": "Beleza", "potencial": "Médio"},
            {"produto": "sungas", "categoria": "Moda", "potencial": "Baixo"}
        ],
        "eventos": ["Carnaval"],
        "sazonal": "Verão"
    },
    3: {
        "tendencias": [
            {"produto": "kit praia", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "oculos sol", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "canga", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "vestido", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "sandalia", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "bolsa praia", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "toalha", "categoria": "Casa", "potencial": "Baixo"},
            {"produto": "chapeu", "categoria": "Moda", "potencial": "Baixo"}
        ],
        "eventos": ["Dia da Mulher", "Outono"],
        "sazonal": "Outono"
    },
    4: {
        "tendencias": [
            {"produto": "ovo pascoa", "categoria": "Alimentos", "potencial": "Alto"},
            {"produto": "chocolate", "categoria": "Alimentos", "potencial": "Alto"},
            {"produto": "cesta", "categoria": "Casa", "potencial": "Alto"},
            {"produto": "brinquedo", "categoria": "Brinquedos", "potencial": "Médio"},
            {"produto": "pelucia", "categoria": "Brinquedos", "potencial": "Médio"},
            {"produto": "jogo", "categoria": "Brinquedos", "potencial": "Médio"},
            {"produto": "boneca", "categoria": "Brinquedos", "potencial": "Baixo"},
            {"produto": "carrinho", "categoria": "Brinquedos", "potencial": "Baixo"}
        ],
        "eventos": ["Páscoa", "Tiradentes"],
        "sazonal": "Outono"
    },
    5: {
        "tendencias": [
            {"produto": "dia das maes", "categoria": "Presentes", "potencial": "Alto"},
            {"produto": "perfume", "categoria": "Beleza", "potencial": "Alto"},
            {"produto": "bolsa", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "flores", "categoria": "Presentes", "potencial": "Médio"},
            {"produto": "kit beleza", "categoria": "Beleza", "potencial": "Médio"},
            {"produto": "caneca", "categoria": "Presentes", "potencial": "Médio"},
            {"produto": "bijuteria", "categoria": "Moda", "potencial": "Baixo"},
            {"produto": "cartao presente", "categoria": "Presentes", "potencial": "Baixo"}
        ],
        "eventos": ["Dia das Mães", "Dia do Trabalho"],
        "sazonal": "Outono"
    },
    6: {
        "tendencias": [
            {"produto": "dia dos namorados", "categoria": "Presentes", "potencial": "Alto"},
            {"produto": "perfume", "categoria": "Beleza", "potencial": "Alto"},
            {"produto": "vinho", "categoria": "Alimentos", "potencial": "Alto"},
            {"produto": "kit jantar", "categoria": "Casa", "potencial": "Médio"},
            {"produto": "lingerie", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "jantar", "categoria": "Presentes", "potencial": "Médio"},
            {"produto": "flores", "categoria": "Presentes", "potencial": "Baixo"},
            {"produto": "chocolate", "categoria": "Alimentos", "potencial": "Baixo"}
        ],
        "eventos": ["Dia dos Namorados", "Festa Junina"],
        "sazonal": "Inverno"
    },
    7: {
        "tendencias": [
            {"produto": "casaco", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "blusa de la", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "bota", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "cachecol", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "cobertor", "categoria": "Casa", "potencial": "Médio"},
            {"produto": "meia", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "luva", "categoria": "Moda", "potencial": "Baixo"},
            {"produto": "jaqueta", "categoria": "Moda", "potencial": "Baixo"}
        ],
        "eventos": ["Férias Escolares"],
        "sazonal": "Inverno"
    },
    8: {
        "tendencias": [
            {"produto": "dia dos pais", "categoria": "Presentes", "potencial": "Alto"},
            {"produto": "relogio", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "ferramenta", "categoria": "Casa", "potencial": "Alto"},
            {"produto": "camisa", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "perfume masculino", "categoria": "Beleza", "potencial": "Médio"},
            {"produto": "kit churrasco", "categoria": "Casa", "potencial": "Médio"},
            {"produto": "caneca", "categoria": "Presentes", "potencial": "Baixo"},
            {"produto": "carteira", "categoria": "Moda", "potencial": "Baixo"}
        ],
        "eventos": ["Dia dos Pais", "Volta às Aulas"],
        "sazonal": "Inverno"
    },
    9: {
        "tendencias": [
            {"produto": "camisa", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "calca", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "tenis", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "blusa", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "jaqueta jeans", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "sapato social", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "mochila", "categoria": "Moda", "potencial": "Baixo"},
            {"produto": "bolsa", "categoria": "Moda", "potencial": "Baixo"}
        ],
        "eventos": ["Independência do Brasil", "Primavera"],
        "sazonal": "Primavera"
    },
    10: {
        "tendencias": [
            {"produto": "fantasia halloween", "categoria": "Moda", "potencial": "Alto"},
            {"produto": "brinquedo", "categoria": "Brinquedos", "potencial": "Alto"},
            {"produto": "decoracao", "categoria": "Casa", "potencial": "Alto"},
            {"produto": "maquiagem", "categoria": "Beleza", "potencial": "Médio"},
            {"produto": "doces", "categoria": "Alimentos", "potencial": "Médio"},
            {"produto": "mascara", "categoria": "Moda", "potencial": "Médio"},
            {"produto": "abobora", "categoria": "Casa", "potencial": "Baixo"},
            {"produto": "livro infantil", "categoria": "Livros", "potencial": "Baixo"}
        ],
        "eventos": ["Dia das Crianças", "Halloween"],
        "sazonal": "Primavera"
    },
    11: {
        "tendencias": [
            {"produto": "black friday", "categoria": "Eletrônicos", "potencial": "Alto"},
            {"produto": "smartwatch", "categoria": "Eletrônicos", "potencial": "Alto"},
            {"produto": "fone", "categoria": "Eletrônicos", "potencial": "Alto"},
            {"produto": "celular", "categoria": "Eletrônicos", "potencial": "Médio"},
            {"produto": "caixa de som", "categoria": "Eletrônicos", "potencial": "Médio"},
            {"produto": "carregador", "categoria": "Eletrônicos", "potencial": "Médio"},
            {"produto": "power bank", "categoria": "Eletrônicos", "potencial": "Baixo"},
            {"produto": "notebook", "categoria": "Eletrônicos", "potencial": "Baixo"}
        ],
        "eventos": ["Black Friday", "Cyber Monday"],
        "sazonal": "Primavera"
    },
    12: {
        "tendencias": [
            {"produto": "natal", "categoria": "Presentes", "potencial": "Alto"},
            {"produto": "brinquedo", "categoria": "Brinquedos", "potencial": "Alto"},
            {"produto": "perfume", "categoria": "Beleza", "potencial": "Alto"},
            {"produto": "decoracao", "categoria": "Casa", "potencial": "Médio"},
            {"produto": "kit beleza", "categoria": "Beleza", "potencial": "Médio"},
            {"produto": "vinho", "categoria": "Alimentos", "potencial": "Médio"},
            {"produto": "espumante", "categoria": "Alimentos", "potencial": "Baixo"},
            {"produto": "arvore", "categoria": "Casa", "potencial": "Baixo"}
        ],
        "eventos": ["Natal", "Réveillon"],
        "sazonal": "Verão"
    }
}

# ============================================================
# FUNCOES DE API
# ============================================================
class GoogleShoppingAPI:
    def __init__(self):
        self.api_key = SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
    
    def buscar_produtos(self, termo, limite=3):
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
# FUNCAO PARA ATUALIZAR SUGESTOES COM DADOS DA SERPAPI
# ============================================================
def atualizar_sugestoes_com_serpapi(tendencias):
    """Atualiza sugestões com dados reais da SerpApi"""
    controle = ControleConsultas()
    resultados = []
    
    for item in tendencias:
        termo = item["produto"]
        
        # Tenta buscar dados reais se tiver consulta disponível
        if controle.pode_consultar():
            produtos = google_shopping.buscar_produtos(termo, 2)
            total = google_shopping.buscar_total_resultados(termo)
            
            if produtos:
                controle.registrar_consulta(termo)
                
                # Calcula score baseado nos dados reais
                score = 0
                if total < 50:
                    score = 10  # Excelente
                elif total < 200:
                    score = 7   # Bom
                elif total < 500:
                    score = 4   # Médio
                else:
                    score = 1   # Baixo
                
                # Ajusta potencial baseado nos dados reais
                if score >= 7:
                    potencial = "Alto"
                    status = "🟢"
                elif score >= 4:
                    potencial = "Médio"
                    status = "🟡"
                else:
                    potencial = "Baixo"
                    status = "🟠"
                
                resultados.append({
                    "produto": termo,
                    "categoria": item["categoria"],
                    "potencial": potencial,
                    "status": status,
                    "total_resultados": total,
                    "produtos_encontrados": len(produtos),
                    "score": score,
                    "evento": ", ".join([e for e in item.get("eventos", ["Geral"])])
                })
            else:
                # Fallback: usa dados históricos
                resultados.append({
                    "produto": termo,
                    "categoria": item["categoria"],
                    "potencial": item["potencial"],
                    "status": "🟡" if item["potencial"] == "Alto" else "🟠",
                    "total_resultados": "N/A",
                    "produtos_encontrados": 0,
                    "score": 0,
                    "evento": ", ".join([e for e in item.get("eventos", ["Geral"])])
                })
        else:
            # Sem consultas disponíveis: usa dados históricos
            resultados.append({
                "produto": termo,
                "categoria": item["categoria"],
                "potencial": item["potencial"],
                "status": "🟢" if item["potencial"] == "Alto" else "🟡" if item["potencial"] == "Médio" else "🟠",
                "total_resultados": "N/A",
                "produtos_encontrados": 0,
                "score": 0,
                "evento": ", ".join([e for e in item.get("eventos", ["Geral"])])
            })
    
    return resultados

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

google_shopping = GoogleShoppingAPI()
controle_consultas = ControleConsultas()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    status = controle_consultas.get_status()
    st.markdown("### 🔢 Consultas SerpApi Hoje")
    st.caption(f"📊 {status['usadas']} de {status['limite']} usadas")
    
    if status['restam'] > 0:
        st.success(f"✅ {status['restam']} consultas restantes")
    else:
        st.warning("⚠️ Limite de 3 consultas/dia atingido")
    
    if status['termos']:
        st.caption(f"📌 Termos: {', '.join(status['termos'])}")
    
    st.markdown("---")
    
    st.markdown("### 🔌 Status da API")
    if SERPAPI_KEY:
        st.success("✅ SerpApi configurada")
        st.caption("3 consultas automáticas/dia")
    else:
        st.warning("⚠️ SerpApi não configurada")
    
    st.markdown("---")
    
    st.markdown("### 📌 Como funciona")
    st.caption("1. Sugestões baseadas no mês atual")
    st.caption("2. 3 consultas automáticas na SerpApi")
    st.caption("3. Status visuais indicam oportunidade")

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

# Adiciona eventos aos itens
for item in dados_mes["tendencias"]:
    item["eventos"] = dados_mes["eventos"]

st.markdown(f"""
### 📊 Tendências para {datetime.now().strftime('%B').capitalize()}
**Eventos:** {', '.join(dados_mes['eventos'])} | **Sazonal:** {dados_mes['sazonal']}
""")

st.markdown("---")

# ============================================================
# ATUALIZA SUGESTOES COM SERPAPI (APENAS 3 POR DIA)
# ============================================================
with st.spinner("Atualizando sugestões com dados reais..."):
    sugestoes_atualizadas = atualizar_sugestoes_com_serpapi(dados_mes["tendencias"])

# ============================================================
# TABELA DE SUGESTOES COM STATUS VISUAIS
# ============================================================
st.markdown("### 🎯 Sugestões de Produtos para este Mês")

# Prepara dados para tabela
dados_tabela = []
for item in sugestoes_atualizadas:
    # Define cores baseadas no potencial
    if item["potencial"] == "Alto":
        status_display = "🟢 Excelente"
    elif item["potencial"] == "Médio":
        status_display = "🟡 Boa"
    else:
        status_display = "🟠 Média"
    
    # Formata resultados
    if item["total_resultados"] != "N/A":
        resultados_str = f"{item['total_resultados']} resultados"
    else:
        resultados_str = "Dados históricos"
    
    dados_tabela.append({
        "Status": status_display,
        "Produto": item["produto"],
        "Categoria": item["categoria"],
        "Evento": item["evento"],
        "Potencial": f"{item['status']} {item['potencial']}",
        "Resultados": resultados_str,
        "Ação": f"🔍 {item['produto']}"
    })

# Cria DataFrame
df_sugestoes = pd.DataFrame(dados_tabela)

# Exibe tabela com status visuais
st.dataframe(
    df_sugestoes,
    column_config={
        "Status": "Status",
        "Produto": "Produto",
        "Categoria": "Categoria",
        "Evento": "Evento Relacionado",
        "Potencial": "Potencial",
        "Resultados": "Resultados",
        "Ação": st.column_config.Column(
            "Buscar na Shopee",
            help="Clique para abrir a busca"
        )
    },
    use_container_width=True,
    hide_index=True
)

# Mostra status das consultas
status = controle_consultas.get_status()
st.caption(f"📊 {status['usadas']} de {status['limite']} consultas SerpApi usadas hoje")

st.markdown("---")

# ============================================================
# AREA DE BUSCA ESPECIFICA (CONSULTA MANUAL)
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
# LEGENDA
# ============================================================
st.markdown("### 📌 Legenda de Potencial")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🟢 **Excelente** - Baixa concorrência, alta demanda")
    st.caption("Produtos com menos de 50 resultados")

with col2:
    st.markdown("🟡 **Boa** - Concorrência moderada")
    st.caption("Produtos com 50-200 resultados")

with col3:
    st.markdown("🟠 **Média** - Mercado concorrido")
    st.caption("Produtos com mais de 200 resultados")

st.markdown("---")

# ============================================================
# DICAS E ESTRATEGIAS
# ============================================================
st.markdown("### 💡 Estratégias para Afiliados")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **📅 Datas Comemorativas**
    
    Aproveite os eventos do mês:
    - Posts sobre presentes
    - Vídeos de unboxing
    - Listas de 'O que comprar'
    """)

with col2:
    st.success("""
    **🎯 Foco nos Status 🟢**
    
    Produtos com status 🟢 Excelente:
    - Menor concorrência
    - Maior potencial de venda
    - Ideal para conteúdo novo
    """)

st.markdown("---")

# ============================================================
# RODAPE
# ============================================================
st.caption(f"🛒 Minerador de Produtos v2.0 | {status['usadas']}/3 consultas SerpApi hoje")
