import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date

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

# Datas fixas aproximadas (datas móveis como Carnaval e Páscoa e os
# "domingos de" Dia das Mães/Pais usam uma data aproximada e podem
# precisar de ajuste manual ano a ano)
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

# Termos que indicam notícia/pessoa pública, não produto
PALAVRAS_BLOQUEADAS = [
    "polícia", "policia", "político", "politico", "política", "politica",
    "futebol", "novela", "eleição", "eleicao", "presidente", "governo",
    "prefeito", "deputado", "senador", "crime", "acidente", "morte",
    "morre", "assassinato", "escândalo", "escandalo", "famoso",
    "celebridade", "artista", "cantor", "cantora", "ator", "atriz",
    "jogador", "técnico", "tecnico", "clube", "campeonato", "copa",
    "seleção", "selecao", "guerra", "processo", "julgamento",
]

# Termos que reforçam que é produto
PALAVRAS_PRODUTO = [
    "comprar", "preço", "preco", "valor", "modelo", "tamanho", "cor",
    "marca", "promoção", "promocao", "desconto", "frete", "original",
    "novo", "usado", "kit", "conjunto", "unidade", "peça", "peca",
]

# Sugestões históricas de categorias/produtos por mês
HIST_POR_MES = {
    1: ["Material escolar", "Moda verão", "Protetor solar", "Ventilador portátil"],
    2: ["Fantasia de carnaval", "Roupa de praia", "Boia inflável", "Óculos de sol"],
    3: ["Casaco leve", "Bota outono", "Guarda-chuva", "Manta"],
    4: ["Cesta de páscoa", "Ovo de chocolate", "Fone de ouvido", "Carregador portátil"],
    5: ["Perfume", "Caneca personalizada", "Kit maquiagem", "Cartão presente"],
    6: ["Presente namorados", "Fogueira artificial", "Roupa xadrez", "Enfeite junino"],
    7: ["Casaco de frio", "Bota de inverno", "Cobertor", "Aquecedor portátil"],
    8: ["Presente para pais", "Churrasqueira portátil", "Mochila escolar", "Estojo"],
    9: ["Vaso de planta", "Roupa leve", "Tênis casual", "Óculos de sol"],
    10: ["Fantasia halloween", "Brinquedo infantil", "Livro infantil", "Doces"],
    11: ["Eletrônicos", "Eletrodomésticos", "Notebook", "Smart TV"],
    12: ["Enfeite de natal", "Presente amigo secreto", "Roupa de festa", "Espumante"],
}

# Termos padrão analisados no Minerador Pro, com categoria associada
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


def calcular_score_oportunidade(total_resultados, media_vendas):
    """Score de 0 a 10: até 6 pontos por baixa saturação + até 4 pontos por vendas médias."""
    if total_resultados <= 0:
        score_saturacao = 0
    else:
        score_saturacao = max(0, 6 - (total_resultados / 100))
    score_vendas = min(media_vendas / 20, 4)
    return round(min(score_saturacao + score_vendas, 10), 1)


def classificar_oportunidade(score):
    if score >= 8:
        return "🟢 OPORTUNIDADE EXCELENTE - Baixa concorrência e boa demanda"
    elif score >= 6:
        return "🟡 BOA OPORTUNIDADE - Vale a pena investir"
    elif score >= 3:
        return "🟠 OPORTUNIDADE MÉDIA - Analise com cautela"
    else:
        return "🔴 OPORTUNIDADE BAIXA - Muita concorrência ou pouca demanda"


def analisar_oportunidade_termo(termo, categoria):
    total_ml = buscar_total_resultados_ml(termo)
    produtos_ml = buscar_produtos_mercadolivre(termo, 5)
    vendas = [p.get("vendas", 0) for p in produtos_ml if p.get("vendas")]
    media_vendas = (sum(vendas) / len(vendas)) if vendas else 0
    saturacao_pct = min(round((total_ml / 500) * 100, 1), 100) if total_ml else 0
    score = calcular_score_oportunidade(total_ml, media_vendas)
    return {
        "Produto": termo,
        "Categoria": categoria,
        "Score": score,
        "Saturação (%)": saturacao_pct,
        "Vendas Médias": round(media_vendas, 1),
        "Recomendação": classificar_oportunidade(score),
    }


# ============================================================
# LOGIN
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
# APIs
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
    # A Shopee não oferece API pública oficial; este endpoint interno
    # pode mudar ou bloquear requisições sem navegador real a qualquer momento.
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
# ANÁLISE
# ============================================================
def analisar_saturacao(total):
    if total < 50:
        return {
            "nivel": "Baixa Saturação - Excelente Oportunidade",
            "recomendacao": "Poucos concorrentes! Ótimo momento para entrar neste nicho.",
        }
    elif total < 200:
        return {
            "nivel": "Saturação Moderada - Boa Oportunidade",
            "recomendacao": "Concorrência razoável, ainda há espaço para se destacar.",
        }
    elif total < 500:
        return {
            "nivel": "Saturação Alta - Oportunidade Média",
            "recomendacao": "Mercado concorrido. Aposte em nichos mais específicos (long-tail).",
        }
    else:
        return {
            "nivel": "Saturação Muito Alta - Baixa Oportunidade",
            "recomendacao": "Mercado saturado. Considere termos mais específicos ou outro produto.",
        }


def filtrar_termos_produtos(lista_termos):
    filtrados = []
    for termo in lista_termos:
        termo_lower = termo.lower()
        if any(palavra in termo_lower for palavra in PALAVRAS_BLOQUEADAS):
            continue
        filtrados.append(termo)
    return filtrados


def analisar_produto_completo(termo):
    total_ml = buscar_total_resultados_ml(termo)
    total_shopee = buscar_total_resultados_shopee(termo)
    total = total_ml + total_shopee
    saturacao = analisar_saturacao(total)
    produtos = buscar_produtos_mercadolivre(termo, 3)

    score = 0
    if total < 200:
        score += 3
    elif total < 500:
        score += 1

    if produtos:
        score += 2
        try:
            precos = [
                float(p["preco"].replace("R$ ", "").replace(",", "."))
                for p in produtos
            ]
            if precos and min(precos) < 200:
                score += 1
        except Exception:
            pass

    if any(p.get("vendas", 0) and p.get("vendas", 0) > 50 for p in produtos):
        score += 2

    return {
        "termo": termo,
        "score": min(score, 8),
        "saturacao": saturacao,
        "produtos": produtos,
    }


def minerar_produtos_em_alta(termos_semente=None, limite_por_termo=3):
    if termos_semente is None:
        mes_atual = datetime.now().month
        termos_semente = HIST_POR_MES.get(
            mes_atual, ["fone bluetooth", "smartwatch", "carregador portátil"]
        )
    resultados = []
    for termo in termos_semente:
        produtos = buscar_produtos_mercadolivre(termo, limite_por_termo)
        for p in produtos:
            p["termo_busca"] = termo
            resultados.append(p)
    return resultados


# ============================================================
# DATAS COMEMORATIVAS
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


def buscar_tendencias_por_periodo(mes, limite=6):
    return HIST_POR_MES.get(mes, [])[:limite]


def gerar_sugestoes_conteudo(evento, tendencias):
    sugestoes = []
    if evento:
        sugestoes.append(f"📝 Post especial sobre {evento}")
        sugestoes.append(f"🎯 Lista 'Top produtos para {evento}'")
    for t in tendencias[:3]:
        sugestoes.append(f"📦 Vídeo/Post: '{t} — vale a pena?'")
    return sugestoes


# ============================================================
# APP
# ============================================================
verificar_login()

st.title("🛒 Minerador de Produtos - Afiliados")
st.caption("Encontre produtos em alta com baixa concorrência")

st.warning(
    "⚠️ **Status das fontes de dados:** a API do Mercado Livre está bloqueando buscas "
    "de produtos (erro 403) desde o fim de 2025, mesmo com autenticação correta — isso "
    "é um problema do lado do Mercado Livre, relatado por diversos desenvolvedores, e não "
    "depende deste app. A Shopee também não oferece API pública oficial. Por isso, as seções "
    "**🔥 Em Alta Agora** e **🛍️ Minerador Pro** podem não retornar produtos no momento. "
    "A seção **📅 Sugestões por Data** não depende dessas APIs e funciona normalmente."
)

if "buscar_tudo" not in st.session_state:
    st.session_state.buscar_tudo = False

if st.button("🔍 Buscar Tudo", type="primary"):
    st.session_state.buscar_tudo = True

st.markdown("---")

# ===== SEÇÃO 1: EM ALTA AGORA =====
st.markdown("## 🔥 Em Alta Agora")
st.caption("Baseado em categorias de destaque do mês, via Mercado Livre.")

if st.session_state.buscar_tudo:
    with st.spinner("Minerando produtos..."):
        produtos_alta = minerar_produtos_em_alta()

    if produtos_alta:
        for p in produtos_alta:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{p.get('nome', '')}**")
                    st.caption(f"Termo: {p.get('termo_busca', '')}")
                    st.markdown(f"💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                with c2:
                    if p.get("link"):
                        st.link_button("Ver produto", p["link"], width='stretch')
    else:
        st.error(
            "🚫 Nenhum produto retornado. A API do Mercado Livre provavelmente está "
            "bloqueando a busca (erro 403) — problema externo, não deste app. "
            "Tente novamente mais tarde."
        )
else:
    st.info("Clique em **'Buscar Tudo'** para ver os produtos em alta.")

st.markdown("---")

# ===== SEÇÃO 2: SUGESTÕES POR DATA =====
st.markdown("## 📅 Sugestões por Data")

mes_atual = datetime.now().month
evento = verificar_data_comemorativa(datetime.now().month, datetime.now().day)

if evento:
    st.success(f"🎉 Data comemorativa próxima: **{evento}**")
else:
    st.info("Nenhuma data comemorativa nos próximos 7 dias.")

tendencias = buscar_tendencias_por_periodo(mes_atual)

st.markdown("#### 📈 Categorias em destaque este mês")
for t in tendencias:
    st.markdown(f"- {t}")

st.markdown("---")
st.markdown("#### 💡 Sugestões de conteúdo")
for s in gerar_sugestoes_conteudo(evento, tendencias):
    st.markdown(f"- {s}")

st.markdown("---")

# ===== SEÇÃO 3: ANÁLISE DE SATURAÇÃO =====
st.markdown("## 🎯 Análise de Saturação de Mercado")
st.caption("Quanto menor o número de resultados, menor a concorrência!")

termo_busca = st.text_input("🔍 Digite um produto:", placeholder="Ex: smartwatch, fone bluetooth...")

if termo_busca and st.button("📊 Analisar Saturação"):
    with st.spinner(f"Analisando '{termo_busca}'..."):
        total_ml = buscar_total_resultados_ml(termo_busca)
        total_shopee = buscar_total_resultados_shopee(termo_busca)
        total = total_ml + total_shopee
        saturacao = analisar_saturacao(total)
        produtos_ml = buscar_produtos_mercadolivre(termo_busca, 3)
        produtos_shopee = buscar_produtos_shopee(termo_busca, 3)

        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 ML", f"{total_ml}")
        c2.metric("🟠 Shopee", f"{total_shopee}")
        c3.metric("📊 Total", f"{total}")

        if total == 0:
            st.error(
                "🚫 Nenhum resultado em nenhuma das duas fontes — isso indica falha nas "
                "APIs (Mercado Livre bloqueando com erro 403, Shopee sem API pública), "
                "e **não que o produto não tem concorrência**. Tente novamente mais tarde."
            )

        st.markdown("---")

        cores = [
            (total < 50, st.success, "✅"),
            (total < 200, st.info, "📊"),
            (total < 500, st.warning, "⚠️"),
            (True, st.error, "🚨"),
        ]
        for cond, func, icon in cores:
            if cond:
                func(f"{icon} **{saturacao['nivel']}**")
                func(f"💡 {saturacao['recomendacao']}")
                break

        st.markdown("---")

        c1, c2 = st.columns(2)

        def mostrar_produtos(col, produtos, nome, emoji):
            col.markdown(f"#### {emoji} {nome}")
            if produtos:
                for p in produtos[:3]:
                    col.markdown(f"- **{p.get('nome', '')}**")
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
        c1.link_button("🔍 ML", f"https://lista.mercadolivre.com.br/{quote(termo_busca)}", width='stretch')
        c2.link_button("🔍 Shopee", f"https://shopee.com.br/search?keyword={quote(termo_busca)}", width='stretch')

st.markdown("---")

# ===== SEÇÃO 4: MINERADOR PRO =====
st.markdown("## 🛍️ Minerador Pro - Oportunidades para Afiliados")
st.markdown("### 🎯 Encontre Produtos com Baixa Concorrência e Alto Potencial")

with st.expander("🔍 Metodologia de Análise"):
    st.markdown("""
    - 🔵 Busca produtos e volume de resultados no **Mercado Livre**
    - 📊 Calcula a **saturação do mercado** (quanto menor, melhor)
    - 📈 Analisa a **média de vendas** dos produtos encontrados
    - ⭐ Gera um **Score de Oportunidade** combinando os dois fatores

    **O que significa cada métrica:**
    - **Score de Oportunidade**: de 0 a 10, quanto maior, melhor para afiliados
    - **Saturação (%)**: proporção de concorrência no Mercado Livre (menor = melhor)
    - **Vendas Médias**: quantidade média de vendas já registradas nos produtos encontrados
    - **Recomendação**: leitura consolidada do score

    ⚠️ *A Shopee não oferece API pública e costuma bloquear buscas automatizadas,
    por isso esta análise usa apenas dados do Mercado Livre — para não repetir o problema
    de métricas quebradas (100% de saturação, 0 vendas) quando a Shopee está indisponível.*
    """)

if st.session_state.buscar_tudo:
    with st.spinner("Analisando produtos..."):
        resultados = [
            analisar_oportunidade_termo(termo, categoria)
            for termo, categoria in CATEGORIAS_TERMOS.items()
        ]

    df = pd.DataFrame(resultados).sort_values("Score", ascending=False).reset_index(drop=True)

    # Se a API do ML estiver bloqueada, todo mundo volta com Score 0 e Saturação 0% —
    # isso não é uma leitura real de mercado, é ausência total de dados.
    todos_zerados = (df["Score"] == 0).all() and (df["Saturação (%)"] == 0).all()

    if todos_zerados:
        st.error(
            "🚫 Todos os produtos retornaram com Score 0 e Saturação 0% — isso indica que "
            "a API do Mercado Livre não retornou nenhum dado (provável bloqueio 403), e "
            "**não que o mercado está sem concorrência**. Tente novamente mais tarde."
        )
    else:
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 Produtos Analisados", len(df))
        c2.metric("🚀 Oportunidades Excelentes", int((df["Score"] >= 8).sum()))
        c3.metric("⭐ Boas Oportunidades", int(((df["Score"] >= 6) & (df["Score"] < 8)).sum()))
        c4.metric("🎯 Baixa Concorrência", int((df["Saturação (%)"] < 30).sum()))

        st.markdown("---")
        st.markdown("### 📊 Oportunidades por Score")
        st.dataframe(df, width='stretch', hide_index=True)

        st.markdown("---")
        st.markdown("### 💡 Estratégia para Afiliados")
        col1, col2 = st.columns(2)
        with col1:
            st.success(
                "**🎯 Oportunidades Excelentes (Score ≥ 8)**\n\n"
                "- ✅ Baixa concorrência\n"
                "- ✅ Produto já validado (vendas consistentes)\n"
                "- ✅ Boa margem para conteúdo de nicho\n\n"
                "**Ação:** crie conteúdo com urgência!"
            )
        with col2:
            st.info(
                "**⭐ Boas Oportunidades (Score ≥ 6)**\n\n"
                "- ⚠️ Concorrência moderada\n"
                "- 📈 Produto com potencial de crescimento\n\n"
                "**Ação:** analise a concorrência e crie conteúdo diferenciado"
            )

        st.success("✅ Análise concluída! Foque nos produtos com maior score e menor saturação.")

        st.markdown("---")
        st.markdown("### 📌 Dica: Como usar essa análise")
        st.info(
            "**Estratégia para maximizar suas vendas:**\n\n"
            "1. 🎯 Foque em produtos com Score ≥ 8 e baixa saturação\n"
            "2. 📈 Crie conteúdo mostrando o produto de forma autêntica\n"
            "3. 🔄 Teste diferentes produtos para ver qual converte melhor\n"
            "4. 🚀 Seja rápido — produtos com alto potencial atraem concorrentes rápido"
        )
else:
    st.info("Clique em **'Buscar Tudo'** para iniciar a análise do Minerador Pro.")
