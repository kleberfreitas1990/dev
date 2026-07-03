import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import requests
import random
import json
import os
from collections import Counter

# Configuração da página
st.set_page_config(page_title="Minerador Pro - Conteúdo Estratégico", page_icon="📅", layout="wide")

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

# ===== BANCO DE DADOS HISTÓRICO (DADOS DO ANO PASSADO) =====
DADOS_HISTORICOS = {
    # Janeiro
    "01": {
        "tendencias": [
            "material escolar", "mochila", "estojo", "caderno", "caneta",
            "tênis", "tênis casual", "calça jeans", "roupa de academia",
            "smartwatch", "fone bluetooth", "carregador portátil",
            "organizador de mesa", "cadeira de escritório", "luminária de mesa"
        ],
        "eventos": [
            {"data": "01-01", "nome": "Ano Novo", "sugestao": "Decoração para festa, roupas para virada, itens para resoluções de ano novo"},
            {"data": "01-06", "nome": "Dia de Reis", "sugestao": "Presentes religiosos, artigos de decoração natalina (últimas promoções)"},
            {"data": "01-20", "nome": "Dia de São Sebastião", "sugestao": "Itens religiosos, artigos para festas juninas (já começam a preparar)"}
        ]
    },
    # Fevereiro
    "02": {
        "tendencias": [
            "fantasia carnaval", "acessórios carnaval", "máscara", "glitter", "cabeleira",
            "maiô", "biquíni", "sungas", "chinelo", "protetor solar",
            "fone bluetooth", "caixa de som portátil", "power bank",
            "roupa de academia", "tênis esportivo", "garrafa térmica"
        ],
        "eventos": [
            {"data": "02-02", "nome": "Dia de Iemanjá", "sugestao": "Artigos religiosos, decoração, flores, velas"},
            {"data": "02-14", "nome": "Dia dos Namorados (EUA)", "sugestao": "Presentes românticos, kits de jantar, lingerie, perfumes"},
            {"data": "02-28", "nome": "Carnaval", "sugestao": "Fantasias, acessórios, bebidas, decoração de festa"}
        ]
    },
    # Março
    "03": {
        "tendencias": [
            "kit praia", "bolsa praia", "toalha", "canga", "chapéu",
            "smartwatch", "fone bluetooth", "caixa de som portátil",
            "cadeira de praia", "guarda-sol", "cooler", "garrafa térmica",
            "vestido", "sandália", "chinelo", "óculos de sol"
        ],
        "eventos": [
            {"data": "03-08", "nome": "Dia Internacional da Mulher", "sugestao": "Presentes femininos, flores, perfumes, kits de beleza"},
            {"data": "03-15", "nome": "Dia do Consumidor", "sugestao": "Eletrônicos, celulares, produtos com desconto"},
            {"data": "03-20", "nome": "Outono", "sugestao": "Roupas de meia estação, cobertores, decoração outonal"}
        ]
    },
    # Abril
    "04": {
        "tendencias": [
            "ovo de páscoa", "chocolate", "presente páscoa", "cestinha", "coelhinho",
            "tênis", "calça jeans", "blusa", "casaco leve", "jaqueta jeans",
            "smartwatch", "fone bluetooth", "fone sem fio",
            "cadeira gamer", "mouse gamer", "teclado mecânico"
        ],
        "eventos": [
            {"data": "04-07", "nome": "Dia do Jornalista", "sugestao": "Presentes para profissionais, canecas personalizadas"},
            {"data": "04-21", "nome": "Tiradentes", "sugestao": "Feriado - viagens, artigos de viagem, malas"},
            {"data": "04-28", "nome": "Páscoa", "sugestao": "Ovos de chocolate, cestas, presentes para crianças, decoração"}
        ]
    },
    # Maio
    "05": {
        "tendencias": [
            "presente dia das mães", "flores", "perfume", "bolsa", "vestido",
            "smartwatch", "fone bluetooth", "caixa de som",
            "tênis", "calça jeans", "blusa feminina", "lenço",
            "livro", "cozinha", "panela", "jogo de panelas", "faqueiro"
        ],
        "eventos": [
            {"data": "05-01", "nome": "Dia do Trabalhador", "sugestao": "Feriado - churrasco, artigos de viagem, promoções de eletrônicos"},
            {"data": "05-13", "nome": "Dia das Mães", "sugestao": "Presentes para mães: perfumes, bolsas, vestidos, eletrônicos"},
            {"data": "05-25", "nome": "Dia do Orgulho LGBTQ+", "sugestao": "Acessórios coloridos, bandeiras, decoração"}
        ]
    },
    # Junho
    "06": {
        "tendencias": [
            "presente dia dos namorados", "kit jantar", "vinho", "chocolate", "perfume",
            "camisa", "calça", "vestido", "blusa", "sandália",
            "fone bluetooth", "smartwatch", "fone sem fio",
            "brinquedo", "jogo", "boneca", "carrinho"
        ],
        "eventos": [
            {"data": "06-01", "nome": "Dia das Crianças (em alguns países)", "sugestao": "Brinquedos, jogos educativos, livros infantis"},
            {"data": "06-12", "nome": "Dia dos Namorados (BR)", "sugestao": "Presentes românticos: perfumes, roupas, jantares, kits"},
            {"data": "06-24", "nome": "São João", "sugestao": "Decoração junina, roupas xadrez, comidas típicas, bebidas"}
        ]
    },
    # Julho
    "07": {
        "tendencias": [
            "roupa de frio", "casaco", "jaqueta", "blusa de lã", "cachecol", "luva",
            "tênis", "tênis casual", "coturno", "bota",
            "fone bluetooth", "fone sem fio", "carregador portátil",
            "livro", "quadrinho", "mangá", "jogo de tabuleiro"
        ],
        "eventos": [
            {"data": "07-09", "nome": "Revolução Constitucionalista", "sugestao": "Feriado - filmes, streaming, roupas de frio"},
            {"data": "07-20", "nome": "Dia do Amigo", "sugestao": "Presentes para amigos, kits de cerveja, jogos"}
        ]
    },
    # Agosto
    "08": {
        "tendencias": [
            "presente dia dos pais", "relógio", "cinto", "camisa", "calça social",
            "ferramenta", "furadeira", "parafusadeira", "kit ferramentas",
            "smartwatch", "fone bluetooth", "caixa de som",
            "mochila", "lancheira", "estojo", "material escolar"
        ],
        "eventos": [
            {"data": "08-11", "nome": "Dia do Estudante", "sugestao": "Material escolar, mochilas, estojos"},
            {"data": "08-14", "nome": "Dia dos Pais", "sugestao": "Presentes para pais: ferramentas, relógios, eletrônicos"},
            {"data": "08-22", "nome": "Dia do Folclore", "sugestao": "Decoração temática, brinquedos tradicionais"}
        ]
    },
    # Setembro
    "09": {
        "tendencias": [
            "camisa", "calça", "vestido", "blusa", "jaqueta jeans",
            "tênis", "tênis casual", "sapato social", "sandália",
            "smartwatch", "fone bluetooth", "carregador portátil",
            "mochila", "bolsa", "carteira", "cinto"
        ],
        "eventos": [
            {"data": "09-07", "nome": "Independência do Brasil", "sugestao": "Decoração verde-amarela, roupas patrióticas, desfiles"},
            {"data": "09-21", "nome": "Dia da Árvore", "sugestao": "Decoração com plantas, vasos, jardinagem"},
            {"data": "09-22", "nome": "Primavera", "sugestao": "Roupas leves, decoração floral, vasos de plantas"}
        ]
    },
    # Outubro
    "10": {
        "tendencias": [
            "fantasia halloween", "decoração halloween", "abóbora", "máscara", "maquiagem",
            "brinquedo", "boneca", "carrinho", "jogo", "pelúcia",
            "smartwatch", "fone bluetooth", "carregador portátil",
            "camisa", "calça", "vestido", "blusa"
        ],
        "eventos": [
            {"data": "10-12", "nome": "Dia das Crianças", "sugestao": "Brinquedos, jogos educativos, livros, roupas infantis"},
            {"data": "10-15", "nome": "Dia do Professor", "sugestao": "Presentes para professores, canecas, livros"},
            {"data": "10-31", "nome": "Halloween", "sugestao": "Fantasias, decoração, doces, maquiagem"}
        ]
    },
    # Novembro
    "11": {
        "tendencias": [
            "black friday", "promoção", "eletrônico", "celular", "tv", "smartwatch",
            "presente natal", "brinquedo", "boneca", "carrinho", "pelúcia",
            "camisa", "calça", "vestido", "blusa", "casaco",
            "perfume", "kit beleza", "maquiagem"
        ],
        "eventos": [
            {"data": "11-02", "nome": "Finados", "sugestao": "Flores, velas, artigos religiosos"},
            {"data": "11-15", "nome": "Proclamação da República", "sugestao": "Feriado - viagens, artigos de viagem"},
            {"data": "11-25", "nome": "Black Friday", "sugestao": "Eletrônicos, celulares, roupas, eletrodomésticos em promoção"}
        ]
    },
    # Dezembro
    "12": {
        "tendencias": [
            "presente natal", "árvore natal", "decoração natalina", "luzes", "enfeite",
            "brinquedo", "boneca", "carrinho", "pelúcia", "jogo",
            "camisa", "vestido", "blusa", "casaco", "jaqueta",
            "perfume", "kit beleza", "maquiagem", "vinho", "espumante",
            "smartwatch", "fone bluetooth", "carregador portátil"
        ],
        "eventos": [
            {"data": "12-25", "nome": "Natal", "sugestao": "Presentes: brinquedos, eletrônicos, roupas, perfumes, decoração"},
            {"data": "12-31", "nome": "Réveillon", "sugestao": "Roupas brancas, brindes, decoração, fogos, bebidas"}
        ]
    }
}

# ===== FUNÇÕES DE API =====
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
                "vendas": item.get("sold_quantity", 0)
            })
        
        return produtos
    except Exception:
        return []

def buscar_produtos_shopee(termo, limite=5):
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
            "nome": nome[:60],
            "preco": preco,
            "link": link,
            "loja": "Shopee",
            "vendas": info.get("sold", 0)
        })

    return produtos

def buscar_produtos_em_alta_ml(categoria_id, limite=5):
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
        termos = []
        
        for item in data.get("results", [])[:limite]:
            nome = item.get("title", "")
            palavras = nome.split()[:4]
            if palavras:
                termo = " ".join(palavras[:3])
                if len(termo) > 3:
                    termos.append(termo)
        
        return list(set(termos))[:3]  # Remove duplicatas
    except Exception:
        return []

# ===== FUNÇÕES DE ANÁLISE =====
def get_mes_atual():
    """Retorna o mês atual em formato MM"""
    return datetime.now().strftime("%m")

def get_dia_atual():
    """Retorna o dia atual em formato DD"""
    return datetime.now().strftime("%d")

def get_dados_historicos_mes(mes):
    """Retorna dados históricos para o mês especificado"""
    return DADOS_HISTORICOS.get(mes, DADOS_HISTORICOS["01"])

def verificar_data_comemorativa(mes, dia):
    """Verifica se hoje tem data comemorativa no banco histórico"""
    dados_mes = get_dados_historicos_mes(mes)
    data_atual = f"{mes}-{dia}"
    
    for evento in dados_mes.get("eventos", []):
        if evento.get("data") == data_atual:
            return evento
    return None

def buscar_tendencias_por_periodo(mes, limite=10):
    """Busca tendências históricas para um determinado mês"""
    dados_mes = get_dados_historicos_mes(mes)
    tendencias = dados_mes.get("tendencias", [])
    
    # Se não tiver dados, usa fallback
    if not tendencias:
        tendencias = [
            "smartwatch", "fone bluetooth", "caixa de som", "carregador portátil",
            "camisa", "vestido", "tênis", "bolsa", "mochila",
            "cadeira gamer", "luminária", "perfume", "brinquedo"
        ]
    
    return tendencias[:limite]

def analisar_produto_para_data(termo, data_tipo="historica"):
    """
    Analisa produto com base em dados históricos ou atuais
    """
    produtos_ml = buscar_produtos_mercadolivre(termo, 3)
    produtos_shopee = buscar_produtos_shopee(termo, 3)
    
    total_produtos = len(produtos_ml) + len(produtos_shopee)
    
    # Score baseado em disponibilidade
    score = 0
    if produtos_ml:
        score += 2
    if produtos_shopee:
        score += 2
    if total_produtos >= 4:
        score += 1
    
    if score >= 4:
        recomendacao = "🔥 OPORTUNIDADE EXCELENTE - Múltiplos fornecedores"
    elif score >= 2:
        recomendacao = "⭐ BOA OPORTUNIDADE - Disponível em alguma plataforma"
    else:
        recomendacao = "⚠️ OPORTUNIDADE BAIXA - Produto pode ser difícil de encontrar"
    
    return {
        "termo": termo,
        "total_produtos": total_produtos,
        "score": score,
        "recomendacao": recomendacao,
        "produtos_ml": produtos_ml,
        "produtos_shopee": produtos_shopee,
        "fonte": data_tipo
    }

def gerar_sugestoes_conteudo(evento, tendencias):
    """Gera sugestões de conteúdo com base no evento e tendências"""
    sugestoes = []
    
    # Sugestões baseadas no evento
    nome_evento = evento.get("nome", "")
    sugestao_base = evento.get("sugestao", "")
    
    if "Dia dos Namorados" in nome_evento:
        sugestoes = [
            "💝 Faça vídeo 'O que comprar para o Dia dos Namorados por R$100'",
            "🎁 Crie uma lista dos 10 melhores presentes românticos",
            "📦 Mostre unboxing de kits de presente",
            "👗 Dicas de look para um jantar romântico"
        ]
    elif "Dia das Mães" in nome_evento:
        sugestoes = [
            "👩 Faça um vídeo 'Presentes para mães que são úteis e baratos'",
            "🎯 Mostre sugestões por faixa de preço: R$50, R$100, R$200",
            "📦 Unboxing de kits de beleza e perfumes",
            "🏠 Ideias de presentes DIY (faça você mesmo)"
        ]
    elif "Dia dos Pais" in nome_evento:
        sugestoes = [
            "👨 'O que seu pai realmente quer ganhar' - sugestões práticas",
            "🔧 Mostre ferramentas e gadgets para homens",
            "⏰ Ideias de presentes diferentes para pais",
            "🎮 Sugestões de eletrônicos e acessórios"
        ]
    elif "Natal" in nome_evento:
        sugestoes = [
            "🎄 '10 brinquedos que vão esgotar no Natal'",
            "🛍️ Lista de presentes por categoria: infantil, adulto, casal",
            "💰 Dicas de como economizar nas compras de Natal",
            "📦 Unboxing dos brinquedos mais procurados"
        ]
    elif "Black Friday" in nome_evento:
        sugestoes = [
            "🛒 'Produtos que valem a pena na Black Friday'",
            "💰 Comparação de preços antes da BF",
            "📱 Sugestões de eletrônicos com melhor custo-benefício",
            "🎯 O que comprar na Black Friday para revender"
        ]
    elif "Carnaval" in nome_evento:
        sugestoes = [
            "🎭 'Fantasias mais procuradas no Carnaval 2026'",
            "📦 Itens essenciais para bloquinhos de rua",
            "💄 Dicas de maquiagem e acessórios para folia",
            "🎵 Caixas de som e acessórios para festas"
        ]
    else:
        # Sugestões genéricas
        sugestoes = [
            f"📸 Faça vídeo mostrando os produtos em tendência para {nome_evento}",
            f"📊 Crie conteúdo mostrando 'O que comprar' para {nome_evento}",
            f"💡 Dicas de presentes/presentes para {nome_evento}",
            f"🛍️ Lista de itens essenciais para {nome_evento}"
        ]
    
    # Adiciona sugestões baseadas nas tendências do mês
    if tendencias:
        if len(tendencias) >= 3:
            sugestoes.append(f"🎯 3 produtos que estão em alta neste mês: {', '.join(tendencias[:3])}")
    
    return sugestoes

def buscar_tendencias_atuais_ml():
    """Busca tendências atuais no Mercado Livre"""
    todos_termos = []
    
    for categoria, categoria_id in CATEGORIAS_ML.items():
        termos = buscar_produtos_em_alta_ml(categoria_id, 3)
        todos_termos.extend(termos)
        time.sleep(0.3)  # Delay para não sobrecarregar
    
    return list(set(todos_termos))[:10]  # Remove duplicatas e limita

# ===== INTERFACE =====
st.title("📅 Minerador Pro - Conteúdo Estratégico para Datas")

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

    # ===== ANÁLISE DO DIA ATUAL =====
    hoje = datetime.now()
    mes_atual = get_mes_atual()
    dia_atual = get_dia_atual()
    
    st.sidebar.markdown(f"**📅 Data atual:** {hoje.strftime('%d/%m/%Y')}")
    st.sidebar.markdown(f"**📊 Mês de referência:** {hoje.strftime('%B').capitalize()}")
    
    # Verifica se hoje tem data comemorativa
    evento_hoje = verificar_data_comemorativa(mes_atual, dia_atual)
    
    if evento_hoje:
        st.sidebar.success(f"🎉 {evento_hoje.get('nome')}!")
    else:
        st.sidebar.info("📌 Buscando tendências do mês passado")
    
    # ===== PAINEL PRINCIPAL =====
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if evento_hoje:
            st.markdown(f"""
            ### 🎉 {evento_hoje.get('nome')} - {hoje.strftime('%d/%m/%Y')}
            
            **Sugestão:** {evento_hoje.get('sugestao', '')}
            """)
        else:
            st.markdown(f"""
            ### 📊 Tendências para {hoje.strftime('%B').capitalize()}
            
            Com base no que as pessoas buscaram no mesmo mês do ano passado
            """)
    
    with col2:
        if st.button("🔄 Buscar Produtos Atuais", use_container_width=True):
            st.session_state.buscar_atuais = True
        st.caption("Busca em tempo real no Mercado Livre")
    
    st.markdown("---")
    
    # ===== BUSCA DE TENDÊNCIAS =====
    if st.session_state.get("buscar_atuais", False):
        with st.spinner("🔄 Buscando produtos em alta no Mercado Livre..."):
            tendencias_atuais = buscar_tendencias_atuais_ml()
            st.session_state.tendencias_atuais = tendencias_atuais
            st.session_state.buscar_atuais = False
    
    # Define tendências a usar
    if evento_hoje:
        # Se tem data comemorativa, usa as tendências do mês + evento
        tendencias_mes = buscar_tendencias_por_periodo(mes_atual, 10)
        
        # Adiciona termos específicos do evento
        termos_evento = []
        if "Dia dos Namorados" in evento_hoje.get("nome", ""):
            termos_evento = ["presente namorado", "kit romântico", "jantar especial"]
        elif "Dia das Mães" in evento_hoje.get("nome", ""):
            termos_evento = ["presente mãe", "flores", "perfume"]
        elif "Dia dos Pais" in evento_hoje.get("nome", ""):
            termos_evento = ["presente pai", "ferramentas", "relógio"]
        elif "Natal" in evento_hoje.get("nome", ""):
            termos_evento = ["presente natal", "árvore natal", "decoração"]
        
        tendencias = list(set(tendencias_mes + termos_evento))[:10]
        fonte_dados = f"Histórico para {evento_hoje.get('nome')}"
    else:
        # Se não tem data, usa tendências do mesmo mês do ano passado
        tendencias = buscar_tendencias_por_periodo(mes_atual, 10)
        fonte_dados = f"Tendências do mesmo período (ano passado)"
        
        # Adiciona tendências atuais do ML se disponíveis
        if hasattr(st.session_state, 'tendencias_atuais') and st.session_state.tendencias_atuais:
            for termo in st.session_state.tendencias_atuais[:3]:
                if termo not in tendencias:
                    tendencias.append(termo)
            fonte_dados += " + tendências atuais do ML"
    
    # ===== ANÁLISE DOS PRODUTOS =====
    if tendencias:
        st.markdown(f"### 📦 Analisando: {fonte_dados}")
        
        # Analisa cada termo
        resultados = []
        for termo in tendencias[:10]:
            analise = analisar_produto_para_data(termo, "histórico")
            resultados.append(analise)
            time.sleep(0.3)  # Delay para não sobrecarregar
        
        # Ordena por score
        resultados = sorted(resultados, key=lambda x: x["score"], reverse=True)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Produtos Analisados", len(resultados))
        with col2:
            excelentes = sum(1 for r in resultados if r["score"] >= 4)
            st.metric("🔥 Excelentes Oportunidades", excelentes)
        with col3:
            tem_produto = sum(1 for r in resultados if r["total_produtos"] > 0)
            st.metric("✅ Com Produtos Disponíveis", tem_produto)
        
        st.markdown("---")
        
        # Tabela de resultados
        st.markdown("### 📊 Produtos e Oportunidades")
        
        df_exibicao = pd.DataFrame([{
            "Produto": r["termo"],
            "Score": r["score"],
            "Disponibilidade": f"{r['total_produtos']} produtos",
            "Recomendação": r["recomendacao"],
            "Fonte": r["fonte"]
        } for r in resultados])
        
        st.dataframe(
            df_exibicao,
            column_config={
                "Produto": "Produto",
                "Score": st.column_config.NumberColumn("Score", format="%d"),
                "Disponibilidade": "Disponibilidade",
                "Recomendação": "Recomendação",
                "Fonte": "Fonte"
            },
            use_container_width=True
        )
        
        # Detalhamento por produto
        st.markdown("### 🛍️ Detalhamento dos Produtos")
        
        for r in resultados[:5]:
            with st.expander(f"📦 {r['termo']} - Score: {r['score']} - {r['recomendacao']}"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if r["produtos_ml"]:
                        st.markdown("**🔵 Mercado Livre:**")
                        for p in r["produtos_ml"][:2]:
                            st.markdown(f"- {p.get('nome', '')}")
                            st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                            if p.get('link'):
                                st.markdown(f"  [🔗 Ver produto]({p['link']})")
                            st.markdown("")
                
                with col_b:
                    if r["produtos_shopee"]:
                        st.markdown("**🟢 Shopee:**")
                        for p in r["produtos_shopee"][:2]:
                            st.markdown(f"- {p.get('nome', '')}")
                            st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                            if p.get('link'):
                                st.markdown(f"  [🔗 Ver produto]({p['link']})")
                            st.markdown("")
        
        # ===== SUGESTÕES DE CONTEÚDO =====
        st.markdown("---")
        st.markdown("### 💡 Sugestões de Conteúdo para Afiliados")
        
        if evento_hoje:
            sugestoes = gerar_sugestoes_conteudo(evento_hoje, tendencias)
            
            for i, sugestao in enumerate(sugestoes[:5], 1):
                st.info(f"{i}. {sugestao}")
        else:
            # Sugestões baseadas nas tendências do mês
            st.markdown(f"**📌 Baseado nas tendências de {hoje.strftime('%B').capitalize()}:**")
            
            sugestoes = [
                f"🎯 Crie vídeos mostrando os produtos em alta: {', '.join(tendencias[:3])}",
                "📊 Faça um 'Top 5' dos produtos mais procurados neste mês",
                "📦 Mostre unboxing dos produtos mais populares",
                "💰 Crie conteúdo sobre 'melhor custo-benefício' para cada categoria",
                "
