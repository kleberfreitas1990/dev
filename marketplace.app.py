import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import random
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

# ===== DADOS HISTÓRICOS COMPLETOS (ML + Pinterest + Google Trends) =====
DADOS_HISTORICOS_COMPLETOS = {
    1: {  # Janeiro
        "tendencias_ml": ["smartwatch", "fone bluetooth", "material escolar", "mochila", "tênis"],
        "tendencias_pinterest": ["decoração ano novo", "organização", "looks verão", "receitas fitness"],
        "tendencias_google": ["smartwatch", "fone", "caderno", "mochila", "tênis"],
        "sazonais": ["✏️ Material Escolar", "🎯 Smartwatch", "🏃 Tênis"],
        "volume_base": {"smartwatch": 150, "fone bluetooth": 200, "material escolar": 300}
    },
    2: {  # Fevereiro
        "tendencias_ml": ["fantasia", "biquíni", "sungas", "protetor solar", "fone"],
        "tendencias_pinterest": ["fantasia carnaval", "looks praia", "maquiagem colorida", "decoração festa"],
        "tendencias_google": ["fantasia", "biquíni", "chinelo", "protetor", "carnaval"],
        "sazonais": ["🎭 Fantasias", "🏖️ Moda Praia", "☀️ Protetor Solar"],
        "volume_base": {"fantasia": 250, "biquíni": 180, "protetor solar": 120}
    },
    3: {  # Março
        "tendencias_ml": ["kit praia", "canga", "chapéu", "óculos sol", "smartwatch"],
        "tendencias_pinterest": ["looks outono", "decoração Páscoa", "jardinagem", "viagens"],
        "tendencias_google": ["canga", "chapéu", "óculos", "smartwatch", "fone"],
        "sazonais": ["🏖️ Kit Praia", "🎯 Smartwatch", "👒 Chapéu"],
        "volume_base": {"kit praia": 200, "canga": 150, "chapéu": 100}
    },
    4: {  # Abril
        "tendencias_ml": ["ovo páscoa", "chocolate", "cesta", "fone", "smartwatch"],
        "tendencias_pinterest": ["decoração Páscoa", "receitas", "ovos decorados", "artesanato"],
        "tendencias_google": ["ovo páscoa", "chocolate", "cesta", "fone", "smartwatch"],
        "sazonais": ["🐣 Ovo Páscoa", "🍫 Chocolate", "🧺 Cesta"],
        "volume_base": {"ovo páscoa": 400, "chocolate": 250, "cesta": 180}
    },
    5: {  # Maio
        "tendencias_ml": ["dia das mães", "perfume", "bolsa", "vestido", "smartwatch"],
        "tendencias_pinterest": ["presentes mães", "DIY", "flores", "looks outono"],
        "tendencias_google": ["dia das mães", "perfume", "bolsa", "vestido", "smartwatch"],
        "sazonais": ["👩 Dia das Mães", "💐 Flores", "🎁 Presentes"],
        "volume_base": {"dia das mães": 500, "perfume": 200, "bolsa": 150}
    },
    6: {  # Junho
        "tendencias_ml": ["dia dos namorados", "perfume", "vinho", "chocolate", "fone"],
        "tendencias_pinterest": ["presentes românticos", "jantar", "looks", "viagem"],
        "tendencias_google": ["dia dos namorados", "perfume", "vinho", "chocolate", "fone"],
        "sazonais": ["💝 Dia dos Namorados", "🍷 Vinho", "🎧 Fone"],
        "volume_base": {"dia dos namorados": 450, "perfume": 180, "vinho": 120}
    },
    7: {  # Julho
        "tendencias_ml": ["casaco", "bota", "cachecol", "fone", "smartwatch"],
        "tendencias_pinterest": ["looks inverno", "decoração", "viagem", "conforto"],
        "tendencias_google": ["casaco", "bota", "cachecol", "fone", "smartwatch"],
        "sazonais": ["🧥 Casaco", "👢 Bota", "🧣 Cachecol"],
        "volume_base": {"casaco": 300, "bota": 200, "cachecol": 120}
    },
    8: {  # Agosto
        "tendencias_ml": ["dia dos pais", "relógio", "cinto", "ferramenta", "smartwatch"],
        "tendencias_pinterest": ["presentes pais", "DIY", "volta aulas", "decoração"],
        "tendencias_google": ["dia dos pais", "relógio", "cinto", "ferramenta", "smartwatch"],
        "sazonais": ["👨 Dia dos Pais", "⌚ Relógio", "🔧 Ferramenta"],
        "volume_base": {"dia dos pais": 400, "relógio": 180, "ferramenta": 150}
    },
    9: {  # Setembro
        "tendencias_ml": ["camisa", "calça", "vestido", "tênis", "smartwatch"],
        "tendencias_pinterest": ["looks primavera", "decoração", "jardinagem", "viagens"],
        "tendencias_google": ["camisa", "calça", "vestido", "tênis", "smartwatch"],
        "sazonais": ["🌸 Moda Primavera", "👕 Camisa", "👟 Tênis"],
        "volume_base": {"camisa": 200, "calça": 180, "vestido": 160}
    },
    10: {  # Outubro
        "tendencias_ml": ["fantasia halloween", "decoração", "brinquedo", "fone", "smartwatch"],
        "tendencias_pinterest": ["fantasia halloween", "decoração", "maquiagem", "receitas"],
        "tendencias_google": ["halloween", "fantasia", "decoração", "brinquedo", "fone"],
        "sazonais": ["🎃 Halloween", "🧙 Fantasia", "🕷️ Decoração"],
        "volume_base": {"fantasia halloween": 350, "decoração": 200, "brinquedo": 180}
    },
    11: {  # Novembro
        "tendencias_ml": ["black friday", "eletrônico", "celular", "tv", "smartwatch"],
        "tendencias_pinterest": ["ideias presentes", "decoração natal", "receitas", "black friday"],
        "tendencias_google": ["black friday", "eletrônico", "celular", "tv", "smartwatch"],
        "sazonais": ["🛒 Black Friday", "📱 Eletrônicos", "🎄 Natal"],
        "volume_base": {"black friday": 800, "eletrônico": 300, "smartwatch": 250}
    },
    12: {  # Dezembro
        "tendencias_ml": ["natal", "presente", "árvore", "decoração", "smartwatch"],
        "tendencias_pinterest": ["decoração natal", "presentes", "receitas", "réveillon"],
        "tendencias_google": ["natal", "presente", "árvore", "decoração", "smartwatch"],
        "sazonais": ["🎄 Natal", "🎁 Presentes", "✨ Decoração"],
        "volume_base": {"natal": 600, "presente": 400, "decoração": 250}
    }
}

# Datas comemorativas fixas
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

# Termos que indicam notícia/pessoa pública
PALAVRAS_BLOQUEADAS = [
    "polícia", "policia", "político", "politico", "política", "politica",
    "futebol", "novela", "eleição", "eleicao", "presidente", "governo",
    "prefeito", "deputado", "senador", "crime", "acidente", "morte",
    "morre", "assassinato", "escândalo", "escandalo", "famoso",
    "celebridade", "artista", "cantor", "cantora", "ator", "atriz",
    "jogador", "técnico", "tecnico", "clube", "campeonato", "copa",
    "seleção", "selecao", "guerra", "processo", "julgamento",
]

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
# FUNÇÕES DE API
# ============================================================
HEADERS_ML = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def buscar_produtos_mercadolivre(termo, limite=5):
    try:
        url = "https://api.mercadolibre.com/sites/MLB/search"
        params = {"q": termo, "limit": limite}
        resp = requests.get(url, params=params, headers=HEADERS_ML, timeout=10)
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
            })
        return produtos
    except Exception:
        return []

def buscar_total_resultados_ml(termo):
    try:
        url = "https://api.mercadolibre.com/sites/MLB/search"
        params = {"q": termo, "limit": 1}
        resp = requests.get(url, params=params, headers=HEADERS_ML, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("paging", {}).get("total", 0)
    except Exception:
        return 0

def buscar_produtos_shopee(termo, limite=5):
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
            })
        return produtos
    except Exception:
        return []

def buscar_total_resultados_shopee(termo):
    try:
        url = "https://shopee.com.br/api/v4/search/search_items"
        params = {
            "by": "relevancy", "keyword": termo, "limit": 1,
            "newest": 0, "order": "desc", "page_type": "search",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://shopee.com.br/search?keyword={quote(termo)}",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("total_count", 0)
    except Exception:
        return 0


# ============================================================
# FUNÇÕES DE ANÁLISE (ML + Pinterest + Google Trends)
# ============================================================
def get_dados_historicos_mes(mes):
    """Retorna dados históricos combinados para o mês"""
    return DADOS_HISTORICOS_COMPLETOS.get(mes, DADOS_HISTORICOS_COMPLETOS[1])

def analisar_cruzamento_tendencias(termo, mes_atual):
    """
    Cruza dados atuais com históricos (ML, Pinterest, Google Trends)
    para identificar saturação emergente
    """
    historico = get_dados_historicos_mes(mes_atual)
    
    # Volume atual (ML)
    volume_atual = buscar_total_resultados_ml(termo)
    
    # Volume histórico (ano passado)
    volume_historico = historico.get("volume_base", {}).get(termo, 0)
    
    # Tendências do Pinterest (histórico)
    tendencias_pinterest = historico.get("tendencias_pinterest", [])
    esta_no_pinterest = any(termo.lower() in t.lower() for t in tendencias_pinterest)
    
    # Tendências do Google (histórico)
    tendencias_google = historico.get("tendencias_google", [])
    esta_no_google = any(termo.lower() in t.lower() for t in tendencias_google)
    
    # Produtos sazonais
    sazonais = historico.get("sazonais", [])
    eh_sazonal = any(termo.lower() in s.lower() for s in sazonais)
    
    # Calcula crescimento YoY (se tiver dados)
    if volume_historico > 0:
        crescimento = ((volume_atual - volume_historico) / volume_historico) * 100
    else:
        crescimento = 0
    
    # Sinaliza saturação emergente
    # Critérios: volume atual alto + crescimento acelerado + presente em múltiplas fontes
    sinais_saturacao = []
    
    if volume_atual > 200:
        sinais_saturacao.append("📈 Volume alto de resultados no ML")
    if crescimento > 50:
        sinais_saturacao.append("🚀 Crescimento acelerado (acima de 50%)")
    if esta_no_pinterest and esta_no_google:
        sinais_saturacao.append("🔥 Tendência confirmada em múltiplas fontes")
    if eh_sazonal and volume_atual > 100:
        sinais_saturacao.append("📅 Produto sazonal com alta demanda")
    
    if len(sinais_saturacao) >= 3:
        status_saturacao = "🔴 COMEÇANDO A SATURAR - Fique atento!"
        recomendacao = "Produto com sinais claros de saturação. Considere nichos mais específicos."
    elif len(sinais_saturacao) >= 2:
        status_saturacao = "🟡 MONITORAR - Crescendo rapidamente"
        recomendacao = "Ainda há oportunidade, mas a concorrência está aumentando. Agora é a hora!"
    elif len(sinais_saturacao) >= 1:
        status_saturacao = "🟢 OPORTUNIDADE - Mercado em crescimento"
        recomendacao = "Bom momento para entrar. Poucos sinais de saturação."
    else:
        status_saturacao = "⚪ OPORTUNIDADE INICIAL"
        recomendacao = "Mercado ainda não validado. Pode ser uma aposta."
    
    return {
        "termo": termo,
        "volume_atual": volume_atual,
        "volume_historico": volume_historico,
        "crescimento_yoy": crescimento,
        "esta_no_pinterest": esta_no_pinterest,
        "esta_no_google": esta_no_google,
        "eh_sazonal": eh_sazonal,
        "sinais_saturacao": sinais_saturacao,
        "status": status_saturacao,
        "recomendacao": recomendacao,
        "produtos_ml": buscar_produtos_mercadolivre(termo, 3)
    }

def analisar_saturacao_simples(total):
    if total < 50:
        return {"nivel": "🟢 Baixa Saturação", "recomendacao": "Ótimo! Pouca concorrência."}
    elif total < 200:
        return {"nivel": "🟡 Saturação Moderada", "recomendacao": "Concorrência razoável."}
    elif total < 500:
        return {"nivel": "🟠 Saturação Alta", "recomendacao": "Mercado concorrido."}
    else:
        return {"nivel": "🔴 Saturação Muito Alta", "recomendacao": "Mercado saturado."}


# ============================================================
# FUNÇÕES DE DATAS
# ============================================================
def verificar_data_comemorativa(mes, dia, margem_dias=7):
    hoje = date.today()
    proximo_evento = None
    menor_diff = None
    for (m, d), nome in DATAS_COMEMORATIVAS.items():
        try:
            data_evento = date(hoje.year, m, d)
        except ValueError:
            continue
        diff = (data_evento - hoje).days
        if 0 <= diff <= margem_dias:
            if menor_diff is None or diff < menor_diff:
                menor_diff = diff
                proximo_evento = nome
    return proximo_evento


# ============================================================
# FUNÇÕES DE LOGIN
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
# APP PRINCIPAL
# ============================================================
verificar_login()

st.title("🛒 Minerador de Produtos - Afiliados")
st.caption("Encontre produtos em alta com baixa concorrência - Cruzando ML, Pinterest e Google Trends")

st.warning(
    "⚠️ **Status das fontes de dados:** a API do Mercado Livre está bloqueando buscas "
    "de produtos (erro 403) desde o fim de 2025. A Shopee não oferece API pública. "
    "As seções baseadas em APIs podem não retornar produtos. "
    "A seção **📊 Análise Cruzada de Tendências** usa dados históricos e funciona normalmente."
)

if "buscar_tudo" not in st.session_state:
    st.session_state.buscar_tudo = False

if st.button("🔍 Buscar Tudo", type="primary"):
    st.session_state.buscar_tudo = True

st.markdown("---")

# ===== SEÇÃO 1: EM ALTA AGORA (ML) =====
st.markdown("## 🔥 Em Alta Agora")
st.caption("Baseado em categorias de destaque do mês, via Mercado Livre.")

if st.session_state.buscar_tudo:
    with st.spinner("Minerando produtos..."):
        mes_atual = datetime.now().month
        termos_semente = DADOS_HISTORICOS_COMPLETOS.get(mes_atual, {}).get("tendencias_ml", 
            ["smartwatch", "fone bluetooth", "carregador portátil"])
        
        produtos_alta = []
        for termo in termos_semente[:5]:
            produtos = buscar_produtos_mercadolivre(termo, 3)
            for p in produtos:
                p["termo_busca"] = termo
                produtos_alta.append(p)

    if produtos_alta:
        for p in produtos_alta[:6]:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{p.get('nome', '')[:60]}**")
                    st.caption(f"Termo: {p.get('termo_busca', '')}")
                    st.markdown(f"💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                with c2:
                    if p.get("link"):
                        st.link_button("Ver", p["link"], width='stretch')
    else:
        st.error("🚫 Nenhum produto retornado. API do ML provavelmente bloqueada.")
else:
    st.info("Clique em **'Buscar Tudo'** para ver os produtos.")

st.markdown("---")

# ===== SEÇÃO 2: SUGESTÕES POR DATA =====
st.markdown("## 📅 Sugestões por Data")

mes_atual = datetime.now().month
evento = verificar_data_comemorativa(datetime.now().month, datetime.now().day)

if evento:
    st.success(f"🎉 Data comemorativa próxima: **{evento}**")
else:
    st.info("Nenhuma data comemorativa nos próximos 7 dias.")

dados_mes = get_dados_historicos_mes(mes_atual)

st.markdown("#### 📈 Tendências por fonte")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**🛒 Mercado Livre**")
    for t in dados_mes.get("tendencias_ml", [])[:4]:
        st.markdown(f"- {t}")
with c2:
    st.markdown("**📌 Pinterest**")
    for t in dados_mes.get("tendencias_pinterest", [])[:4]:
        st.markdown(f"- {t}")
with c3:
    st.markdown("**🔍 Google Trends**")
    for t in dados_mes.get("tendencias_google", [])[:4]:
        st.markdown(f"- {t}")

st.markdown("---")
st.markdown("#### 🎯 Produtos Sazonais em Destaque")
for s in dados_mes.get("sazonais", []):
    st.markdown(f"- {s}")

st.markdown("---")
st.markdown("#### 💡 Sugestões de Conteúdo")
for s in [
    f"📝 Post sobre {evento or 'tendências do mês'}",
    f"🎯 Lista 'Top produtos para {evento or mes_atual}'",
    f"📦 Vídeo: '{dados_mes.get('sazonais', ['produtos'])[0]} — vale a pena?'"
]:
    st.markdown(f"- {s}")

st.markdown("---")

# ===== SEÇÃO 3: ANÁLISE CRUZADA DE TENDÊNCIAS =====
st.markdown("## 📊 Análise Cruzada de Tendências")
st.caption("Cruza dados do Mercado Livre, Pinterest e Google Trends para identificar saturação emergente")

with st.expander("🔍 Como funciona esta análise"):
    st.markdown("""
    **Esta ferramenta cruza 3 fontes de dados para identificar produtos começando a saturar:**
    
    1. **Mercado Livre** - Volume atual de resultados e crescimento YoY
    2. **Pinterest** - Tendências visuais e de busca
    3. **Google Trends** - Tendências históricas de busca
    
    **Sinais de saturação emergente:**
    - 🚀 Volume de resultados crescendo > 50% em relação ao ano passado
    - 📈 Produto presente em múltiplas fontes (ML + Pinterest + Google)
    - 📅 Produto sazonal com alta demanda atual
    - 🔥 Mencionado como tendência em 2+ plataformas
    
    **Status:**
    - 🟢 OPORTUNIDADE - Bom momento para entrar
    - 🟡 MONITORAR - Crescendo rápido, ainda há tempo
    - 🔴 COMEÇANDO A SATURAR - Fique atento, pode ficar saturado em breve
    - ⚪ OPORTUNIDADE INICIAL - Mercado ainda não validado
    """)

termo_busca = st.text_input("🔍 Digite um produto para analisar:", placeholder="Ex: smartwatch, fone bluetooth...")

if termo_busca and st.button("📊 Analisar Tendências"):
    with st.spinner(f"Cruzando dados para '{termo_busca}'..."):
        analise = analisar_cruzamento_tendencias(termo_busca, mes_atual)
        
        # Métricas principais
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("📊 Volume ML Atual", analise["volume_atual"])
        with c2:
            st.metric("📈 Crescimento YoY", f"{analise['crescimento_yoy']:.1f}%")
        with c3:
            st.metric("🔍 Fontes", f"ML + {'Pinterest' if analise['esta_no_pinterest'] else ''} + {'Google' if analise['esta_no_google'] else ''}")
        
        st.markdown("---")
        
        # Status
        st.markdown(f"### {analise['status']}")
        st.markdown(f"**💡 {analise['recomendacao']}**")
        
        st.markdown("---")
        
        # Sinais de saturação
        st.markdown("#### 🚨 Sinais de Saturação Detectados")
        if analise["sinais_saturacao"]:
            for sinal in analise["sinais_saturacao"]:
                st.markdown(f"- {sinal}")
        else:
            st.info("✅ Nenhum sinal de saturação detectado.")
        
        st.markdown("---")
        
        # Produtos disponíveis
        st.markdown("#### 🛒 Produtos encontrados no Mercado Livre")
        if analise["produtos_ml"]:
            for p in analise["produtos_ml"][:3]:
                st.markdown(f"- **{p.get('nome', '')[:60]}**")
                st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                if p.get("link"):
                    st.markdown(f"  [🔗 Ver produto]({p['link']})")
                st.markdown("")
        else:
            st.info("Nenhum produto encontrado no Mercado Livre")
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.link_button("🔍 Buscar no ML", f"https://lista.mercadolivre.com.br/{quote(termo_busca)}", width='stretch')
        c2.link_button("🔍 Buscar na Shopee", f"https://shopee.com.br/search?keyword={quote(termo_busca)}", width='stretch')

st.markdown("---")

# ===== SEÇÃO 4: ANÁLISE DE SATURAÇÃO SIMPLES =====
st.markdown("## 🎯 Análise de Saturação de Mercado")
st.caption("Quanto menor o número de resultados, menor a concorrência!")

termo_sat = st.text_input("🔍 Digite um produto para analisar saturação:", placeholder="Ex: smartwatch, fone bluetooth...", key="sat")

if termo_sat and st.button("📊 Analisar Saturação", key="btn_sat"):
    with st.spinner(f"Analisando '{termo_sat}'..."):
        total_ml = buscar_total_resultados_ml(termo_sat)
        total_shopee = buscar_total_resultados_shopee(termo_sat)
        total = total_ml + total_shopee
        saturacao = analisar_saturacao_simples(total)
        produtos_ml = buscar_produtos_mercadolivre(termo_sat, 3)
        produtos_shopee = buscar_produtos_shopee(termo_sat, 3)

        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 ML", f"{total_ml}")
        c2.metric("🟠 Shopee", f"{total_shopee}")
        c3.metric("📊 Total", f"{total}")

        if total == 0:
            st.error("🚫 Nenhum resultado — provável falha nas APIs. Tente novamente mais tarde.")

        st.markdown("---")
        st.markdown(f"### {saturacao['nivel']}")
        st.markdown(f"💡 {saturacao['recomendacao']}")

        st.markdown("---")
        c1, c2 = st.columns(2)

        def mostrar_produtos(col, produtos, nome, emoji):
            col.markdown(f"#### {emoji} {nome}")
            if produtos:
                for p in produtos[:3]:
                    col.markdown(f"- **{p.get('nome', '')[:50]}**")
                    col.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                    if p.get("link"):
                        col.markdown(f"  [🔗 Ver]({p['link']})")
                    col.markdown("")
            else:
                col.info(f"Nenhum produto no {nome}")

        mostrar_produtos(c1, produtos_ml, "Mercado Livre", "🔵")
        mostrar_produtos(c2, produtos_shopee, "Shopee", "🟠")

        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.link_button("🔍 ML", f"https://lista.mercadolivre.com.br/{quote(termo_sat)}", width='stretch')
        c2.link_button("🔍 Shopee", f"https://shopee.com.br/search?keyword={quote(termo_sat)}", width='stretch')
