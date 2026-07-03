import streamlit as st
import pandas as pd
import feedparser
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import requests
from pytrends.request import TrendReq
import json

# Configuração da página do seu sistema
st.set_page_config(page_title="Minerador Pro - Afiliados", page_icon="🚀", layout="wide")

# Credenciais temporárias para o app não quebrar sem banco de dados
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sua-anon-key-do-supabase"

# Dicionário de datas comemorativas brasileiras (mês-dia)
DATAS_COMEMORATIVAS = {
    "01-01": "Ano Novo",
    "02-02": "Dia de Iemanjá",
    "02-14": "Dia dos Namorados (EUA)",
    "03-08": "Dia Internacional da Mulher",
    "03-15": "Dia do Consumidor",
    "04-21": "Tiradentes",
    "05-01": "Dia do Trabalhador",
    "05-13": "Dia das Mães",
    "06-01": "Dia das Crianças (em alguns países)",
    "06-12": "Dia dos Namorados (BR)",
    "07-09": "Revolução Constitucionalista",
    "08-11": "Dia do Estudante",
    "08-14": "Dia dos Pais",
    "09-07": "Independência do Brasil",
    "10-12": "Dia das Crianças",
    "10-15": "Dia do Professor",
    "10-31": "Dia das Bruxas/Halloween",
    "11-02": "Finados",
    "11-15": "Proclamação da República",
    "11-25": "Black Friday",
    "12-25": "Natal",
    "12-31": "Réveillon"
}

def validar_licenca_supabase(chave):
    """Verificação híbrida: Aceita chave local de teste e evita travar a tela"""
    # CHAVE DE TESTE LOCAL (Funciona sempre)
    if chave == "TESTE-AFILIADO-2026":
        return {"valido": True, "expira": "2026-12-31"}
    return {"valido": False}

def identificar_sazonalidade(termo, data_atual):
    """Identifica se um termo está relacionado a datas comemorativas"""
    mes_dia = data_atual.strftime("%m-%d")
    
    # Verifica se é uma data comemorativa hoje
    if mes_dia in DATAS_COMEMORATIVAS:
        return DATAS_COMEMORATIVAS[mes_dia]
    
    # Verifica se o termo contém palavras-chave de datas comemorativas
    palavras_chave = {
        "natal": "Natal",
        "presente": "Natal",
        "amigo secreto": "Natal",
        "ano novo": "Réveillon",
        "reveillon": "Réveillon",
        "carnaval": "Carnaval",
        "fantasia": "Carnaval",
        "pascoa": "Páscoa",
        "páscoa": "Páscoa",
        "ovo de pascoa": "Páscoa",
        "dia das mães": "Dia das Mães",
        "mãe": "Dia das Mães",
        "dia dos pais": "Dia dos Pais",
        "pai": "Dia dos Pais",
        "namorados": "Dia dos Namorados",
        "romantico": "Dia dos Namorados",
        "black friday": "Black Friday",
        "promocao": "Black Friday",
        "crianca": "Dia das Crianças",
        "brinquedo": "Dia das Crianças",
        "halloween": "Halloween",
        "dia das bruxas": "Halloween",
        "fantasia halloween": "Halloween"
    }
    
    termo_lower = termo.lower()
    for palavra, evento in palavras_chave.items():
        if palavra in termo_lower:
            return evento
    
    return "Geral (Sem sazonalidade)"

def buscar_trends_google(termo, data_inicio, data_fim):
    """Busca dados de tendência do Google para um termo em um período específico"""
    try:
        pytrends = TrendReq(hl='pt-BR', tz=-180)
        pytrends.build_payload([termo], cat=0, timeframe=f'{data_inicio} {data_fim}', geo='BR')
        dados = pytrends.interest_over_time()
        
        if dados.empty:
            return None
            
        # Remove a coluna 'isPartial' se existir
        if 'isPartial' in dados.columns:
            dados = dados.drop('isPartial', axis=1)
            
        return dados
    except Exception as e:
        st.warning(f"Não foi possível buscar dados históricos para '{termo}': {str(e)}")
        return None

def comparar_tendencia_sazonal(termo, data_atual):
    """Compara a tendência atual com a mesma época do ano passado"""
    # Data atual e data do ano passado
    data_ano_passado = data_atual - timedelta(days=365)
    
    # Período de 7 dias para análise
    data_fim_atual = data_atual.strftime('%Y-%m-%d')
    data_ini_atual = (data_atual - timedelta(days=7)).strftime('%Y-%m-%d')
    
    data_fim_passado = data_ano_passado.strftime('%Y-%m-%d')
    data_ini_passado = (data_ano_passado - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Busca dados atuais
    dados_atual = buscar_trends_google(termo, data_ini_atual, data_fim_atual)
    dados_passado = buscar_trends_google(termo, data_ini_passado, data_fim_passado)
    
    resultado = {
        "termo": termo,
        "media_atual": 0,
        "media_passado": 0,
        "variacao_percentual": 0,
        "tendencia": "Estável",
        "sazonalidade": identificar_sazonalidade(termo, data_atual)
    }
    
    if dados_atual is not None and not dados_atual.empty:
        resultado["media_atual"] = dados_atual[termo].mean()
        
    if dados_passado is not None and not dados_passado.empty:
        resultado["media_passado"] = dados_passado[termo].mean()
    
    # Calcula variação e classifica tendência
    if resultado["media_atual"] > 0 and resultado["media_passado"] > 0:
        resultado["variacao_percentual"] = ((resultado["media_atual"] - resultado["media_passado"]) / resultado["media_passado"]) * 100
        
        if resultado["variacao_percentual"] > 20:
            resultado["tendencia"] = "🚀 Alta (Emergente)"
        elif resultado["variacao_percentual"] > 5:
            resultado["tendencia"] = "📈 Crescente"
        elif resultado["variacao_percentual"] > -5:
            resultado["tendencia"] = "➡️ Estável"
        elif resultado["variacao_percentual"] > -20:
            resultado["tendencia"] = "📉 Declinando"
        else:
            resultado["tendencia"] = "⬇️ Queda Forte"
    
    return resultado

def buscar_produtos_shopee(termo, limite=3):
    """Busca produtos reais na Shopee para um termo"""
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

def minerar_dados_trends_avancado(geo="BR"):
    """Minerar tendências com análise sazonal e comparação histórica"""
    url_feed = f"https://trends.google.com/trending/rss?geo={geo}"
    feed = feedparser.parse(url_feed)

    if feed.bozo and not feed.entries:
        raise ValueError("Não foi possível ler o feed do Google Trends no momento.")

    termos = []
    for entrada in feed.entries:
        titulo = entrada.get("title", "").strip()
        if titulo and titulo not in termos:
            termos.append(titulo)

    if not termos:
        raise ValueError("O feed do Google Trends voltou vazio.")

    termos = termos[:15]
    data_atual = datetime.now()
    
    # Analisa cada termo com sazonalidade
    resultados = []
    for termo in termos:
        analise = comparar_tendencia_sazonal(termo, data_atual)
        analise["link_shopee"] = f"https://shopee.com.br/search?keyword={quote(termo)}"
        resultados.append(analise)
    
    return pd.DataFrame(resultados)

def cruzar_trends_com_shopee_avancado(df_tendencias, max_produtos_por_termo=2):
    """Cruza tendências com produtos da Shopee mantendo informações de sazonalidade"""
    linhas = []
    for _, row in df_tendencias.iterrows():
        termo = row["termo"]
        produtos = buscar_produtos_shopee(termo, limite=max_produtos_por_termo)
        
        if produtos:
            for p in produtos:
                linhas.append({
                    "Tendência": termo,
                    "Sazonalidade": row["sazonalidade"],
                    "Tendência Atual": row["tendencia"],
                    "Variação YoY": f"{row['variacao_percentual']:.1f}%",
                    "Produto na Shopee": p["nome"],
                    "Preço": p["preco"],
                    "Link do Produto": p["link"],
                })
        else:
            linhas.append({
                "Tendência": termo,
                "Sazonalidade": row["sazonalidade"],
                "Tendência Atual": row["tendencia"],
                "Variação YoY": f"{row['variacao_percentual']:.1f}%",
                "Produto na Shopee": "(nenhum produto encontrado)",
                "Preço": "—",
                "Link do Produto": f"https://shopee.com.br/search?keyword={quote(termo)}",
            })
    return pd.DataFrame(linhas)

# --- INTERFACE DO USUÁRIO (SISTEMA) ---
st.title("🚀 Minerador Pro - Painel de Tendências Sazonais")

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

# TELA 2: O Dashboard do Cliente
else:
    st.sidebar.success("Acesso Garantido")
    st.sidebar.info(f"Sua licença expira em: {st.session_state.data_expira}")
    if st.sidebar.button("Sair / Desconectar"):
        st.session_state.autenticado = False
        st.rerun()

    # Informações da data atual
    data_atual = datetime.now()
    st.sidebar.markdown(f"**📅 Data de Análise:** {data_atual.strftime('%d/%m/%Y')}")
    st.sidebar.markdown(f"**📊 Período Comparado:** Mesma semana do ano passado")

    st.markdown("### 🔥 Análise de Tendências com Comparação Sazonal")
    st.markdown("""
    💡 **Como funciona:**
    - 🔄 Compara o interesse atual com a MESMA ÉPOCA do ano passado
    - 🎯 Identifica termos sazonais ligados a datas comemorativas
    - 📊 Classifica tendências por variação de busca
    - 🛍️ Recomenda produtos com base no momento ideal de venda
    """)

    if st.button("🔄 Rodar Mineração Avançada"):
        with st.spinner("Analisando tendências com comparação histórica..."):
            try:
                # Minera dados com análise sazonal
                df_tendencias = minerar_dados_trends_avancado()
                
                # Exibe resumo estatístico
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Tendências", len(df_tendencias))
                
                with col2:
                    sazonais = df_tendencias[df_tendencias["sazonalidade"] != "Geral (Sem sazonalidade)"]
                    st.metric("Tendências Sazonais", len(sazonais))
                
                with col3:
                    alta = df_tendencias[df_tendencias["tendencia"].str.contains("Alta|Crescente")]
                    st.metric("Tendências em Alta", len(alta))
                
                st.markdown("---")
                
                # Tabela principal com todas as análises
                st.markdown("### 📊 Análise Detalhada por Termo")
                
                # Configura cores para tendências
                def color_tendencia(val):
                    if "🚀 Alta" in val:
                        return 'background-color: #28a745; color: white'
                    elif "📈 Crescente" in val:
                        return 'background-color: #17a2b8; color: white'
                    elif "➡️ Estável" in val:
                        return 'background-color: #ffc107; color: black'
                    elif "📉 Declinando" in val:
                        return 'background-color: #fd7e14; color: white'
                    else:
                        return 'background-color: #dc3545; color: white'
                
                # Aplica estilo
                st.dataframe(
                    df_tendencias[["termo", "sazonalidade", "tendencia", "variacao_percentual"]],
                    column_config={
                        "termo": "Termo de Busca",
                        "sazonalidade": "Sazonalidade",
                        "tendencia": "Classificação",
                        "variacao_percentual": st.column_config.NumberColumn("Variação YoY (%)", format="%.1f%%")
                    },
                    use_container_width=True
                )
                
                # Gráfico de comparação
                st.markdown("### 📈 Comparação: Interesse Atual vs Ano Passado")
                
                # Filtra termos com dados completos
                df_validos = df_tendencias[
                    (df_tendencias["media_atual"] > 0) & 
                    (df_tendencias["media_passado"] > 0)
                ].copy()
                
                if not df_validos.empty:
                    # Cria gráfico de barras comparativo
                    df_grafico = df_validos.head(10).copy()
                    df_grafico["Interesse Atual"] = df_grafico["media_atual"]
                    df_grafico["Ano Passado"] = df_grafico["media_passado"]
                    
                    st.bar_chart(
                        df_grafico.set_index("termo")[["Interesse Atual", "Ano Passado"]]
                    )
                    
                    # Destaque sazonal
                    st.markdown("### 🎯 Produtos Sazonais em Destaque")
                    df_sazonais = df_validos[df_validos["sazonalidade"] != "Geral (Sem sazonalidade)"]
                    
                    if not df_sazonais.empty:
                        st.info(f"📌 Encontrados {len(df_sazonais)} produtos com forte sazonalidade!")
                        
                        # Lista de recomendações sazonais
                        for _, row in df_sazonais.head(5).iterrows():
                            with st.container():
                                col_a, col_b = st.columns([3, 1])
                                with col_a:
                                    st.markdown(f"**{row['termo']}** - {row['sazonalidade']}")
                                    st.caption(f"Tendência: {row['tendencia']} | Variação: {row['variacao_percentual']:.1f}%")
                                with col_b:
                                    st.link_button("🔍 Ver na Shopee", row["link_shopee"])
                                st.markdown("---")
                    else:
                        st.info("Nenhum produto sazonal identificado nas tendências atuais.")
                else:
                    st.warning("Dados históricos insuficientes para comparação visual.")
                
                st.success("Análise completa! Role para baixo para ver os produtos.")

                # Seção de cruzamento com Shopee
                st.markdown("---")
                st.markdown("### 🛍️ Cruzar com Produtos Reais da Shopee")
                st.caption("Busca produtos correspondentes para cada tendência, mantendo informações de sazonalidade")
                
                if st.button("🔍 Buscar Produtos na Shopee"):
                    with st.spinner("Cruzando tendências com produtos reais..."):
                        df_cruzado = cruzar_trends_com_shopee_avancado(df_tendencias)
                        
                        # Filtra apenas produtos encontrados
                        df_com_produtos = df_cruzado[df_cruzado["Produto na Shopee"] != "(nenhum produto encontrado)"]
                        
                        if not df_com_produtos.empty:
                            st.success(f"✅ {len(df_com_produtos)} produtos encontrados!")
                            
                            # Destaque produtos sazonais
                            df_sazonais_com_produtos = df_com_produtos[
                                df_com_produtos["Sazonalidade"] != "Geral (Sem sazonalidade)"
                            ]
                            
                            if not df_sazonais_com_produtos.empty:
                                st.markdown("#### 🎄 Produtos Sazonais em Alta")
                                st.dataframe(
                                    df_sazonais_com_produtos,
                                    column_config={
                                        "Tendência": "Termo Buscado",
                                        "Sazonalidade": "Data Comemorativa",
                                        "Tendência Atual": "Classificação",
                                        "Variação YoY": "Crescimento",
                                        "Produto na Shopee": "Produto",
                                        "Preço": "Preço",
                                        "Link do Produto": st.column_config.LinkColumn("Comprar")
                                    },
                                    use_container_width=True
                                )
                            
                            # Tabela completa
                            st.markdown("#### 📋 Todos os Produtos Encontrados")
                            st.dataframe(
                                df_com_produtos,
                                column_config={
                                    "Tendência": "Termo Buscado",
                                    "Sazonalidade": "Sazonalidade",
                                    "Tendência Atual": "Tendência",
                                    "Variação YoY": "Variação",
                                    "Produto na Shopee": "Produto",
                                    "Preço": "Preço",
                                    "Link do Produto": st.column_config.LinkColumn("Abrir na Shopee")
                                },
                                use_container_width=True
                            )
                        else:
                            st.warning("Nenhum produto correspondente encontrado nas tendências atuais.")
                        
                        # Estatísticas finais
                        total_tendencias = len(df_tendencias)
                        encontrados = (df_cruzado["Produto na Shopee"] != "(nenhum produto encontrado)").sum()
                        st.info(f"📊 {encontrados} de {total_tendencias} tendências têm produtos na Shopee")

            except Exception as e:
                st.error(
                    "Não foi possível completar a mineração avançada. "
                    "O Google Trends pode estar limitando requisições."
                )
                st.caption(f"Detalhe técnico: {e}")

    st.markdown("---")
    st.markdown("### 📅 Próximas Datas Comemorativas")
    
    # Mostra próximas datas comemorativas
    hoje = datetime.now()
    proximas_datas = []
    
    for mes_dia, evento in DATAS_COMEMORATIVAS.items():
        mes, dia = map(int, mes_dia.split('-'))
        data_evento = datetime(hoje.year, mes, dia)
        
        if data_evento >= hoje:
            dias_para = (data_evento - hoje).days
            if dias_para <= 30:  # Próximos 30 dias
                proximas_datas.append((dias_para, evento, data_evento.strftime('%d/%m')))
    
    if proximas_datas:
        proximas_datas.sort(key=lambda x: x[0])
        for dias, evento, data in proximas_datas:
            if dias == 0:
                st.warning(f"🎉 HOJE é {evento}! Aproveite as tendências!")
            elif dias <= 7:
                st.info(f"📌 {evento} em {dias} dias ({data}) - Prepare seus conteúdos!")
            else:
                st.caption(f"📅 {evento} em {dias} dias ({data})")
    else:
        st.caption("Nenhuma data comemorativa nos próximos 30 dias.")
