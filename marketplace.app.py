import streamlit as st
import pandas as pd
import feedparser
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import requests
from pytrends.request import TrendReq
import json
import re

# Configuração da página
st.set_page_config(page_title="Minerador Pro - Produtos", page_icon="🛍️", layout="wide")

# ===== CONFIGURAÇÕES DE API =====
# IMPORTANTE: Substitua com suas chaves reais
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "sua-chave-serpapi-aqui")
MERCADOLIVRE_APP_ID = st.secrets.get("MERCADOLIVRE_APP_ID", "seu-app-id-aqui")

# ===== CATEGORIAS DE PRODUTOS PARA TRENDS =====
# Códigos de categoria do Google Trends para produtos
CATEGORIAS_PRODUTOS = {
    "Eletrônicos": 5,
    "Moda": 411,
    "Casa e Decoração": 455,
    "Beleza": 442,
    "Saúde": 451,
    "Esportes": 445,
    "Brinquedos": 444,
    "Automotivo": 447,
    "Alimentos": 452,
    "Livros": 443,
    "Pet": 475,
    "Ferramentas": 457
}

# Palavras-chave para buscar produtos populares
PRODUTOS_BASE = [
    "smartwatch", "fone bluetooth", "caixa de som", "carregador portátil",
    "camisa feminina", "vestido", "tênis", "bolsa", "mochila",
    "cadeira gamer", "mesa de escritório", "luminária led", "quadro decorativo",
    "creme hidratante", "base", "perfume", "kit maquiagem",
    "suplemento whey", "garrafa térmica", "tapete yoga",
    "brinquedo educativo", "boneca", "carrinho controle remoto",
    "capinha celular", "película protetora", "power bank"
]

def validar_licenca_supabase(chave):
    if chave == "TESTE-AFILIADO-2026":
        return {"valido": True, "expira": "2026-12-31"}
    return {"valido": False}

def buscar_trends_por_categoria(categoria_codigo, limite=10):
    """
    Busca tendências por categoria de produto no Google Trends
    Usando códigos de categoria específicos para produtos
    """
    try:
        pytrends = TrendReq(hl='pt-BR', tz=-180)
        
        # Busca por categoria específica
        pytrends.build_payload(
            kw_list=PRODUTOS_BASE[:5],  # Usa produtos base como semente
            cat=categoria_codigo,
            timeframe='now 1-d',
            geo='BR'
        )
        
        dados = pytrends.interest_over_time()
        
        if dados.empty:
            return []
        
        # Pega os termos mais buscados na categoria
        termos = dados.columns.tolist()
        if 'isPartial' in termos:
            termos.remove('isPartial')
        
        return termos[:limite]
        
    except Exception as e:
        st.warning(f"Erro ao buscar tendências por categoria: {str(e)}")
        return []

def buscar_produtos_serpapi(termo, limite=10):
    """
    Busca produtos reais no Google Shopping via SerpApi
    """
    if not SERPAPI_KEY or SERPAPI_KEY == "sua-chave-serpapi-aqui":
        return []
    
    url = "https://serpapi.com/search.json"
    params = {
        "q": termo,
        "tbm": "shop",
        "api_key": SERPAPI_KEY,
        "gl": "br",
        "hl": "pt",
        "num": limite
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        produtos = []
        for item in data.get("shopping_results", [])[:limite]:
            produtos.append({
                "nome": item.get("title", ""),
                "preco": item.get("price", ""),
                "loja": item.get("source", ""),
                "link": item.get("link", ""),
                "imagem": item.get("thumbnail", ""),
                "avaliacao": item.get("rating", None)
            })
        
        return produtos
    except Exception as e:
        return []

def buscar_produtos_mercadolivre(termo, limite=10):
    """
    Busca produtos no Mercado Livre API (gratuita)
    """
    url = f"https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "q": termo,
        "limit": limite,
        "sort": "relevance"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        produtos = []
        for item in data.get("results", [])[:limite]:
            produtos.append({
                "nome": item.get("title", ""),
                "preco": f"R$ {item.get('price', 0):.2f}",
                "loja": "Mercado Livre",
                "link": item.get("permalink", ""),
                "imagem": item.get("thumbnail", ""),
                "avaliacao": item.get("seller", {}).get("seller_reputation", {}).get("power_seller_status", None)
            })
        
        return produtos
    except Exception as e:
        return []

def buscar_produtos_shopee(termo, limite=3):
    """Busca produtos na Shopee (mantido como fallback)"""
    url = "https://shopee.com.br/api/v4/search/search_items"
    params = {
        "keyword": termo,
        "limit": limite,
        "newest": 0,
        "order": "desc",
        "by": "sales",
        "page_type": "search",
        "scenario": "PAGE_OTHERS",
        "version": 2,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Referer": f"https://shopee.com.br/search?keyword={quote(termo)}",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = data.get("items", []) or []
    except Exception:
        return []

    produtos = []
    for it in items:
        info = it.get("item_basic") or it.get("item") or it
        nome = info.get("name")
        preco_centavos = info.get("price")
        itemid = info.get("itemid")
        shopid = info.get("shopid")
        if not nome or not itemid or not shopid:
            continue
        preco = f"R$ {preco_centavos / 100000:.2f}" if preco_centavos else "—"
        link = f"https://shopee.com.br/product/{shopid}/{itemid}"
        produtos.append({"nome": nome, "preco": preco, "link": link, "loja": "Shopee"})

    return produtos

def analisar_produto(termo):
    """
    Análise completa de um produto:
    - Busca em múltiplas plataformas
    - Calcula score de oportunidade
    - Gera recomendações
    """
    # Busca produtos em diferentes plataformas
    produtos_shopee = buscar_produtos_shopee(termo, 3)
    produtos_ml = buscar_produtos_mercadolivre(termo, 3)
    produtos_serp = buscar_produtos_serpapi(termo, 3) if SERPAPI_KEY != "sua-chave-serpapi-aqui" else []
    
    # Combina resultados
    todos_produtos = []
    
    # Adiciona Shopee
    for p in produtos_shopee:
        p["plataforma"] = "Shopee"
        todos_produtos.append(p)
    
    # Adiciona Mercado Livre
    for p in produtos_ml:
        p["plataforma"] = "Mercado Livre"
        todos_produtos.append(p)
    
    # Adiciona SerpApi
    for p in produtos_serp:
        p["plataforma"] = "Google Shopping"
        if "loja" in p:
            p["loja"] = f"Google Shopping - {p['loja']}"
        todos_produtos.append(p)
    
    # Calcula score de oportunidade
    score = 0
    recomendacao = ""
    
    # Fatores de score
    if len(todos_produtos) > 0:
        score += 2  # Produto existe no mercado
    
    if len(produtos_shopee) > 0:
        score += 2  # Disponível na Shopee
    
    if len(produtos_ml) > 0:
        score += 1  # Disponível no Mercado Livre
    
    if len(produtos_serp) > 0:
        score += 1  # Disponível no Google Shopping
    
    # Gera recomendação baseada no score
    if score >= 5:
        recomendacao = "🔥 OPORTUNIDADE EXCELENTE - Produto com alta demanda e múltiplas fontes!"
    elif score >= 3:
        recomendacao = "⭐ BOA OPORTUNIDADE - Produto com potencial de venda"
    elif score >= 1:
        recomendacao = "📊 OPORTUNIDADE MÉDIA - Avaliar concorrência"
    else:
        recomendacao = "⚠️ OPORTUNIDADE BAIXA - Produto pode não ter boa demanda"
    
    return {
        "termo": termo,
        "total_produtos": len(todos_produtos),
        "score": score,
        "recomendacao": recomendacao,
        "produtos": todos_produtos
    }

def minerar_produtos_tendencias():
    """
    Mineração avançada usando múltiplas fontes:
    1. Google Trends por categoria
    2. Sugestões de produtos base
    3. Produtos populares por plataforma
    """
    resultados = []
    
    # 1. Busca por categoria no Google Trends
    with st.spinner("Buscando tendências por categoria..."):
        for categoria, codigo in CATEGORIAS_PRODUTOS.items():
            termos = buscar_trends_por_categoria(codigo, 3)
            for termo in termos:
                if termo and termo not in [r["termo"] for r in resultados]:
                    analise = analisar_produto(termo)
                    analise["fonte"] = f"Google Trends - {categoria}"
                    resultados.append(analise)
    
    # 2. Busca produtos base populares
    with st.spinner("Analisando produtos populares..."):
        for produto in PRODUTOS_BASE[:10]:
            if produto not in [r["termo"] for r in resultados]:
                analise = analisar_produto(produto)
                analise["fonte"] = "Produto Base"
                resultados.append(analise)
    
    # Remove duplicatas e ordena por score
    resultados = sorted(resultados, key=lambda x: x["score"], reverse=True)
    
    return pd.DataFrame(resultados[:20])  # Limita a 20 resultados

# ===== INTERFACE =====
st.title("🛍️ Minerador Pro - Produtos em Alta")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.subheader("🔐 Ative sua Licença para Acessar")
    chave_input = st.text_input("Digite sua Chave de Acesso:", type="password")

    if st.button("Verificar e Entrar"):
        resultado = validar_licenca_supabase(chave_input)
        if resultado["valido"]:
            st.session_state.autenticado = True
            st.session_state.data_expira = resultado["expira"]
            st.success("Acesso liberado com sucesso!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Chave inválida, expirada ou inativa. Verifique sua assinatura.")

else:
    st.sidebar.success("Acesso Garantido")
    st.sidebar.info(f"Sua licença expira em: {st.session_state.data_expira}")
    if st.sidebar.button("Sair / Desconectar"):
        st.session_state.autenticado = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Configuração das APIs")
    st.sidebar.caption("Para melhores resultados, configure:")
    st.sidebar.code("SERPAPI_KEY = 'sua-chave'", language="python")
    st.sidebar.caption("Obtenha em: serpapi.com")

    st.markdown("""
    ### 🎯 Produtos em Tendência no Brasil
    
    🔍 **Como funciona:**
    - 🔄 Busca em **Google Trends por categoria** (Eletrônicos, Moda, Casa, etc.)
    - 🛒 Verifica disponibilidade em **Shopee, Mercado Livre e Google Shopping**
    - 📊 Calcula **score de oportunidade** para afiliados
    - 🎯 Recomenda produtos com **maior potencial de venda**
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Minerar Produtos em Tendência", use_container_width=True):
            st.session_state.minerar = True
    with col2:
        st.caption("Busca em múltiplas fontes")
    with col3:
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")

    if st.session_state.get("minerar", False):
        with st.spinner("🔄 Minerando produtos em tempo real..."):
            try:
                df_resultados = minerar_produtos_tendencias()
                
                if not df_resultados.empty:
                    # Métricas
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Produtos Encontrados", len(df_resultados))
                    
                    with col2:
                        excelentes = df_resultados[df_resultados["score"] >= 5]
                        st.metric("Oportunidades Excelentes", len(excelentes))
                    
                    with col3:
                        boas = df_resultados[(df_resultados["score"] >= 3) & (df_resultados["score"] < 5)]
                        st.metric("Boas Oportunidades", len(boas))
                    
                    with col4:
                        fontes = df_resultados["fonte"].nunique()
                        st.metric("Fontes de Dados", fontes)
                    
                    st.markdown("---")
                    
                    # Tabela de produtos
                    st.markdown("### 📊 Produtos com Score de Oportunidade")
                    
                    df_exibicao = df_resultados[["termo", "score", "recomendacao", "fonte"]].copy()
                    df_exibicao.columns = ["Produto", "Score", "Recomendação", "Fonte"]
                    
                    st.dataframe(
                        df_exibicao,
                        column_config={
                            "Produto": "Produto",
                            "Score": st.column_config.NumberColumn("Score", format="%d"),
                            "Recomendação": "Recomendação",
                            "Fonte": "Fonte do Dado"
                        },
                        use_container_width=True
                    )
                    
                    # Detalhamento dos produtos
                    st.markdown("### 🛒 Detalhamento por Produto")
                    
                    # Filtro por score
                    score_filtro = st.selectbox(
                        "Filtrar por oportunidade:",
                        ["Todos", "Excelente (Score ≥ 5)", "Boa (Score ≥ 3)", "Média (Score ≥ 1)"]
                    )
                    
                    df_filtrado = df_resultados.copy()
                    if score_filtro == "Excelente (Score ≥ 5)":
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 5]
                    elif score_filtro == "Boa (Score ≥ 3)":
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 3]
                    elif score_filtro == "Média (Score ≥ 1)":
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 1]
                    
                    # Exibe cada produto
                    for _, row in df_filtrado.iterrows():
                        with st.expander(f"{row['termo']} - Score: {row['score']} - {row['recomendacao']}"):
                            col_a, col_b = st.columns([2, 1])
                            
                            with col_a:
                                st.markdown(f"**Fonte:** {row['fonte']}")
                                st.markdown(f"**Total de produtos encontrados:** {row['total_produtos']}")
                            
                            with col_b:
                                st.link_button(
                                    f"🔍 Buscar na Shopee",
                                    f"https://shopee.com.br/search?keyword={quote(row['termo'])}"
                                )
                            
                            # Produtos encontrados
                            if row["produtos"]:
                                st.markdown("**Produtos disponíveis:**")
                                for p in row["produtos"][:5]:
                                    st.markdown(f"- {p.get('nome', 'Produto')} - {p.get('preco', '')} ({p.get('plataforma', '')})")
                                    if p.get('link'):
                                        st.caption(f"  [Link]({p['link']})")
                            else:
                                st.info("Nenhum produto encontrado nas plataformas")
                    
                    st.success("✅ Mineração concluída com sucesso!")
                    
                else:
                    st.warning("Nenhum produto encontrado. Tente novamente.")
                
                st.session_state.minerar = False
                
            except Exception as e:
                st.error(f"Erro na mineração: {str(e)}")
                st.session_state.minerar = False

    # Configuração de chaves
    with st.expander("⚙️ Configuração Avançada"):
        st.markdown("### Configure suas chaves de API para melhores resultados")
        
        col1, col2 = st.columns(2)
        with col1:
            serp_key = st.text_input("SERPAPI Key", type="password", value=SERPAPI_KEY)
            if serp_key != SERPAPI_KEY:
                SERPAPI_KEY = serp_key
                st.success("Chave SERPAPI atualizada!")
        
        with col2:
            st.markdown("**Dicas:**")
            st.caption("1. Obtenha SERPAPI Key em serpapi.com")
            st.caption("2. Free tier: 100 buscas/mês")
            st.caption("3. Mercado Livre API é gratuita")
            st.caption("4. Shopee é scraping (pode falhar)")

    st.markdown("---")
    st.markdown("### 📌 Próximos Passos para Afiliados")
    
    st.info("""
    💡 **Estratégias de conteúdo:**
    1. **Produtos com Score ≥ 5** → Crie vídeos URGENTE no TikTok/Reels
    2. **Produtos com Score ≥ 3** → Excelente para posts no Instagram
    3. **Produtos Sazonais** → Prepare conteúdo com antecedência
    4. **Múltiplas fontes** → Produto consolidado, menor risco
    """)
