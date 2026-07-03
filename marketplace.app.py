import streamlit as st
import pandas as pd
import feedparser
import time
from datetime import datetime
from urllib.parse import quote
import requests

# Configuração da página do seu sistema
st.set_page_config(page_title="Minerador Pro - Afiliados", page_icon="🚀", layout="wide")

# Credenciais temporárias para o app não quebrar sem banco de dados
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sua-anon-key-do-supabase"


def validar_licenca_supabase(chave):
    """Verificação híbrida: Aceita chave local de teste e evita travar a tela"""
    # CHAVE DE TESTE LOCAL (Funciona sempre)
    if chave == "TESTE-AFILIADO-2026":
        return {"valido": True, "expira": "2026-12-31"}

    return {"valido": False}


def buscar_produtos_shopee(termo, limite=3):
    """Busca produtos reais na Shopee para um termo, via endpoint interno público.

    ATENÇÃO: não é uma API oficial da Shopee. Pode parar de funcionar sem aviso
    e a Shopee pode bloquear requisições automatizadas (CAPTCHA/IP block).
    Trate falhas aqui como esperadas, não como bug.
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
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
        produtos.append({"nome": nome, "preco": preco, "link": link})

    return produtos


def cruzar_trends_com_shopee(termos, max_produtos_por_termo=2):
    """Para cada termo em alta, busca produtos correspondentes reais na Shopee."""
    linhas = []
    for termo in termos:
        produtos = buscar_produtos_shopee(termo, limite=max_produtos_por_termo)
        if produtos:
            for p in produtos:
                linhas.append({
                    "Tendência": termo,
                    "Produto na Shopee": p["nome"],
                    "Preço": p["preco"],
                    "Link do Produto": p["link"],
                })
        else:
            # Sem produto encontrado: mantém a tendência com link de busca genérico
            linhas.append({
                "Tendência": termo,
                "Produto na Shopee": "(nenhum produto encontrado)",
                "Preço": "—",
                "Link do Produto": f"https://shopee.com.br/search?keyword={quote(termo)}",
            })
    return pd.DataFrame(linhas)


def minerar_dados_trends(geo="BR"):
    """Lê o feed RSS oficial do Google Trends (Trending Now) para o país informado.

    Esse feed é público e mantido pelo próprio Google, então não sofre com as
    quebras de API que atingiam o pytrends (biblioteca não-oficial e sem
    manutenção desde 2025).
    """
    url_feed = f"https://trends.google.com/trending/rss?geo={geo}"
    feed = feedparser.parse(url_feed)

    if feed.bozo and not feed.entries:
        # bozo=True indica falha ao interpretar o XML; sem entries, não há dado usável
        raise ValueError("Não foi possível ler o feed do Google Trends no momento.")

    termos = []
    for entrada in feed.entries:
        titulo = entrada.get("title", "").strip()
        if titulo and titulo not in termos:
            termos.append(titulo)

    if not termos:
        raise ValueError("O feed do Google Trends voltou vazio.")

    termos = termos[:15]

    resultados = {
        "Produto / Tendência": termos,
        "Link de Busca Shopee": [
            f"https://shopee.com.br/search?keyword={quote(t)}" for t in termos
        ]
    }
    return pd.DataFrame(resultados)


# --- INTERFACE DO USUÁRIO (SISTEMA) ---
st.title("🚀 Minerador Pro - Painel de Tendências")

# Inicializa o estado da sessão de login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# TELA 1: Bloqueio de Licença
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

# TELA 2: O Dashboard do Cliente (Só renderiza se estiver autenticado)
else:
    st.sidebar.success("Acesso Garantido")
    st.sidebar.info(f"Sua licença expira em: {st.session_state.data_expira}")
    if st.sidebar.button("Sair / Desconectar"):
        st.session_state.autenticado = False
        st.rerun()

    st.markdown("### 🔥 Produtos e Termos Mais Buscados no Brasil (Últimas Horas)")
    st.write("Use esses insights para criar vídeos de 'achadinhos' no TikTok/Instagram antes dos concorrentes.")

    if st.button("🔄 Rodar Mineração em Tempo Real"):
        with st.spinner("Buscando dados no Google Trends..."):
            try:
                df_produtos = minerar_dados_trends()

                # Exibe os dados em uma tabela interativa bonita
                st.dataframe(
                    df_produtos,
                    column_config={
                        "Link de Busca Shopee": st.column_config.LinkColumn("Ver Produtos na Shopee")
                    },
                    use_container_width=True
                )

                st.success("Dados atualizados com sucesso!")

                # Gráfico de Projeção Simples (Simulação de demanda do dia)
                st.markdown("### 📈 Gráfico de Volume Estimado de Interesse")
                qtd = len(df_produtos)
                valores_interesse = [max(40, 95 - i * 4) for i in range(qtd)]
                df_grafico = pd.DataFrame({
                    "Termo": df_produtos["Produto / Tendência"],
                    "Interesse Estimado (0-100)": valores_interesse
                })
                st.bar_chart(df_grafico.set_index("Termo"))

            except Exception as e:
                st.error(
                    "Não foi possível buscar os dados agora. O Google Trends pode estar "
                    "limitando as requisições temporariamente. Tente novamente em alguns minutos."
                )
                st.caption(f"Detalhe técnico: {e}")

    st.markdown("---")
    st.markdown("### 🛍️ Cruzar Tendências com Produtos Reais da Shopee")
    st.caption(
        "Busca produto por produto na Shopee para cada tendência. Mais lento, e pode "
        "falhar pontualmente se a Shopee bloquear a requisição — isso é esperado, "
        "não é erro do sistema."
    )

    if st.button("🔍 Buscar Produtos Correspondentes na Shopee"):
        try:
            df_trends_base = minerar_dados_trends()
            termos_base = df_trends_base["Produto / Tendência"].tolist()
        except Exception as e:
            st.error("Não foi possível obter as tendências para cruzar com a Shopee.")
            st.caption(f"Detalhe técnico: {e}")
            termos_base = []

        if termos_base:
            with st.spinner("Cruzando tendências com produtos reais na Shopee..."):
                df_cruzado = cruzar_trends_com_shopee(termos_base)

                st.dataframe(
                    df_cruzado,
                    column_config={
                        "Link do Produto": st.column_config.LinkColumn("Abrir na Shopee")
                    },
                    use_container_width=True
                )

                encontrados = (df_cruzado["Produto na Shopee"] != "(nenhum produto encontrado)").sum()
                st.info(f"{encontrados} de {len(df_cruzado)} tendências tiveram produto correspondente encontrado.")
