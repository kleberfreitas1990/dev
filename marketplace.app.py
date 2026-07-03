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
from functools import lru_cache
import random

# Configuração da página
st.set_page_config(page_title="Minerador Pro - Produtos", page_icon="🛍️", layout="wide")

# ===== CONFIGURAÇÕES =====
# Cache para evitar requisições repetidas
CACHE_DURATION = 3600  # 1 hora
ULTIMA_BUSCA = {}

# Lista de produtos base para fallback (quando Google Trends falha)
PRODUTOS_FALLBACK = [
    {"termo": "smartwatch", "categoria": "Eletrônicos"},
    {"termo": "fone bluetooth", "categoria": "Eletrônicos"},
    {"termo": "caixa de som", "categoria": "Eletrônicos"},
    {"termo": "carregador portátil", "categoria": "Eletrônicos"},
    {"termo": "camisa feminina", "categoria": "Moda"},
    {"termo": "vestido", "categoria": "Moda"},
    {"termo": "tênis", "categoria": "Moda"},
    {"termo": "bolsa", "categoria": "Moda"},
    {"termo": "cadeira gamer", "categoria": "Casa e Decoração"},
    {"termo": "luminária led", "categoria": "Casa e Decoração"},
    {"termo": "quadro decorativo", "categoria": "Casa e Decoração"},
    {"termo": "creme hidratante", "categoria": "Beleza"},
    {"termo": "perfume", "categoria": "Beleza"},
    {"termo": "kit maquiagem", "categoria": "Beleza"},
    {"termo": "suplemento whey", "categoria": "Saúde"},
    {"termo": "garrafa térmica", "categoria": "Esportes"},
    {"termo": "brinquedo educativo", "categoria": "Brinquedos"},
    {"termo": "capinha celular", "categoria": "Eletrônicos"},
    {"termo": "power bank", "categoria": "Eletrônicos"},
    {"termo": "mochila", "categoria": "Moda"}
]

# ===== FUNÇÕES =====
def validar_licenca_supabase(chave):
    if chave == "TESTE-AFILIADO-2026":
        return {"valido": True, "expira": "2026-12-31"}
    return {"valido": False}

@lru_cache(maxsize=100)
def buscar_trends_por_categoria_com_cache(categoria_codigo):
    """
    Busca tendências por categoria com cache para evitar 429
    """
    time.sleep(random.uniform(1, 3))  # Delay aleatório para evitar rate limit
    
    try:
        pytrends = TrendReq(hl='pt-BR', tz=-180)
        
        # Usa termos base para buscar tendências
        termos_base = ["smartwatch", "fone", "camisa", "cadeira", "perfume"]
        
        pytrends.build_payload(
            kw_list=termos_base,
            cat=categoria_codigo,
            timeframe='now 1-d',
            geo='BR'
        )
        
        dados = pytrends.interest_over_time()
        
        if dados.empty:
            return []
        
        termos = dados.columns.tolist()
        if 'isPartial' in termos:
            termos.remove('isPartial')
        
        return termos[:3]  # Limita a 3 termos por categoria
        
    except Exception as e:
        if "429" in str(e):
            st.warning(f"⏳ Limite de requisições do Google atingido. Usando produtos base.")
        return []

def buscar_produtos_mercadolivre(termo, limite=5):
    """Busca produtos no Mercado Livre API (gratuita)"""
    url = f"https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "q": termo,
        "limit": limite,
        "sort": "relevance"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
            
        data = response.json()
        
        produtos = []
        for item in data.get("results", [])[:limite]:
            produtos.append({
                "nome": item.get("title", "")[:60] + "...",
                "preco": f"R$ {item.get('price', 0):.2f}",
                "loja": "Mercado Livre",
                "link": item.get("permalink", ""),
                "imagem": item.get("thumbnail", "")
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
            "nome": nome[:60] + "...", 
            "preco": preco, 
            "link": link, 
            "loja": "Shopee"
        })

    return produtos

def analisar_produto(termo, categoria=""):
    """
    Análise completa de um produto
    """
    # Busca produtos em diferentes plataformas
    produtos_shopee = buscar_produtos_shopee(termo, 3)
    produtos_ml = buscar_produtos_mercadolivre(termo, 3)
    
    # Combina resultados
    todos_produtos = []
    
    for p in produtos_shopee:
        p["plataforma"] = "Shopee"
        todos_produtos.append(p)
    
    for p in produtos_ml:
        p["plataforma"] = "Mercado Livre"
        todos_produtos.append(p)
    
    # Calcula score de oportunidade
    score = 0
    recomendacao = ""
    
    if len(todos_produtos) > 0:
        score += 2
    
    if len(produtos_shopee) > 0:
        score += 2
    
    if len(produtos_ml) > 0:
        score += 1
    
    # Gera recomendação
    if score >= 5:
        recomendacao = "🔥 OPORTUNIDADE EXCELENTE"
    elif score >= 3:
        recomendacao = "⭐ BOA OPORTUNIDADE"
    elif score >= 1:
        recomendacao = "📊 OPORTUNIDADE MÉDIA"
    else:
        recomendacao = "⚠️ OPORTUNIDADE BAIXA"
    
    return {
        "termo": termo,
        "categoria": categoria,
        "total_produtos": len(todos_produtos),
        "score": score,
        "recomendacao": recomendacao,
        "produtos": todos_produtos
    }

def minerar_produtos_tendencias():
    """
    Mineração avançada com fallback inteligente
    """
    resultados = []
    
    # Tenta buscar do Google Trends primeiro
    categorias = {
        "Eletrônicos": 5,
        "Moda": 411,
        "Casa e Decoração": 455,
        "Beleza": 442,
        "Saúde": 451,
        "Esportes": 445,
        "Brinquedos": 444,
        "Automotivo": 447
    }
    
    termos_encontrados = []
    
    # Busca por categoria (com delay e limite)
    for categoria, codigo in categorias.items():
        termos = buscar_trends_por_categoria_com_cache(codigo)
        if termos:
            for termo in termos:
                if termo not in termos_encontrados:
                    termos_encontrados.append(termo)
                    analise = analisar_produto(termo, categoria)
                    analise["fonte"] = f"Google Trends - {categoria}"
                    resultados.append(analise)
        
        # Delay entre categorias para evitar rate limit
        time.sleep(random.uniform(2, 4))
    
    # Se poucos resultados, usa fallback
    if len(resultados) < 5:
        st.info("📌 Usando lista de produtos populares como base...")
        
        # Usa produtos de fallback
        for produto in PRODUTOS_FALLBACK[:15]:
            if produto["termo"] not in termos_encontrados:
                analise = analisar_produto(produto["termo"], produto["categoria"])
                analise["fonte"] = "Produtos Populares (Base)"
                resultados.append(analise)
    
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
    - 🔄 Busca em **Google Trends** com delay inteligente para evitar bloqueios
    - 🛒 Verifica disponibilidade em **Shopee e Mercado Livre**
    - 📊 Calcula **score de oportunidade** para afiliados
    - 📌 Fallback automático para produtos populares se o Trends falhar
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Minerar Produtos", use_container_width=True):
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
                        st.metric("🔥 Excelentes", len(excelentes))
                    
                    with col3:
                        boas = df_resultados[(df_resultados["score"] >= 3) & (df_resultados["score"] < 5)]
                        st.metric("⭐ Boas", len(boas))
                    
                    with col4:
                        medias = df_resultados[df_resultados["score"] < 3]
                        st.metric("📊 Médias", len(medias))
                    
                    st.markdown("---")
                    
                    # Tabela de produtos
                    st.markdown("### 📊 Produtos com Score de Oportunidade")
                    
                    df_exibicao = df_resultados[["termo", "categoria", "score", "recomendacao", "fonte"]].copy()
                    df_exibicao.columns = ["Produto", "Categoria", "Score", "Recomendação", "Fonte"]
                    
                    # Aplica cores no score
                    def color_score(val):
                        if val >= 5:
                            return 'background-color: #28a745; color: white'
                        elif val >= 3:
                            return 'background-color: #17a2b8; color: white'
                        elif val >= 1:
                            return 'background-color: #ffc107; color: black'
                        else:
                            return 'background-color: #dc3545; color: white'
                    
                    st.dataframe(
                        df_exibicao,
                        column_config={
                            "Produto": "Produto",
                            "Categoria": "Categoria",
                            "Score": st.column_config.NumberColumn("Score", format="%d"),
                            "Recomendação": "Recomendação",
                            "Fonte": "Fonte"
                        },
                        use_container_width=True
                    )
                    
                    # Detalhamento dos produtos
                    st.markdown("### 🛒 Produtos Disponíveis nas Plataformas")
                    
                    # Filtro por score
                    score_filtro = st.selectbox(
                        "Filtrar por oportunidade:",
                        ["Todos", "Excelente (Score ≥ 5)", "Boa (Score ≥ 3)", "Média (Score ≥ 1)"]
                    )
                    
                    df_filtrado = df_resultados.copy()
                    if "Excelente" in score_filtro:
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 5]
                    elif "Boa" in score_filtro:
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 3]
                    elif "Média" in score_filtro:
                        df_filtrado = df_filtrado[df_filtrado["score"] >= 1]
                    
                    # Exibe cada produto em cards
                    for _, row in df_filtrado.iterrows():
                        with st.expander(f"📦 {row['termo']} - Score: {row['score']} - {row['recomendacao']}"):
                            col_a, col_b = st.columns([2, 1])
                            
                            with col_a:
                                st.markdown(f"**Categoria:** {row['categoria']}")
                                st.markdown(f"**Fonte:** {row['fonte']}")
                                st.markdown(f"**Total de produtos encontrados:** {row['total_produtos']}")
                            
                            with col_b:
                                st.link_button(
                                    "🔍 Buscar na Shopee",
                                    f"https://shopee.com.br/search?keyword={quote(row['termo'])}"
                                )
                                st.link_button(
                                    "🔍 Buscar no Mercado Livre",
                                    f"https://lista.mercadolivre.com.br/{quote(row['termo'])}"
                                )
                            
                            # Produtos encontrados
                            if row["produtos"]:
                                st.markdown("**Produtos disponíveis:**")
                                for p in row["produtos"][:5]:
                                    st.markdown(f"- **{p.get('nome', 'Produto')}**")
                                    st.markdown(f"  💰 {p.get('preco', '')} - {p.get('plataforma', '')}")
                                    if p.get('link'):
                                        st.markdown(f"  [🔗 Ver produto]({p['link']})")
                                    st.markdown("---")
                            else:
                                st.info("Nenhum produto encontrado nas plataformas")
                    
                    # Dicas para afiliados
                    st.markdown("---")
                    st.markdown("### 💡 Dicas para Afiliados")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("""
                        **🔥 Produtos com Score ≥ 5**
                        - Crie vídeos URGENTE no TikTok/Reels
                        - Use chamadas como "PRODUTO VIRAL!"
                        - Poste em horários de pico (19h-22h)
                        """)
                    
                    with col2:
                        st.success("""
                        **⭐ Produtos com Score ≥ 3**
                        - Ótimo para posts no Instagram
                        - Faça stories mostrando o produto
                        - Use hashtags relacionadas
                        """)
                    
                    st.success("✅ Mineração concluída com sucesso!")
                    
                else:
                    st.warning("Nenhum produto encontrado. Tente novamente.")
                
                st.session_state.minerar = False
                
            except Exception as e:
                st.error(f"Erro na mineração: {str(e)}")
                st.session_state.minerar = False

    st.markdown("---")
    st.markdown("### 📌 Próximas Datas para Conteúdo")
    
    # Calendário de datas relevantes para produtos
    hoje = datetime.now()
    datas_produtos = [
        ("Dia dos Pais", "presentes masculinos, ferramentas, eletrônicos"),
        ("Dia das Crianças", "brinquedos, jogos, material escolar"),
        ("Black Friday", "eletrônicos, moda, promoções"),
        ("Natal", "presentes, decoração, brinquedos")
    ]
    
    for evento, dica in datas_produtos:
        st.caption(f"📅 **{evento}** → {dica}")
