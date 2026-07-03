import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import requests
import random

# Configuração da página
st.set_page_config(page_title="Minerador Pro - Produtos", page_icon="🛍️", layout="wide")

# ===== CONFIGURAÇÕES =====
# Categorias do Mercado Livre Brasil (MLB)
CATEGORIAS_ML = {
    "Eletrônicos": "MLB1000",
    "Moda": "MLB1430", 
    "Casa e Decoração": "MLB1574",
    "Beleza": "MLB1246",
    "Esportes": "MLB1384",
    "Brinquedos": "MLB1384",
    "Automotivo": "MLB1743",
    "Ferramentas": "MLB1648"
}

# Palavras-chave para busca (fallback)
PRODUTOS_POPULARES = [
    "smartwatch", "fone de ouvido bluetooth", "caixa de som", "carregador portátil",
    "camiseta", "vestido", "tênis", "bolsa feminina", "mochila",
    "cadeira gamer", "mesa escritório", "luminária", "quadro decorativo",
    "creme hidratante", "perfume importado", "kit maquiagem",
    "garrafa térmica", "tapete yoga", "peso academia",
    "brinquedo educativo", "boneca", "carrinho controle remoto",
    "capinha celular", "película protetora", "power bank",
    "fritadeira", "liquidificador", "panela elétrica", "cafeteira",
    "colchão", "travesseiro", "lençol", "toalha",
    "relógio", "óculos de sol", "cinto", "boné"
]

def validar_licenca_supabase(chave):
    if chave == "TESTE-AFILIADO-2026":
        return {"valido": True, "expira": "2026-12-31"}
    return {"valido": False}

def buscar_produtos_mercadolivre(termo, limite=5):
    """Busca produtos no Mercado Livre API"""
    url = f"https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "q": termo,
        "limit": limite,
        "sort": "relevance",
        "condition": "new"  # Apenas produtos novos
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
            
        data = response.json()
        produtos = []
        
        for item in data.get("results", [])[:limite]:
            preco = item.get("price", 0)
            
            # Calcula parcela se disponível
            parcelas = ""
            if item.get("installments"):
                parcela_info = item.get("installments")
                parcelas = f" ou {parcela_info.get('quantity')}x R$ {parcela_info.get('amount'):.2f}"
            
            produtos.append({
                "nome": item.get("title", "")[:80] + "..." if len(item.get("title", "")) > 80 else item.get("title", ""),
                "preco": f"R$ {preco:.2f}{parcelas}",
                "preco_numero": preco,
                "loja": "Mercado Livre",
                "link": item.get("permalink", ""),
                "imagem": item.get("thumbnail", ""),
                "vendas": item.get("sold_quantity", 0),
                "rating": item.get("seller", {}).get("seller_reputation", {}).get("power_seller_status", "normal")
            })
        
        return produtos
    except Exception as e:
        return []

def buscar_produtos_categoria_ml(categoria_id, limite=10):
    """Busca produtos em alta por categoria no Mercado Livre"""
    url = f"https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "category": categoria_id,
        "limit": limite,
        "sort": "relevance",
        "condition": "new"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
            
        data = response.json()
        produtos = []
        
        for item in data.get("results", [])[:limite]:
            preco = item.get("price", 0)
            
            produtos.append({
                "nome": item.get("title", "")[:80] + "..." if len(item.get("title", "")) > 80 else item.get("title", ""),
                "preco": f"R$ {preco:.2f}",
                "preco_numero": preco,
                "loja": "Mercado Livre",
                "link": item.get("permalink", ""),
                "imagem": item.get("thumbnail", ""),
                "vendas": item.get("sold_quantity", 0)
            })
        
        return produtos
    except Exception as e:
        return []

def buscar_produtos_shopee(termo, limite=3):
    """Busca produtos na Shopee"""
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
        produtos.append({
            "nome": nome[:60] + "..." if len(nome) > 60 else nome, 
            "preco": preco, 
            "link": link, 
            "loja": "Shopee"
        })

    return produtos

def analisar_produto(termo, categoria=""):
    """Análise completa do produto"""
    # Busca em ambas plataformas
    produtos_ml = buscar_produtos_mercadolivre(termo, 3)
    produtos_shopee = buscar_produtos_shopee(termo, 3)
    
    # Combina resultados
    todos_produtos = []
    
    for p in produtos_ml:
        p["plataforma"] = "Mercado Livre"
        todos_produtos.append(p)
    
    for p in produtos_shopee:
        p["plataforma"] = "Shopee"
        todos_produtos.append(p)
    
    # Calcula score de oportunidade (0-10)
    score = 0
    
    # Pontua por disponibilidade
    if len(produtos_ml) > 0:
        score += 3  # Mercado Livre é confiável
    if len(produtos_shopee) > 0:
        score += 2  # Shopee pode ter preços melhores
    
    # Pontua por variedade
    if len(todos_produtos) >= 4:
        score += 2
    elif len(todos_produtos) >= 2:
        score += 1
    
    # Pontua por preço médio (prefere produtos com preço médio)
    precos = [p.get("preco_numero", 0) for p in produtos_ml if p.get("preco_numero", 0) > 0]
    if precos:
        preco_medio = sum(precos) / len(precos)
        if 20 <= preco_medio <= 200:  # Faixa ideal para afiliado
            score += 2
        elif 200 < preco_medio <= 500:
            score += 1
    
    # Gera recomendação
    if score >= 7:
        recomendacao = "🔥 OPORTUNIDADE EXCELENTE - Produto com alta demanda!"
    elif score >= 5:
        recomendacao = "⭐ BOA OPORTUNIDADE - Bom potencial de venda"
    elif score >= 3:
        recomendacao = "📊 OPORTUNIDADE MÉDIA - Avaliar concorrência"
    else:
        recomendacao = "⚠️ OPORTUNIDADE BAIXA - Pouca oferta no mercado"
    
    return {
        "termo": termo,
        "categoria": categoria,
        "total_produtos": len(todos_produtos),
        "score": score,
        "recomendacao": recomendacao,
        "produtos_ml": produtos_ml,
        "produtos_shopee": produtos_shopee,
        "todos_produtos": todos_produtos
    }

def minerar_produtos():
    """Mineração sem Google Trends - apenas Mercado Livre e Shopee"""
    resultados = []
    
    # 1. Busca por categorias no Mercado Livre
    with st.spinner("Buscando produtos em alta no Mercado Livre..."):
        for categoria, categoria_id in CATEGORIAS_ML.items():
            produtos_cat = buscar_produtos_categoria_ml(categoria_id, 5)
            
            # Extrai termos únicos dos produtos encontrados
            termos = []
            for p in produtos_cat:
                # Pega palavras-chave do título
                palavras = p.get("nome", "").split()[:4]
                if palavras:
                    termo = " ".join(palavras[:3])
                    if len(termo) > 3 and termo not in termos:
                        termos.append(termo)
            
            # Analisa cada termo encontrado
            for termo in termos[:3]:  # Limita a 3 por categoria
                if termo not in [r["termo"] for r in resultados]:
                    analise = analisar_produto(termo, categoria)
                    analise["fonte"] = f"Mercado Livre - {categoria}"
                    resultados.append(analise)
                    time.sleep(0.5)  # Delay para não sobrecarregar
    
    # 2. Busca produtos populares como fallback
    if len(resultados) < 5:
        with st.spinner("Buscando produtos populares..."):
            produtos_random = random.sample(PRODUTOS_POPULARES, min(10, len(PRODUTOS_POPULARES)))
            
            for termo in produtos_random:
                if termo not in [r["termo"] for r in resultados]:
                    # Determina categoria aproximada
                    categoria = "Geral"
                    for cat, palavras in {
                        "Eletrônicos": ["smartwatch", "fone", "caixa", "carregador", "celular"],
                        "Moda": ["camiseta", "vestido", "tênis", "bolsa", "mochila"],
                        "Casa": ["cadeira", "mesa", "luminária", "quadro"],
                        "Beleza": ["creme", "perfume", "maquiagem"]
                    }.items():
                        if any(p in termo.lower() for p in palavras):
                            categoria = cat
                            break
                    
                    analise = analisar_produto(termo, categoria)
                    analise["fonte"] = "Produtos Populares"
                    resultados.append(analise)
                    time.sleep(0.5)
    
    # Ordena por score
    resultados = sorted(resultados, key=lambda x: x["score"], reverse=True)
    
    return pd.DataFrame(resultados[:20])

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

    st.markdown("""
    ### 🎯 Produtos em Tendência no Brasil
    
    🔍 **Como funciona:**
    - 🛒 Busca produtos em **Mercado Livre** (API oficial)
    - 📦 Verifica disponibilidade na **Shopee**
    - 📊 Calcula **score de oportunidade** para afiliados
    - 💡 Recomenda produtos com melhor potencial de venda
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Minerar Produtos", use_container_width=True):
            st.session_state.minerar = True
    with col2:
        st.caption("Mercado Livre + Shopee")
    with col3:
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")

    if st.session_state.get("minerar", False):
        with st.spinner("🔄 Minerando produtos em tempo real..."):
            try:
                df_resultados = minerar_produtos()
                
                if not df_resultados.empty:
                    # Métricas
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Produtos Encontrados", len(df_resultados))
                    
                    with col2:
                        excelentes = df_resultados[df_resultados["score"] >= 7]
                        st.metric("🔥 Excelentes", len(excelentes))
                    
                    with col3:
                        boas = df_resultados[(df_resultados["score"] >= 5) & (df_resultados["score"] < 7)]
                        st.metric("⭐ Boas", len(boas))
                    
                    with col4:
                        medias = df_resultados[df_resultados["score"] < 5]
                        st.metric("📊 Médias", len(medias))
                    
                    st.markdown("---")
                    
                    # Tabela de produtos
                    st.markdown("### 📊 Produtos com Score de Oportunidade")
                    
                    df_exibicao = df_resultados[["termo", "categoria", "score", "recomendacao", "fonte"]].copy()
                    df_exibicao.columns = ["Produto", "Categoria", "Score", "Recomendação", "Fonte"]
                    
                    st.dataframe(
                        df_exibicao,
                        column_config={
                            "Produto": "Produto",
                            "Categoria": "Categoria",
                            "Score": st.column_config.NumberColumn("Score", format="%d", 
                                help="Score baseado em disponibilidade, preço e variedade"),
                            "Recomendação": "Recomendação",
                            "Fonte": "Fonte do Dado"
                        },
                        use_container_width=True
                    )
                    
                    st.markdown("---")
                    st.markdown("### 🛒 Produtos Encontrados nas Plataformas")
                    
                    # Filtro por score
                    score_filtro = st.selectbox(
                        "Filtrar por oportunidade:",
                        ["Todos", "🔥 Excelente (Score ≥ 7)", "⭐ Boa (Score ≥ 5)", "📊 Média (Score ≥ 3)"]
                    )
                    
                    df_filtrado = df_resultados.copy()
                    if "Excelente" in score_filtro:
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 7]
                    elif "Boa" in score_filtro:
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 5]
                    elif "Média" in score_filtro:
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 3]
                    
                    # Exibe produtos em cards
                    for _, row in df_filtrado.iterrows():
                        with st.expander(f"📦 {row['termo']} - Score: {row['score']} - {row['recomendacao']}"):
                            col_a, col_b = st.columns([2, 1])
                            
                            with col_a:
                                st.markdown(f"**Categoria:** {row['categoria']}")
                                st.markdown(f"**Fonte:** {row['fonte']}")
                                st.markdown(f"**Total encontrado:** {row['total_produtos']}")
                            
                            with col_b:
                                st.link_button(
                                    "🔍 Shopee",
                                    f"https://shopee.com.br/search?keyword={quote(row['termo'])}",
                                    use_container_width=True
                                )
                                st.link_button(
                                    "🔍 Mercado Livre",
                                    f"https://lista.mercadolivre.com.br/{quote(row['termo'])}",
                                    use_container_width=True
                                )
                            
                            # Produtos do Mercado Livre
                            if row["produtos_ml"]:
                                st.markdown("**🟡 Mercado Livre:**")
                                for p in row["produtos_ml"][:3]:
                                    st.markdown(f"- {p.get('nome', 'Produto')}")
                                    st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                                    if p.get('link'):
                                        st.markdown(f"  [🔗 Ver produto]({p['link']})")
                                    st.markdown("")
                            
                            # Produtos da Shopee
                            if row["produtos_shopee"]:
                                st.markdown("**🟢 Shopee:**")
                                for p in row["produtos_shopee"][:3]:
                                    st.markdown(f"- {p.get('nome', 'Produto')}")
                                    st.markdown(f"  💰 {p.get('preco', '')}")
                                    if p.get('link'):
                                        st.markdown(f"  [🔗 Ver produto]({p['link']})")
                                    st.markdown("")
                            
                            if not row["produtos_ml"] and not row["produtos_shopee"]:
                                st.info("Nenhum produto encontrado nas plataformas")
                    
                    # Dicas para afiliados
                    st.markdown("---")
                    st.markdown("### 💡 Dicas para Afiliados")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("""
                        **🔥 Score ≥ 7 (Excelente)**
                        - Crie conteúdo URGENTE
                        - Vídeos mostrando o produto
                        - Poste em horários de pico
                        """)
                    
                    with col2:
                        st.success("""
                        **⭐ Score ≥ 5 (Boa)**
                        - Bom para conteúdo orgânico
                        - Posts no Instagram
                        - Stories mostrando o produto
                        """)
                    
                    st.success("✅ Mineração concluída com sucesso!")
                    
                else:
                    st.warning("Nenhum produto encontrado. Tente novamente.")
                
                st.session_state.minerar = False
                
            except Exception as e:
                st.error(f"Erro na mineração: {str(e)}")
                st.session_state.minerar = False

    st.markdown("---")
    st.markdown("### 📌 Dicas de Conteúdo por Categoria")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🛍️ Moda**")
        st.caption("Faça vídeos mostrando combinações e tendências")
        st.markdown("**📱 Eletrônicos**")
        st.caption("Mostre funcionalidades e faça comparativos")
    with col2:
        st.markdown("**🏠 Casa**")
        st.caption("Vídeos de decoração e transformação de ambientes")
        st.markdown("**🎁 Presentes**")
        st.caption("Crie listas de presentes para datas comemorativas")
