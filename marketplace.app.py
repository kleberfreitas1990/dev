import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import json
import re

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide"
)

# ============================================================
# CONSTANTES
# ============================================================
CHAVE_TESTE = "TESTE-AFILIADO-2026"

# ============================================================
# CLASSE API MERCADO LIVRE
# ============================================================
class MercadoLivreAPI:
    def __init__(self):
        # ⚠️ ATUALIZE COM OS NOVOS TOKENS OBTIDOS ⚠️
        self.access_token = "APP_USR-1720081667983577-070322-d1ca9bcc48460cc957f49983536b39c7-28997765"
        self.refresh_token = "TG-6a4870c075af2a00015e6298-28997765"
        self.client_id = "1720081667983577"
        self.client_secret = "js6wH9JpaPoR3rlgLFvqLBaXt6EHyoVd"  # ATUALIZE COM A NOVA CHAVE
    
    def renovar_token(self):
        """Renova o Access Token usando o Refresh Token"""
        url = "https://api.mercadolibre.com/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        try:
            resp = requests.post(url, data=payload, timeout=10)
            data = resp.json()
            if "access_token" in data:
                self.access_token = data["access_token"]
                st.success("✅ Token renovado com sucesso!")
                return True
            else:
                st.error(f"Erro ao renovar token: {data}")
                return False
        except Exception as e:
            st.error(f"Erro na renovação: {e}")
            return False
    
    def buscar_produtos(self, termo, limite=5):
        """Busca produtos no Mercado Livre com autenticação"""
        try:
            url = "https://api.mercadolibre.com/sites/MLB/search"
            params = {
                "q": termo,
                "limit": limite,
                "condition": "new"
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            
            # Se token expirou, tenta renovar
            if resp.status_code == 401:
                st.warning("⏳ Token expirado. Renovando...")
                if self.renovar_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    resp = requests.get(url, params=params, headers=headers, timeout=10)
            
            resp.raise_for_status()
            data = resp.json()
            
            produtos = []
            for item in data.get("results", [])[:limite]:
                produtos.append({
                    "nome": item.get("title", ""),
                    "preco": f"R$ {item.get('price', 0):.2f}",
                    "vendas": item.get("sold_quantity", 0),
                    "link": item.get("permalink", ""),
                    "imagem": item.get("thumbnail", ""),
                    "loja": "Mercado Livre"
                })
            return produtos
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                st.error("🚫 Erro 403: Acesso negado. Verifique as permissões do token.")
            elif e.response.status_code == 429:
                st.error("⏳ Muitas requisições. Aguarde um momento e tente novamente.")
            else:
                st.error(f"Erro HTTP: {e}")
            return []
        except Exception as e:
            st.error(f"Erro na busca ML: {e}")
            return []
    
    def buscar_total_resultados(self, termo):
        """Busca total de resultados para um termo no Mercado Livre"""
        try:
            url = "https://api.mercadolibre.com/sites/MLB/search"
            params = {
                "q": termo,
                "limit": 1,
                "condition": "new"
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            
            if resp.status_code == 401:
                if self.renovar_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    resp = requests.get(url, params=params, headers=headers, timeout=10)
            
            resp.raise_for_status()
            data = resp.json()
            return data.get("paging", {}).get("total", 0)
        except Exception as e:
            return 0

# ============================================================
# INSTANCIA A API
# ============================================================
ml_api = MercadoLivreAPI()

# ============================================================
# DADOS HISTÓRICOS
# ============================================================
DADOS_HISTORICOS_COMPLETOS = {
    1: {
        "tendencias": ["smartwatch", "fone bluetooth", "material escolar", "mochila", "tênis"],
        "pinterest": ["decoração ano novo", "organização", "looks verão"],
        "google": ["smartwatch", "fone", "caderno", "mochila"],
        "sazonais": ["✏️ Material Escolar", "🎯 Smartwatch", "🏃 Tênis"],
        "volume_base": {"smartwatch": 150, "fone bluetooth": 200, "material escolar": 300}
    },
    2: {
        "tendencias": ["fantasia", "biquíni", "sungas", "protetor solar", "fone"],
        "pinterest": ["fantasia carnaval", "looks praia", "maquiagem colorida"],
        "google": ["fantasia", "biquíni", "chinelo", "protetor"],
        "sazonais": ["🎭 Fantasias", "🏖️ Moda Praia", "☀️ Protetor Solar"],
        "volume_base": {"fantasia": 250, "biquíni": 180, "protetor solar": 120}
    },
    3: {
        "tendencias": ["kit praia", "canga", "chapéu", "óculos sol", "smartwatch"],
        "pinterest": ["looks outono", "decoração Páscoa", "jardinagem"],
        "google": ["canga", "chapéu", "óculos", "smartwatch"],
        "sazonais": ["🏖️ Kit Praia", "🎯 Smartwatch", "👒 Chapéu"],
        "volume_base": {"kit praia": 200, "canga": 150, "chapéu": 100}
    },
    4: {
        "tendencias": ["ovo páscoa", "chocolate", "cesta", "fone", "smartwatch"],
        "pinterest": ["decoração Páscoa", "receitas", "ovos decorados"],
        "google": ["ovo páscoa", "chocolate", "cesta", "fone"],
        "sazonais": ["🐣 Ovo Páscoa", "🍫 Chocolate", "🧺 Cesta"],
        "volume_base": {"ovo páscoa": 400, "chocolate": 250, "cesta": 180}
    },
    5: {
        "tendencias": ["dia das mães", "perfume", "bolsa", "vestido", "smartwatch"],
        "pinterest": ["presentes mães", "DIY", "flores", "looks outono"],
        "google": ["dia das mães", "perfume", "bolsa", "vestido"],
        "sazonais": ["👩 Dia das Mães", "💐 Flores", "🎁 Presentes"],
        "volume_base": {"dia das mães": 500, "perfume": 200, "bolsa": 150}
    },
    6: {
        "tendencias": ["dia dos namorados", "perfume", "vinho", "chocolate", "fone"],
        "pinterest": ["presentes românticos", "jantar", "looks", "viagem"],
        "google": ["dia dos namorados", "perfume", "vinho", "chocolate"],
        "sazonais": ["💝 Dia dos Namorados", "🍷 Vinho", "🎧 Fone"],
        "volume_base": {"dia dos namorados": 450, "perfume": 180, "vinho": 120}
    },
    7: {
        "tendencias": ["casaco", "bota", "cachecol", "fone", "smartwatch"],
        "pinterest": ["looks inverno", "decoração", "viagem", "conforto"],
        "google": ["casaco", "bota", "cachecol", "fone"],
        "sazonais": ["🧥 Casaco", "👢 Bota", "🧣 Cachecol"],
        "volume_base": {"casaco": 300, "bota": 200, "cachecol": 120}
    },
    8: {
        "tendencias": ["dia dos pais", "relógio", "cinto", "ferramenta", "smartwatch"],
        "pinterest": ["presentes pais", "DIY", "volta aulas", "decoração"],
        "google": ["dia dos pais", "relógio", "cinto", "ferramenta"],
        "sazonais": ["👨 Dia dos Pais", "⌚ Relógio", "🔧 Ferramenta"],
        "volume_base": {"dia dos pais": 400, "relógio": 180, "ferramenta": 150}
    },
    9: {
        "tendencias": ["camisa", "calça", "vestido", "tênis", "smartwatch"],
        "pinterest": ["looks primavera", "decoração", "jardinagem", "viagens"],
        "google": ["camisa", "calça", "vestido", "tênis"],
        "sazonais": ["🌸 Moda Primavera", "👕 Camisa", "👟 Tênis"],
        "volume_base": {"camisa": 200, "calça": 180, "vestido": 160}
    },
    10: {
        "tendencias": ["fantasia halloween", "decoração", "brinquedo", "fone", "smartwatch"],
        "pinterest": ["fantasia halloween", "decoração", "maquiagem", "receitas"],
        "google": ["halloween", "fantasia", "decoração", "brinquedo"],
        "sazonais": ["🎃 Halloween", "🧙 Fantasia", "🕷️ Decoração"],
        "volume_base": {"fantasia halloween": 350, "decoração": 200, "brinquedo": 180}
    },
    11: {
        "tendencias": ["black friday", "eletrônico", "celular", "tv", "smartwatch"],
        "pinterest": ["ideias presentes", "decoração natal", "receitas", "black friday"],
        "google": ["black friday", "eletrônico", "celular", "tv"],
        "sazonais": ["🛒 Black Friday", "📱 Eletrônicos", "🎄 Natal"],
        "volume_base": {"black friday": 800, "eletrônico": 300, "smartwatch": 250}
    },
    12: {
        "tendencias": ["natal", "presente", "árvore", "decoração", "smartwatch"],
        "pinterest": ["decoração natal", "presentes", "receitas", "réveillon"],
        "google": ["natal", "presente", "árvore", "decoração"],
        "sazonais": ["🎄 Natal", "🎁 Presentes", "✨ Decoração"],
        "volume_base": {"natal": 600, "presente": 400, "decoração": 250}
    }
}

DATAS_COMEMORATIVAS = {
    (1, 1): "Ano Novo",
    (2, 14): "Carnaval (período)",
    (3, 8): "Dia da Mulher",
    (3, 20): "Início do Outono",
    (4, 1): "Páscoa (período)",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (5, 11): "Dia das Mães",
    (6, 12): "Dia dos Namorados",
    (6, 24): "Festa Junina / São João",
    (7, 9): "Férias Escolares de Julho",
    (8, 10): "Dia dos Pais",
    (8, 22): "Volta às Aulas (2º semestre)",
    (9, 7): "Independência do Brasil",
    (9, 23): "Início da Primavera",
    (10, 12): "Dia das Crianças",
    (10, 31): "Halloween",
    (11, 2): "Finados",
    (11, 28): "Black Friday (período)",
    (12, 1): "Cyber Monday (período)",
    (12, 25): "Natal",
    (12, 31): "Réveillon",
}

CATEGORIAS_TERMOS = {
    "smartwatch": "Eletrônicos",
    "fone bluetooth": "Eletrônicos",
    "caixa de som": "Eletrônicos",
    "carregador portátil": "Eletrônicos",
    "camisa": "Moda",
    "vestido": "Moda",
    "tênis": "Moda",
    "bolsa": "Moda",
    "mochila": "Moda",
    "cadeira gamer": "Casa",
}

# ============================================================
# FUNÇÕES DE ANÁLISE
# ============================================================
def analisar_saturacao(total):
    if total == 0:
        return {"nivel": "Sem dados", "recomendacao": "Nenhum produto encontrado"}
    elif total < 50:
        return {"nivel": "🟢 Baixa Saturação", "recomendacao": "Ótimo! Pouca concorrência. Aproveite!"}
    elif total < 200:
        return {"nivel": "🟡 Saturação Moderada", "recomendacao": "Concorrência razoável. Ainda há espaço."}
    elif total < 500:
        return {"nivel": "🟠 Saturação Alta", "recomendacao": "Mercado concorrido. Foque em nichos específicos."}
    else:
        return {"nivel": "🔴 Saturação Muito Alta", "recomendacao": "Mercado saturado. Busque variações menos competitivas."}

def calcular_score_oportunidade(total_resultados, media_vendas):
    if total_resultados <= 0:
        score_saturacao = 0
    else:
        score_saturacao = max(0, 6 - (total_resultados / 100))
    score_vendas = min(media_vendas / 20, 4)
    return round(min(score_saturacao + score_vendas, 10), 1)

def analisar_produto_completo(termo, categoria):
    total_ml = ml_api.buscar_total_resultados(termo)
    produtos_ml = ml_api.buscar_produtos(termo, 5)
    
    vendas = [p.get("vendas", 0) for p in produtos_ml if p.get("vendas", 0) > 0]
    media_vendas = (sum(vendas) / len(vendas)) if vendas else 0
    
    saturacao_pct = min(round((total_ml / 500) * 100, 1), 100) if total_ml else 0
    score = calcular_score_oportunidade(total_ml, media_vendas)
    
    return {
        "Produto": termo,
        "Categoria": categoria,
        "Score": score,
        "Saturação (%)": saturacao_pct,
        "Vendas Médias": round(media_vendas, 1),
        "Total Resultados": total_ml,
        "Recomendação": analisar_saturacao(total_ml)["recomendacao"]
    }

# ============================================================
# FUNÇÕES DE DATAS E SUGESTÕES
# ============================================================
def get_dados_historicos_mes(mes):
    return DADOS_HISTORICOS_COMPLETOS.get(mes, DADOS_HISTORICOS_COMPLETOS[1])

def verificar_data_comemorativa(mes, dia):
    hoje = date.today()
    proximo_evento = None
    menor_diff = None
    for (m, d), nome in DATAS_COMEMORATIVAS.items():
        try:
            data_evento = date(hoje.year, m, d)
        except ValueError:
            continue
        diff = (data_evento - hoje).days
        if 0 <= diff <= 7:
            if menor_diff is None or diff < menor_diff:
                menor_diff = diff
                proximo_evento = nome
    return proximo_evento

# ============================================================
# FUNÇÃO DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🔐 Minerador de Produtos - Login")
        chave = st.text_input("Digite sua chave de acesso:", type="password")
        if st.button("Entrar"):
            if chave == CHAVE_TESTE:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Chave inválida. Tente novamente.")
        st.stop()

# ============================================================
# FUNÇÃO BUSCAR SHOPEE (FALLBACK)
# ============================================================
def buscar_produtos_shopee(termo, limite=5):
    """Busca produtos na Shopee (pode ser bloqueado)"""
    try:
        url = "https://shopee.com.br/api/v4/search/search_items"
        params = {
            "by": "relevancy",
            "keyword": termo,
            "limit": limite,
            "newest": 0,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://shopee.com.br/search?keyword={quote(termo)}",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        produtos = []
        for item in data.get("items", [])[:limite]:
            info = item.get("item_basic", item)
            preco = info.get("price", 0) / 100000
            itemid = info.get("itemid")
            shopid = info.get("shopid")
            link = f"https://shopee.com.br/product/{shopid}/{itemid}" if itemid and shopid else ""
            produtos.append({
                "nome": info.get("name", ""),
                "preco": f"R$ {preco:.2f}",
                "vendas": info.get("historical_sold", info.get("sold", 0)),
                "link": link,
                "loja": "Shopee"
            })
        return produtos
    except Exception:
        return []

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

st.title("🛒 Minerador de Produtos - Afiliados")
st.caption("Análise de produtos com dados do Mercado Livre (autenticado) e Shopee")

# Status do token no sidebar
with st.sidebar:
    st.markdown("### 🔐 Status da API ML")
    st.success("✅ Token autenticado")
    st.caption(f"User ID: 28997765")
    st.caption("Expira em: 6 horas")
    st.caption(f"Refresh Token: {ml_api.refresh_token[:20] if ml_api.refresh_token else 'N/A'}...")
    
    st.markdown("---")
    if st.button("🔄 Renovar Token Manualmente"):
        if ml_api.renovar_token():
            st.success("Token renovado com sucesso!")
        else:
            st.error("Falha na renovação")

st.markdown("---")

# ===== SEÇÃO 1: BUSCAR PRODUTOS =====
st.markdown("## 🔍 Buscar Produtos no Mercado Livre")

termo_busca = st.text_input("🔍 Digite um produto:", placeholder="Ex: smartwatch, fone bluetooth...")

if termo_busca and st.button("📊 Buscar", type="primary"):
    with st.spinner(f"Buscando '{termo_busca}'..."):
        produtos = ml_api.buscar_produtos(termo_busca, 10)
        total = ml_api.buscar_total_resultados(termo_busca)
        saturacao = analisar_saturacao(total)
        
        st.markdown(f"### 📊 Resultados para '{termo_busca}'")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Resultados", total)
        with col2:
            st.metric("Produtos Exibidos", len(produtos))
        with col3:
            st.metric("Saturação", saturacao["nivel"])
        
        st.markdown("---")
        st.markdown(f"💡 {saturacao['recomendacao']}")
        
        if produtos:
            st.markdown("---")
            st.markdown("### 🛒 Produtos Encontrados")
            for p in produtos[:5]:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{p.get('nome', '')[:80]}**")
                        st.markdown(f"💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                    with c2:
                        if p.get("link"):
                            st.link_button("🔗 Ver", p["link"], use_container_width=True)

st.markdown("---")

# ===== SEÇÃO 2: ANÁLISE DE SATURAÇÃO =====
st.markdown("## 🎯 Análise de Saturação")

with st.expander("🔍 O que é a Análise de Saturação?"):
    st.markdown("""
    A análise de saturação mede a concorrência para um produto no Mercado Livre.
    Quanto menor o número de resultados, **menor a concorrência** e **melhor a oportunidade**.
    
    - 🟢 **Baixa Saturação** (< 50 resultados) → Ótima oportunidade
    - 🟡 **Moderada** (50-200 resultados) → Concorrência razoável
    - 🟠 **Alta** (200-500 resultados) → Mercado concorrido
    - 🔴 **Muito Alta** (> 500 resultados) → Mercado saturado
    """)

termo_sat = st.text_input("🔍 Digite um produto para analisar saturação:", placeholder="Ex: smartwatch, fone bluetooth...", key="sat")

if termo_sat and st.button("📊 Analisar Saturação", key="btn_sat"):
    with st.spinner(f"Analisando '{termo_sat}'..."):
        total = ml_api.buscar_total_resultados(termo_sat)
        produtos = ml_api.buscar_produtos(termo_sat, 3)
        saturacao = analisar_saturacao(total)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Resultados", total)
        with col2:
            st.metric("Status", saturacao["nivel"])
        
        st.markdown(f"💡 {saturacao['recomendacao']}")
        
        if produtos:
            st.markdown("---")
            st.markdown("#### 📦 Primeiros produtos encontrados:")
            for p in produtos[:3]:
                st.markdown(f"- **{p.get('nome', '')[:50]}** - 💰 {p.get('preco', '')}")

st.markdown("---")

# ===== SEÇÃO 3: SUGESTÕES POR DATA =====
st.markdown("## 📅 Sugestões por Data")

mes_atual = datetime.now().month
dados_mes = get_dados_historicos_mes(mes_atual)
evento = verificar_data_comemorativa(datetime.now().month, datetime.now().day)

if evento:
    st.success(f"🎉 Data comemorativa próxima: **{evento}**")
else:
    st.info("Nenhuma data comemorativa nos próximos 7 dias.")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🛒 Em Alta no ML**")
    for t in dados_mes.get("tendencias", [])[:4]:
        st.markdown(f"- {t}")

with col2:
    st.markdown("**📌 Pinterest**")
    for t in dados_mes.get("pinterest", [])[:4]:
        st.markdown(f"- {t}")

with col3:
    st.markdown("**🔍 Google Trends**")
    for t in dados_mes.get("google", [])[:4]:
        st.markdown(f"- {t}")

st.markdown("---")
st.markdown("#### 🎯 Produtos Sazonais em Destaque")
for s in dados_mes.get("sazonais", []):
    st.markdown(f"- {s}")

st.markdown("---")

# ===== SEÇÃO 4: MINERADOR PRO =====
st.markdown("## 🛍️ Minerador Pro - Oportunidades para Afiliados")

if st.button("🚀 Analisar Oportunidades", type="primary"):
    with st.spinner("Analisando produtos..."):
        resultados = [
            analisar_produto_completo(termo, categoria)
            for termo, categoria in CATEGORIAS_TERMOS.items()
        ]
        df = pd.DataFrame(resultados).sort_values("Score", ascending=False).reset_index(drop=True)
        
        st.markdown("### 📊 Oportunidades por Score")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 💡 Estratégia para Afiliados")
        col1, col2 = st.columns(2)
        with col1:
            st.success(
                "**🎯 Oportunidades Excelentes (Score ≥ 8)**\n\n"
                "- ✅ Baixa concorrência\n"
                "- ✅ Produto já validado\n"
                "- ✅ Boa margem para conteúdo\n\n"
                "**Ação:** crie conteúdo com urgência!"
            )
        with col2:
            st.info(
                "**⭐ Boas Oportunidades (Score ≥ 6)**\n\n"
                "- ⚠️ Concorrência moderada\n"
                "- 📈 Produto com potencial\n\n"
                "**Ação:** analise a concorrência e crie conteúdo diferenciado"
            )

st.markdown("---")

# ===== SEÇÃO 5: SHOPEE (FALLBACK) =====
with st.expander("🛍️ Buscar na Shopee (fallback)"):
    st.caption("A Shopee não tem API pública, pode falhar")
    termo_shopee = st.text_input("🔍 Digite um produto para buscar na Shopee:", key="shopee")
    
    if termo_shopee and st.button("🔍 Buscar Shopee"):
        with st.spinner(f"Buscando '{termo_shopee}' na Shopee..."):
            produtos = buscar_produtos_shopee(termo_shopee, 5)
            if produtos:
                for p in produtos:
                    st.markdown(f"- **{p.get('nome', '')[:50]}** - 💰 {p.get('preco', '')}")
            else:
                st.warning("Nenhum produto encontrado ou Shopee bloqueou a requisição.")
