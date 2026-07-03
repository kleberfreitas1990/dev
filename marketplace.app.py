import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import requests
import random
import re

# Configuração da página
st.set_page_config(page_title="Minerador Pro - Produtos", page_icon="🛍️", layout="wide")

# ===== CONFIGURAÇÕES =====
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

# Palavras-chave para identificar afiliados na Shopee
PALAVRAS_AFILIADO = [
    "afiliado", "shopee", "promoção", "desconto", "cupom", 
    "parceria", "indicado", "recomendado", "oferta", "imperdível",
    "coach", "digital", "influencer", "indicada", "parceria"
]

# Palavras-chave de produtos com potencial de venda
PALAVRAS_POTENCIAL = [
    "bestseller", "mais vendido", "top vendas", "sucesso", "febre",
    "viral", "boom", "popular", "queridinho", "lançamento",
    "novo", "tendência", "moda", "estilo", "desejado",
    "edição limitada", "exclusivo", "raro", "difícil encontrar"
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
                "nome": item.get("title", "")[:80],
                "preco": f"R$ {preco:.2f}",
                "preco_numero": preco,
                "loja": "Mercado Livre",
                "link": item.get("permalink", ""),
                "vendas": item.get("sold_quantity", 0),
                "rating": item.get("seller", {}).get("seller_reputation", {}).get("power_seller_status", "normal")
            })
        
        return produtos
    except Exception as e:
        return []

def buscar_produtos_shopee_detalhado(termo, limite=10):
    """
    Busca produtos na Shopee com análise de afiliados
    Retorna também informações sobre potencial de vendas
    """
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
        
        nome = info.get("name", "")
        preco_centavos = info.get("price")
        itemid = info.get("itemid")
        shopid = info.get("shopid")
        sold_count = info.get("sold", 0)
        stock = info.get("stock", 0)
        
        if not nome or not itemid or not shopid:
            continue
        
        preco = f"R$ {preco_centavos / 100000:.2f}" if preco_centavos else "—"
        link = f"https://shopee.com.br/product/{shopid}/{itemid}"
        
        # Análise de afiliado
        is_afiliado = any(palavra in nome.lower() for palavra in PALAVRAS_AFILIADO)
        
        # Análise de potencial de venda
        potencial_score = 0
        for palavra in PALAVRAS_POTENCIAL:
            if palavra.lower() in nome.lower():
                potencial_score += 1
        
        # Verifica se tem muitas vendas (produto validado)
        if sold_count > 100:
            potencial_score += 2
        elif sold_count > 50:
            potencial_score += 1
        
        # Calcula densidade de afiliados (simulação)
        # Na Shopee real, isso seria feito analisando a descrição do produto
        # Aqui usamos palavras-chave na descrição como proxy
        afiliado_score = 0
        if "afiliado" in nome.lower():
            afiliado_score += 2
        if "cupom" in nome.lower() or "desconto" in nome.lower():
            afiliado_score += 1
        
        produtos.append({
            "nome": nome[:60],
            "preco": preco,
            "preco_numero": preco_centavos / 100000 if preco_centavos else 0,
            "link": link,
            "loja": "Shopee",
            "vendas": sold_count,
            "estoque": stock,
            "is_afiliado": is_afiliado,
            "afiliado_score": afiliado_score,  # Quanto menor, menos afiliados
            "potencial_score": potencial_score,  # Quanto maior, mais potencial
            "potencial_descricao": "🟢 Alto potencial" if potencial_score >= 3 else "🟡 Médio potencial" if potencial_score >= 1 else "🔴 Baixo potencial"
        })
    
    return produtos

def analisar_produto_completo(termo, categoria=""):
    """
    Análise completa com foco em potencial de vendas e concorrência de afiliados
    """
    # Busca em ambas plataformas
    produtos_ml = buscar_produtos_mercadolivre(termo, 3)
    produtos_shopee = buscar_produtos_shopee_detalhado(termo, 10)
    
    # Análise de afiliados na Shopee
    total_shopee = len(produtos_shopee)
    afiliados_shopee = [p for p in produtos_shopee if p.get("is_afiliado", False)]
    total_afiliados = len(afiliados_shopee)
    
    # Calcula densidade de afiliados (%)
    densidade_afiliados = (total_afiliados / total_shopee * 100) if total_shopee > 0 else 100
    
    # Calcula score de oportunidade para afiliados
    # Queremos: muitos produtos (oferta), poucos afiliados (baixa concorrência), alto potencial
    score_oportunidade = 0
    
    # 1. Disponibilidade de produtos
    if total_shopee >= 5:
        score_oportunidade += 3
    elif total_shopee >= 3:
        score_oportunidade += 2
    elif total_shopee >= 1:
        score_oportunidade += 1
    
    # 2. Baixa densidade de afiliados (concorrência)
    if densidade_afiliados < 20:
        score_oportunidade += 3  # Ótimo! Poucos afiliados
    elif densidade_afiliados < 40:
        score_oportunidade += 2
    elif densidade_afiliados < 60:
        score_oportunidade += 1
    else:
        score_oportunidade -= 1  # Muitos afiliados, concorrência alta
    
    # 3. Potencial de vendas (média de vendas)
    vendas_totais = sum(p.get("vendas", 0) for p in produtos_shopee)
    media_vendas = vendas_totais / total_shopee if total_shopee > 0 else 0
    
    if media_vendas > 100:
        score_oportunidade += 3  # Produto validado, mercado quente
    elif media_vendas > 50:
        score_oportunidade += 2
    elif media_vendas > 10:
        score_oportunidade += 1
    
    # 4. Potencial score dos produtos
    potencial_medio = sum(p.get("potencial_score", 0) for p in produtos_shopee) / total_shopee if total_shopee > 0 else 0
    if potencial_medio >= 2:
        score_oportunidade += 2
    elif potencial_medio >= 1:
        score_oportunidade += 1
    
    # 5. Preço médio (faixa ideal para afiliado: R$30-R$150)
    precos = [p.get("preco_numero", 0) for p in produtos_shopee if p.get("preco_numero", 0) > 0]
    if precos:
        preco_medio = sum(precos) / len(precos)
        if 30 <= preco_medio <= 150:
            score_oportunidade += 2  # Faixa ideal para afiliados
        elif 150 < preco_medio <= 300:
            score_oportunidade += 1
    
    # Gera recomendação
    if score_oportunidade >= 8:
        recomendacao = "🚀 OPORTUNIDADE EXCELENTE - Baixa concorrência e alto potencial!"
    elif score_oportunidade >= 6:
        recomendacao = "⭐ ÓTIMA OPORTUNIDADE - Poucos afiliados, boa demanda"
    elif score_oportunidade >= 4:
        recomendacao = "📊 BOA OPORTUNIDADE - Concorrência moderada"
    elif score_oportunidade >= 2:
        recomendacao = "⚠️ OPORTUNIDADE MÉDIA - Avaliar concorrência"
    else:
        recomendacao = "🔴 OPORTUNIDADE BAIXA - Muitos afiliados ou pouca demanda"
    
    return {
        "termo": termo,
        "categoria": categoria,
        "total_produtos_shopee": total_shopee,
        "total_afiliados": total_afiliados,
        "densidade_afiliados": f"{densidade_afiliados:.1f}%",
        "media_vendas": media_vendas,
        "score_oportunidade": score_oportunidade,
        "recomendacao": recomendacao,
        "produtos_ml": produtos_ml,
        "produtos_shopee": produtos_shopee,
        "fonte": f"Shopee + ML"
    }

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
                "nome": item.get("title", "")[:80],
                "preco": f"R$ {preco:.2f}",
                "preco_numero": preco,
                "loja": "Mercado Livre",
                "link": item.get("permalink", ""),
                "vendas": item.get("sold_quantity", 0)
            })
        
        return produtos
    except Exception as e:
        return []

def minerar_produtos_oportunidade():
    """
    Minera produtos com foco em:
    1. Produtos disponíveis na Shopee
    2. Poucos afiliados (baixa concorrência)
    3. Alto potencial de vendas
    """
    resultados = []
    
    # 1. Busca por categorias no Mercado Livre para encontrar produtos quentes
    with st.spinner("Buscando produtos em alta no Mercado Livre..."):
        for categoria, categoria_id in CATEGORIAS_ML.items():
            produtos_cat = buscar_produtos_categoria_ml(categoria_id, 5)
            
            for p in produtos_cat:
                # Extrai termos-chave
                palavras = p.get("nome", "").split()[:4]
                if palavras:
                    termo = " ".join(palavras[:3])
                    if len(termo) > 3 and termo not in [r["termo"] for r in resultados]:
                        analise = analisar_produto_completo(termo, categoria)
                        resultados.append(analise)
                        time.sleep(0.3)  # Delay para não sobrecarregar
    
    # 2. Produtos populares como fallback
    produtos_base = [
        "smartwatch", "fone bluetooth", "caixa de som", "carregador portátil",
        "camisa", "vestido", "tênis", "bolsa", "mochila",
        "cadeira gamer", "luminária led", "quadro decorativo",
        "perfume", "kit maquiagem", "garrafa térmica",
        "brinquedo educativo", "boneca", "carrinho controle remoto",
        "capinha celular", "power bank"
    ]
    
    for termo in produtos_base[:10]:
        if termo not in [r["termo"] for r in resultados]:
            categoria = "Geral"
            for cat, keywords in {
                "Eletrônicos": ["smartwatch", "fone", "caixa", "carregador", "celular"],
                "Moda": ["camisa", "vestido", "tênis", "bolsa", "mochila"],
                "Casa": ["cadeira", "luminária", "quadro"],
                "Beleza": ["perfume", "maquiagem"]
            }.items():
                if any(k in termo.lower() for k in keywords):
                    categoria = cat
                    break
            
            analise = analisar_produto_completo(termo, categoria)
            resultados.append(analise)
            time.sleep(0.3)
    
    # Ordena por score de oportunidade (maior = melhor)
    resultados = sorted(resultados, key=lambda x: x["score_oportunidade"], reverse=True)
    
    return pd.DataFrame(resultados[:20])

# ===== INTERFACE =====
st.title("🛍️ Minerador Pro - Oportunidades para Afiliados")

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

    # Explicação do método
    st.markdown("""
    ### 🎯 Encontre Produtos com Baixa Concorrência e Alto Potencial
    
    🔍 **Metodologia de Análise:**
    - 🔄 Busca produtos em **Mercado Livre** (tendências)
    - 📊 Analisa **densidade de afiliados** na Shopee
    - 📈 Calcula **potencial de vendas** por produto
    - ⭐ Identifica **oportunidades com pouca concorrência**
    
    💡 **O que significa cada métrica:**
    - **Score de Oportunidade**: Quanto maior, melhor para afiliados
    - **Densidade de Afiliados**: % de produtos com menção a afiliado (menor = melhor)
    - **Média de Vendas**: Produtos que já estão vendendo bem
    - **Recomendação**: Análise consolidada da oportunidade
    """)

    if st.button("🚀 Buscar Oportunidades", use_container_width=True):
        with st.spinner("Analisando oportunidades na Shopee..."):
            try:
                df_resultados = minerar_produtos_oportunidade()
                
                if not df_resultados.empty:
                    # Métricas principais
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Produtos Analisados", len(df_resultados))
                    
                    with col2:
                        excelentes = df_resultados[df_resultados["score_oportunidade"] >= 8]
                        st.metric("🚀 Oportunidades Excelentes", len(excelentes))
                    
                    with col3:
                        boas = df_resultados[(df_resultados["score_oportunidade"] >= 6) & (df_resultados["score_oportunidade"] < 8)]
                        st.metric("⭐ Boas Oportunidades", len(boas))
                    
                    with col4:
                        baixa_concorrencia = df_resultados[df_resultados["densidade_afiliados"].str.replace('%', '').astype(float) < 30]
                        st.metric("🎯 Baixa Concorrência", len(baixa_concorrencia))
                    
                    st.markdown("---")
                    
                    # Tabela principal
                    st.markdown("### 📊 Oportunidades por Score")
                    
                    df_exibicao = df_resultados[["termo", "categoria", "score_oportunidade", "densidade_afiliados", "media_vendas", "recomendacao"]].copy()
                    df_exibicao.columns = ["Produto", "Categoria", "Score", "% Afiliados", "Média Vendas", "Recomendação"]
                    
                    # Formata números
                    df_exibicao["Média Vendas"] = df_exibicao["Média Vendas"].apply(lambda x: f"{x:.0f}")
                    
                    st.dataframe(
                        df_exibicao,
                        column_config={
                            "Produto": "Produto",
                            "Categoria": "Categoria",
                            "Score": st.column_config.NumberColumn("Score", format="%d"),
                            "% Afiliados": "% Afiliados",
                            "Média Vendas": "Média Vendas",
                            "Recomendação": "Recomendação"
                        },
                        use_container_width=True
                    )
                    
                    st.markdown("---")
                    
                    # Filtros
                    st.markdown("### 🎯 Filtrar Oportunidades")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        filtro_score = st.selectbox(
                            "Score mínimo:",
                            ["Todos", "Excelente (≥8)", "Boa (≥6)", "Média (≥4)"]
                        )
                    
                    with col2:
                        filtro_concorrencia = st.selectbox(
                            "Concorrência:",
                            ["Todas", "Baixa (<30% afiliados)", "Média (30-50%)", "Alta (>50%)"]
                        )
                    
                    with col3:
                        filtro_categoria = st.selectbox(
                            "Categoria:",
                            ["Todas"] + list(CATEGORIAS_ML.keys())
                        )
                    
                    # Aplica filtros
                    df_filtrado = df_resultados.copy()
                    
                    if "Excelente" in filtro_score:
                        df_filtrado = df_filtrado[df_filtrado["score_oportunidade"] >= 8]
                    elif "Boa" in filtro_score:
                        df_filtrado = df_filtrado[df_filtrado["score_oportunidade"] >= 6]
                    elif "Média" in filtro_score:
                        df_filtrado = df_filtrado[df_filtrado["score_oportunidade"] >= 4]
                    
                    if "Baixa" in filtro_concorrencia:
                        df_filtrado = df_filtrado[df_filtrado["densidade_afiliados"].str.replace('%', '').astype(float) < 30]
                    elif "Média" in filtro_concorrencia:
                        df_filtrado = df_filtrado[(df_filtrado["densidade_afiliados"].str.replace('%', '').astype(float) >= 30) & 
                                                   (df_filtrado["densidade_afiliados"].str.replace('%', '').astype(float) <= 50)]
                    elif "Alta" in filtro_concorrencia:
                        df_filtrado = df_filtrado[df_filtrado["densidade_afiliados"].str.replace('%', '').astype(float) > 50]
                    
                    if filtro_categoria != "Todas":
                        df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_categoria]
                    
                    # Exibe produtos filtrados
                    if not df_filtrado.empty:
                        st.markdown(f"**{len(df_filtrado)} produtos encontrados com os filtros selecionados**")
                        
                        for _, row in df_filtrado.iterrows():
                            with st.expander(f"📦 {row['termo']} - Score: {row['score_oportunidade']} - {row['recomendacao']}"):
                                
                                # Métricas do produto
                                col_a, col_b, col_c = st.columns(3)
                                
                                with col_a:
                                    st.metric("Score Oportunidade", f"{row['score_oportunidade']}/10")
                                    st.caption(row['recomendacao'])
                                
                                with col_b:
                                    st.metric("Densidade Afiliados", row['densidade_afiliados'])
                                    if float(row['densidade_afiliados'].replace('%', '')) < 30:
                                        st.success("✅ Baixa concorrência!")
                                    else:
                                        st.warning("⚠️ Concorrência moderada/alta")
                                
                                with col_c:
                                    st.metric("Média de Vendas", f"{row['media_vendas']:.0f}")
                                    if row['media_vendas'] > 50:
                                        st.success("✅ Produto validado!")
                                    else:
                                        st.info("📊 Produto em crescimento")
                                
                                st.markdown("---")
                                
                                # Produtos da Shopee (detalhados)
                                if row["produtos_shopee"]:
                                    st.markdown("#### 🟢 Produtos na Shopee")
                                    
                                    # Separa por afiliado
                                    afiliados = [p for p in row["produtos_shopee"] if p.get("is_afiliado", False)]
                                    nao_afiliados = [p for p in row["produtos_shopee"] if not p.get("is_afiliado", False)]
                                    
                                    # Mostra produtos NÃO afiliados primeiro (melhor oportunidade)
                                    if nao_afiliados:
                                        st.markdown("**🔍 Produtos sem afiliados (melhor oportunidade):**")
                                        for p in nao_afiliados[:3]:
                                            st.markdown(f"- {p.get('nome', '')}")
                                            st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                                            st.markdown(f"  🔗 [Ver na Shopee]({p.get('link', '#')})")
                                            st.markdown(f"  📊 Potencial: {p.get('potencial_descricao', '')}")
                                            st.markdown("")
                                    
                                    if afiliados and len(nao_afiliados) < 3:
                                        st.markdown("**📌 Produtos com afiliados (concorrência):**")
                                        for p in afiliados[:2]:
                                            st.markdown(f"- {p.get('nome', '')}")
                                            st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                                            st.markdown("")
                                
                                # Links rápidos
                                st.markdown("---")
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.link_button(
                                        "🔍 Buscar na Shopee",
                                        f"https://shopee.com.br/search?keyword={quote(row['termo'])}",
                                        use_container_width=True
                                    )
                                with col_b:
                                    st.link_button(
                                        "🔍 Buscar no Mercado Livre",
                                        f"https://lista.mercadolivre.com.br/{quote(row['termo'])}",
                                        use_container_width=True
                                    )
                    else:
                        st.warning("Nenhum produto encontrado com os filtros selecionados")
                    
                    # Dicas estratégicas
                    st.markdown("---")
                    st.markdown("### 💡 Estratégia para Afiliados")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success("""
                        **🎯 Oportunidades Excelentes (Score ≥ 8)**
                        - ✅ Baixa concorrência de afiliados
                        - ✅ Produto já validado (muitas vendas)
                        - ✅ Faixa de preço ideal (R$30-R$150)
                        
                        **Ação:** Crie conteúdo URGENTE!
                        """)
                    
                    with col2:
                        st.info("""
                        **⭐ Boas Oportunidades (Score ≥ 6)**
                        - ⚠️ Concorrência moderada
                        - 📊 Produto com potencial de crescimento
                        
                        **Ação:** Analise a concorrência e crie conteúdo diferenciado
                        """)
                    
                    st.success("✅ Análise concluída! Foque nos produtos com menor densidade de afiliados!")
                    
                else:
                    st.warning("Nenhum produto encontrado. Tente novamente.")
                
            except Exception as e:
                st.error(f"Erro na mineração: {str(e)}")
                st.info("Tente novamente em alguns segundos.")

    st.markdown("---")
    st.markdown("### 📌 Dica: Como usar essa análise")
    
    st.info("""
    **Estratégia para maximizar suas vendas:**
    1. 🎯 Foque em produtos com **Score ≥ 8** e **baixa densidade de afiliados**
    2. 📈 Crie conteúdo mostrando o produto de forma autêntica
    3. 🔄 Teste diferentes produtos para ver qual converte melhor
    4. 🚀 Seja rápido - produtos com alto potencial atraem concorrentes rápido
    """)
