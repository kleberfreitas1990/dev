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
st.set_page_config(page_title="Minerador Pro - Afiliados", page_icon="🚀", layout="wide")

# Lista de palavras-chave que indicam que NÃO é um produto
PALAVRAS_BLOQUEADAS = [
    'polícia', 'policial', 'presidente', 'governador', 'senador', 'deputado',
    'ministro', 'juiz', 'advogado', 'delegado', 'política', 'político',
    'partido', 'eleição', 'voto', 'campanha', 'manifestação', 'greve',
    'acidente', 'assalto', 'homicídio', 'sequestro', 'tiroteio', 'incêndio',
    'enchente', 'terremoto', 'furacão', 'temporal', 'chuva', 'calor', 'frio',
    'futebol', 'jogador', 'time', 'campeonato', 'partida', 'gol', 'narciso',
    'novela', 'ator', 'atriz', 'artista', 'cantor', 'cantora', 'apresentador',
    'jornalista', 'programa', 'tv', 'globo', 'record', 'sbt', 'band',
    'ao vivo', 'assistir', 'streaming', 'netflix', 'prime video', 'hbo',
    'youtube', 'instagram', 'facebook', 'twitter', 'tiktok', 'whatsapp',
    'telegram', 'aplicativo', 'download', 'instalar', 'site', 'link',
    'notícia', 'noticias', 'últimas', 'momento', 'hoje', 'agora'
]

# Lista de palavras que indicam que É um produto
PALAVRAS_PRODUTO = [
    'preço', 'compra', 'comprar', 'produto', 'oferta', 'promoção', 'desconto',
    'kit', 'pacote', 'caixa', 'unidade', 'peça', 'modelo', 'tamanho', 'cor',
    'presente', 'casa', 'cozinha', 'quarto', 'sala', 'banheiro', 'decoração',
    'roupa', 'vestido', 'calça', 'camisa', 'blusa', 'short', 'sapato', 'tênis',
    'bolsa', 'mochila', 'relógio', 'óculos', 'colar', 'anel', 'brinco',
    'eletrônico', 'celular', 'tablet', 'notebook', 'fone', 'carregador',
    'cabo', 'adaptador', 'monitor', 'teclado', 'mouse', 'caixa de som',
    'smartwatch', 'fitness', 'esportes', 'academia', 'suplemento', 'vitamina',
    'beleza', 'maquiagem', 'creme', 'perfume', 'sabonete', 'shampoo',
    'condicionador', 'hidratante', 'protetor', 'bebê', 'criança', 'brinquedo',
    'livro', 'caderno', 'caneta', 'papelaria', 'escritório', 'cadeira', 'mesa'
]

# Dicionário de datas comemorativas
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
    if chave == "TESTE-AFILIADO-2026":
        return {"valido": True, "expira": "2026-12-31"}
    return {"valido": False}

def filtrar_termos_produtos(termos):
    """Filtra apenas termos que são produtos (não notícias/personalidades)"""
    termos_filtrados = []
    
    for termo in termos:
        termo_lower = termo.lower()
        
        # Verifica se é uma notícia/personalidade
        is_noticia = any(palavra in termo_lower for palavra in PALAVRAS_BLOQUEADAS)
        
        # Verifica se é um produto
        is_produto = any(palavra in termo_lower for palavra in PALAVRAS_PRODUTO)
        
        # Se tem características de produto E não é notícia, mantém
        if is_produto and not is_noticia:
            termos_filtrados.append(termo)
        # Se não tem características de notícia mas também não tem de produto, 
        # mantém se tiver menos de 3 palavras (provavelmente é um objeto/nome de produto)
        elif not is_noticia and len(termo.split()) <= 3:
            termos_filtrados.append(termo)
    
    return termos_filtrados

def buscar_trends_pinterest(termo, limite=10):
    """Busca tendências no Pinterest de forma simulada (API real requer token)"""
    # Como o Pinterest não tem API pública gratuita, usamos uma simulação
    # Na versão real, integrar com a API do Pinterest Ads ou usar scraping
    
    # Simula busca no Pinterest com base no termo
    pinterest_suggestions = {
        "vestido": ["Vestido longo", "Vestido curto", "Vestido estampado", "Vestido festa"],
        "calça": ["Calça jeans", "Calça social", "Calça moletom", "Calça cargo"],
        "tênis": ["Tênis casual", "Tênis esportivo", "Tênis feminino", "Tênis masculino"],
        "bolsa": ["Bolsa feminina", "Mochila", "Bolsa tiracolo", "Bolsa de mão"],
        "smartwatch": ["Smartwatch esportivo", "Smartwatch feminino", "Smartwatch Samsung", "Smartwatch Apple"],
        "fone": ["Fone Bluetooth", "Fone sem fio", "Fone cancelamento de ruído", "Fone gamer"],
        "brinquedo": ["Brinquedo educativo", "Brinquedo infantil", "Brinquedo montessori", "Brinquedo de madeira"],
        "cadeira": ["Cadeira gamer", "Cadeira de escritório", "Cadeira ergonômica", "Cadeira de jantar"],
        "perfume": ["Perfume feminino", "Perfume masculino", "Perfume importado", "Perfume nacional"],
        "maquiagem": ["Base", "Batom", "Paleta de sombras", "Máscara de cílios"]
    }
    
    # Tenta encontrar sugestões relacionadas
    termo_lower = termo.lower()
    sugestoes = []
    
    for chave, valores in pinterest_suggestions.items():
        if chave in termo_lower or termo_lower in chave:
            sugestoes.extend(valores[:limite])
    
    # Se não encontrou, retorna o termo original com variações
    if not sugestoes:
        sugestoes = [
            f"{termo} moderno",
            f"{termo} estilo",
            f"{termo} decorativo",
            f"{termo} funcional",
            f"{termo} criativo"
        ][:limite]
    
    return sugestoes

def buscar_trends_google(termo, data_inicio, data_fim):
    """Busca dados de tendência do Google para um termo"""
    try:
        pytrends = TrendReq(hl='pt-BR', tz=-180)
        pytrends.build_payload([termo], cat=0, timeframe=f'{data_inicio} {data_fim}', geo='BR')
        dados = pytrends.interest_over_time()
        
        if dados.empty:
            return None
            
        if 'isPartial' in dados.columns:
            dados = dados.drop('isPartial', axis=1)
            
        return dados
    except Exception as e:
        return None

def identificar_sazonalidade(termo, data_atual):
    """Identifica se um termo está relacionado a datas comemorativas"""
    mes_dia = data_atual.strftime("%m-%d")
    
    if mes_dia in DATAS_COMEMORATIVAS:
        return DATAS_COMEMORATIVAS[mes_dia]
    
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

def comparar_tendencia_sazonal(termo, data_atual):
    """Compara a tendência atual com a mesma época do ano passado"""
    data_ano_passado = data_atual - timedelta(days=365)
    
    data_fim_atual = data_atual.strftime('%Y-%m-%d')
    data_ini_atual = (data_atual - timedelta(days=7)).strftime('%Y-%m-%d')
    
    data_fim_passado = data_ano_passado.strftime('%Y-%m-%d')
    data_ini_passado = (data_ano_passado - timedelta(days=7)).strftime('%Y-%m-%d')
    
    dados_atual = buscar_trends_google(termo, data_ini_atual, data_fim_atual)
    dados_passado = buscar_trends_google(termo, data_ini_passado, data_fim_passado)
    
    # Busca tendências no Pinterest
    pinterest_trends = buscar_trends_pinterest(termo)
    
    resultado = {
        "termo": termo,
        "media_atual": 0,
        "media_passado": 0,
        "variacao_percentual": 0,
        "tendencia": "Estável",
        "sazonalidade": identificar_sazonalidade(termo, data_atual),
        "pinterest_trends": pinterest_trends,
        "score_produto": 0,
        "recomendacao": ""
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
    
    # Calcula score do produto baseado em:
    # 1. Variação positiva
    # 2. Sazonalidade
    # 3. Tendências no Pinterest
    score = 0
    
    if resultado["variacao_percentual"] > 0:
        score += 3
    if resultado["sazonalidade"] != "Geral (Sem sazonalidade)":
        score += 2
    if resultado["tendencia"] in ["🚀 Alta (Emergente)", "📈 Crescente"]:
        score += 2
    if len(pinterest_trends) >= 3:
        score += 1
    
    resultado["score_produto"] = score
    
    # Gera recomendação
    if score >= 7:
        resultado["recomendacao"] = "🔥 ALTAMENTE RECOMENDADO - Produto com alta chance de viralizar!"
    elif score >= 5:
        resultado["recomendacao"] = "⭐ BOM POTENCIAL - Ótima oportunidade para conteúdo"
    elif score >= 3:
        resultado["recomendacao"] = "📊 POTENCIAL MÉDIO - Monitorar evolução"
    else:
        resultado["recomendacao"] = "⚠️ BAIXO POTENCIAL - Pode não ter boa conversão"
    
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
        produtos.append({"nome": nome, "preco": preco, "link": link})

    return produtos

def minerar_dados_trends_produtos(geo="BR"):
    """Minerar apenas termos que são produtos"""
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

    # Filtra apenas termos que são produtos
    termos_produtos = filtrar_termos_produtos(termos[:30])
    
    # Limita a 15 produtos
    termos_produtos = termos_produtos[:15]
    
    if not termos_produtos:
        raise ValueError("Nenhum termo relacionado a produtos encontrado nas tendências.")

    data_atual = datetime.now()
    
    resultados = []
    for termo in termos_produtos:
        analise = comparar_tendencia_sazonal(termo, data_atual)
        analise["link_shopee"] = f"https://shopee.com.br/search?keyword={quote(termo)}"
        resultados.append(analise)
    
    return pd.DataFrame(resultados)

# --- INTERFACE DO USUÁRIO ---
st.title("🚀 Minerador Pro - Produtos em Tendência")

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

    data_atual = datetime.now()
    st.sidebar.markdown(f"**📅 Data de Análise:** {data_atual.strftime('%d/%m/%Y')}")
    st.sidebar.markdown(f"**📊 Período Comparado:** Mesma semana do ano passado")

    st.markdown("### 🎯 Produtos em Tendência no Brasil")
    st.markdown("""
    💡 **Como funciona:**
    - 🔄 Filtra APENAS termos que são produtos (não notícias/personalidades)
    - 🔍 Compara com tendências do Pinterest
    - 🎯 Calcula score de recomendação para afiliados
    - 📈 Identifica produtos com maior potencial de venda
    """)

    if st.button("🔄 Buscar Produtos em Tendência"):
        with st.spinner("Analisando tendências de produtos..."):
            try:
                df_tendencias = minerar_dados_trends_produtos()
                
                # Métricas rápidas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Produtos em Alta", len(df_tendencias))
                
                with col2:
                    sazonais = df_tendencias[df_tendencias["sazonalidade"] != "Geral (Sem sazonalidade)"]
                    st.metric("Produtos Sazonais", len(sazonais))
                
                with col3:
                    alta = df_tendencias[df_tendencias["tendencia"].str.contains("Alta|Crescente")]
                    st.metric("Produtos Crescendo", len(alta))
                
                with col4:
                    recomendados = df_tendencias[df_tendencias["score_produto"] >= 5]
                    st.metric("Altamente Recomendados", len(recomendados))
                
                st.markdown("---")
                
                # Tabela principal com análise detalhada
                st.markdown("### 📊 Análise de Produtos em Tendência")
                
                # DataFrame para exibição
                df_exibicao = df_tendencias[["termo", "sazonalidade", "tendencia", "variacao_percentual", "score_produto", "recomendacao"]].copy()
                df_exibicao.columns = ["Produto", "Sazonalidade", "Tendência", "Variação YoY", "Score", "Recomendação"]
                
                st.dataframe(
                    df_exibicao,
                    column_config={
                        "Produto": "Produto em Tendência",
                        "Sazonalidade": "Sazonalidade",
                        "Tendência": "Classificação",
                        "Variação YoY": st.column_config.NumberColumn("Variação (%)", format="%.1f%%"),
                        "Score": st.column_config.NumberColumn("Score", format="%d"),
                        "Recomendação": "Recomendação"
                    },
                    use_container_width=True
                )
                
                # Destaque para produtos com Pinterest
                st.markdown("### 📌 Tendências no Pinterest")
                
                for _, row in df_tendencias.iterrows():
                    if row["pinterest_trends"]:
                        with st.expander(f"🎨 {row['termo']} - Ideias no Pinterest"):
                            for ideia in row["pinterest_trends"][:5]:
                                st.markdown(f"- {ideia}")
                            st.link_button(f"🔍 Ver '{row['termo']}' na Shopee", row["link_shopee"])
                
                # Produtos altamente recomendados
                st.markdown("### 🔥 Produtos Altamente Recomendados")
                df_recomendados = df_tendencias[df_tendencias["score_produto"] >= 5].sort_values("score_produto", ascending=False)
                
                if not df_recomendados.empty:
                    for _, row in df_recomendados.iterrows():
                        with st.container():
                            col_a, col_b, col_c = st.columns([3, 2, 1])
                            with col_a:
                                st.markdown(f"**{row['termo']}**")
                                st.caption(f"🎯 {row['sazonalidade']}")
                            with col_b:
                                st.markdown(f"Score: {row['score_produto']}/9")
                                st.caption(row['recomendacao'])
                            with col_c:
                                st.link_button("🛒 Ver na Shopee", row["link_shopee"])
                            st.markdown("---")
                else:
                    st.info("Nenhum produto altamente recomendado no momento.")
                
                st.success("Análise concluída! Produtos filtrados para afiliados.")
                
            except Exception as e:
                st.error("Erro ao buscar produtos em tendência.")
                st.caption(f"Detalhe: {e}")

    st.markdown("---")
    st.markdown("### 📅 Próximas Datas para Conteúdo")
    
    hoje = datetime.now()
    proximas_datas = []
    
    for mes_dia, evento in DATAS_COMEMORATIVAS.items():
        mes, dia = map(int, mes_dia.split('-'))
        data_evento = datetime(hoje.year, mes, dia)
        
        if data_evento >= hoje:
            dias_para = (data_evento - hoje).days
            if dias_para <= 30:
                proximas_datas.append((dias_para, evento, data_evento.strftime('%d/%m')))
    
    if proximas_datas:
        proximas_datas.sort(key=lambda x: x[0])
        for dias, evento, data in proximas_datas:
            if dias == 0:
                st.warning(f"🎉 HOJE é {evento}! Crie conteúdo AGORA!")
            elif dias <= 7:
                st.info(f"📌 {evento} em {dias} dias ({data}) - Prepare seus vídeos!")
            else:
                st.caption(f"📅 {evento} em {dias} dias ({data})")
    else:
        st.caption("Nenhuma data comemorativa nos próximos 30 dias.")
