import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import requests
import random
import json
import re
from collections import Counter

# Configuração da página
st.set_page_config(page_title="Minerador Pro - Produtos em Alta", page_icon="📊", layout="wide")

# ===== CONFIGURAÇÕES =====
CATEGORIAS_ML = {
    "Eletrônicos": "MLB1000",
    "Moda": "MLB1430", 
    "Casa e Decoração": "MLB1574",
    "Beleza": "MLB1246",
    "Esportes": "MLB1384",
    "Brinquedos": "MLB1384",
    "Automotivo": "MLB1743",
    "Ferramentas": "MLB1648",
    "Livros": "MLB3025",
    "Saúde": "MLB1246"
}

# ===== BANCO DE DADOS HISTÓRICO =====
DADOS_HISTORICOS = {
    "01": {
        "tendencias": [
            "material escolar", "mochila", "estojo", "caderno", "caneta",
            "tênis", "tênis casual", "calça jeans", "roupa de academia",
            "smartwatch", "fone bluetooth", "carregador portátil"
        ],
        "eventos": [
            {"data": "01-01", "nome": "Ano Novo", "sugestao": "Decoração para festa, roupas para virada"},
            {"data": "01-06", "nome": "Dia de Reis", "sugestao": "Presentes religiosos, artigos de decoração"},
            {"data": "01-20", "nome": "Dia de São Sebastião", "sugestao": "Itens religiosos, artigos para festas"}
        ]
    },
    "02": {
        "tendencias": [
            "fantasia carnaval", "acessórios carnaval", "máscara", "glitter",
            "maiô", "biquíni", "sungas", "chinelo", "protetor solar",
            "fone bluetooth", "caixa de som portátil", "power bank"
        ],
        "eventos": [
            {"data": "02-02", "nome": "Dia de Iemanjá", "sugestao": "Artigos religiosos, decoração, flores"},
            {"data": "02-14", "nome": "Dia dos Namorados (EUA)", "sugestao": "Presentes românticos, kits de jantar"},
            {"data": "02-28", "nome": "Carnaval", "sugestao": "Fantasias, acessórios, bebidas, decoração"}
        ]
    },
    "03": {
        "tendencias": [
            "kit praia", "bolsa praia", "toalha", "canga", "chapéu",
            "smartwatch", "fone bluetooth", "caixa de som portátil",
            "vestido", "sandália", "chinelo", "óculos de sol"
        ],
        "eventos": [
            {"data": "03-08", "nome": "Dia Internacional da Mulher", "sugestao": "Presentes femininos, flores, perfumes"},
            {"data": "03-15", "nome": "Dia do Consumidor", "sugestao": "Eletrônicos, celulares, produtos com desconto"},
            {"data": "03-20", "nome": "Outono", "sugestao": "Roupas de meia estação, cobertores"}
        ]
    },
    "04": {
        "tendencias": [
            "ovo de páscoa", "chocolate", "presente páscoa", "cestinha",
            "tênis", "calça jeans", "blusa", "casaco leve",
            "smartwatch", "fone bluetooth", "fone sem fio"
        ],
        "eventos": [
            {"data": "04-07", "nome": "Dia do Jornalista", "sugestao": "Presentes para profissionais"},
            {"data": "04-21", "nome": "Tiradentes", "sugestao": "Feriado - viagens, artigos de viagem"},
            {"data": "04-28", "nome": "Páscoa", "sugestao": "Ovos de chocolate, cestas, presentes"}
        ]
    },
    "05": {
        "tendencias": [
            "presente dia das mães", "flores", "perfume", "bolsa", "vestido",
            "smartwatch", "fone bluetooth", "caixa de som",
            "tênis", "calça jeans", "blusa feminina", "lenço"
        ],
        "eventos": [
            {"data": "05-01", "nome": "Dia do Trabalhador", "sugestao": "Feriado - churrasco, artigos de viagem"},
            {"data": "05-13", "nome": "Dia das Mães", "sugestao": "Presentes para mães: perfumes, bolsas, vestidos"},
            {"data": "05-25", "nome": "Dia do Orgulho LGBTQ+", "sugestao": "Acessórios coloridos, bandeiras"}
        ]
    },
    "06": {
        "tendencias": [
            "presente dia dos namorados", "kit jantar", "vinho", "chocolate", "perfume",
            "camisa", "calça", "vestido", "blusa", "sandália",
            "fone bluetooth", "smartwatch", "fone sem fio"
        ],
        "eventos": [
            {"data": "06-01", "nome": "Dia das Crianças (em alguns países)", "sugestao": "Brinquedos, jogos educativos"},
            {"data": "06-12", "nome": "Dia dos Namorados (BR)", "sugestao": "Presentes românticos: perfumes, roupas, jantares"},
            {"data": "06-24", "nome": "São João", "sugestao": "Decoração junina, roupas xadrez, comidas típicas"}
        ]
    },
    "07": {
        "tendencias": [
            "roupa de frio", "casaco", "jaqueta", "blusa de lã", "cachecol",
            "tênis", "tênis casual", "coturno", "bota",
            "fone bluetooth", "fone sem fio", "carregador portátil"
        ],
        "eventos": [
            {"data": "07-09", "nome": "Revolução Constitucionalista", "sugestao": "Feriado - filmes, streaming, roupas de frio"},
            {"data": "07-20", "nome": "Dia do Amigo", "sugestao": "Presentes para amigos, kits de cerveja"}
        ]
    },
    "08": {
        "tendencias": [
            "presente dia dos pais", "relógio", "cinto", "camisa", "calça social",
            "ferramenta", "furadeira", "parafusadeira", "kit ferramentas",
            "smartwatch", "fone bluetooth", "caixa de som"
        ],
        "eventos": [
            {"data": "08-11", "nome": "Dia do Estudante", "sugestao": "Material escolar, mochilas, estojos"},
            {"data": "08-14", "nome": "Dia dos Pais", "sugestao": "Presentes para pais: ferramentas, relógios, eletrônicos"},
            {"data": "08-22", "nome": "Dia do Folclore", "sugestao": "Decoração temática, brinquedos tradicionais"}
        ]
    },
    "09": {
        "tendencias": [
            "camisa", "calça", "vestido", "blusa", "jaqueta jeans",
            "tênis", "tênis casual", "sapato social", "sandália",
            "smartwatch", "fone bluetooth", "carregador portátil"
        ],
        "eventos": [
            {"data": "09-07", "nome": "Independência do Brasil", "sugestao": "Decoração verde-amarela, roupas patrióticas"},
            {"data": "09-21", "nome": "Dia da Árvore", "sugestao": "Decoração com plantas, vasos, jardinagem"},
            {"data": "09-22", "nome": "Primavera", "sugestao": "Roupas leves, decoração floral, vasos de plantas"}
        ]
    },
    "10": {
        "tendencias": [
            "fantasia halloween", "decoração halloween", "abóbora", "máscara",
            "brinquedo", "boneca", "carrinho", "jogo", "pelúcia",
            "smartwatch", "fone bluetooth", "carregador portátil"
        ],
        "eventos": [
            {"data": "10-12", "nome": "Dia das Crianças", "sugestao": "Brinquedos, jogos educativos, livros, roupas infantis"},
            {"data": "10-15", "nome": "Dia do Professor", "sugestao": "Presentes para professores, canecas, livros"},
            {"data": "10-31", "nome": "Halloween", "sugestao": "Fantasias, decoração, doces, maquiagem"}
        ]
    },
    "11": {
        "tendencias": [
            "black friday", "promoção", "eletrônico", "celular", "tv", "smartwatch",
            "presente natal", "brinquedo", "boneca", "carrinho",
            "camisa", "calça", "vestido", "blusa", "casaco"
        ],
        "eventos": [
            {"data": "11-02", "nome": "Finados", "sugestao": "Flores, velas, artigos religiosos"},
            {"data": "11-15", "nome": "Proclamação da República", "sugestao": "Feriado - viagens, artigos de viagem"},
            {"data": "11-25", "nome": "Black Friday", "sugestao": "Eletrônicos, celulares, roupas, eletrodomésticos"}
        ]
    },
    "12": {
        "tendencias": [
            "presente natal", "árvore natal", "decoração natalina", "luzes", "enfeite",
            "brinquedo", "boneca", "carrinho", "pelúcia", "jogo",
            "camisa", "vestido", "blusa", "casaco", "jaqueta",
            "perfume", "kit beleza", "maquiagem", "vinho", "espumante"
        ],
        "eventos": [
            {"data": "12-25", "nome": "Natal", "sugestao": "Presentes: brinquedos, eletrônicos, roupas, perfumes"},
            {"data": "12-31", "nome": "Réveillon", "sugestao": "Roupas brancas, brindes, decoração, fogos"}
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
                "vendas": item.get("sold_quantity", 0),
                "condicao": item.get("condition", "new")
            })
        
        return produtos
    except Exception as e:
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
        preco = f"R$ {preco_centavos / 100000:.2f}" if preco_centavos else "-"
        link = f"https://shopee.com.br/product/{shopid}/{itemid}"
        produtos.append({
            "nome": nome[:60],
            "preco": preco,
            "link": link,
            "loja": "Shopee",
            "vendas": info.get("sold", 0)
        })

    return produtos

def buscar_total_resultados_ml(termo):
    """Busca o total de resultados para um termo no Mercado Livre"""
    url = f"https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "q": termo,
        "limit": 1,
        "condition": "new"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return 0
            
        data = response.json()
        return data.get("paging", {}).get("total", 0)
    except Exception:
        return 0

def buscar_total_resultados_shopee(termo):
    """Busca o total de resultados para um termo na Shopee"""
    url = "https://shopee.com.br/api/v4/search/search_items"
    params = {
        "keyword": termo,
        "limit": 1,
        "newest": 0,
        "order": "desc",
        "by": "sales",
        "page_type": "search",
        "scenario": "PAGE_OTHERS",
        "version": 2,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://shopee.com.br/search?keyword={quote(termo)}",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code != 200:
            return 0
        data = resp.json()
        return data.get("total_count", 0)
    except Exception:
        return 0

def buscar_produtos_em_alta_ml(categoria_id=None, limite=10):
    """Busca produtos em alta por categoria no Mercado Livre"""
    url = f"https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "limit": limite,
        "sort": "relevance",
        "condition": "new"
    }
    
    if categoria_id:
        params["category"] = categoria_id
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
            
        data = response.json()
        produtos = []
        
        for item in data.get("results", [])[:limite]:
            nome = item.get("title", "")
            preco = item.get("price", 0)
            
            # Extrai palavras-chave do título
            palavras = re.findall(r'\w+', nome.lower())
            palavras = [p for p in palavras if len(p) > 3]
            
            produtos.append({
                "nome": nome[:80],
                "preco": f"R$ {preco:.2f}",
                "link": item.get("permalink", ""),
                "vendas": item.get("sold_quantity", 0),
                "palavras_chave": palavras[:5]
            })
        
        return produtos
    except Exception as e:
        return []

def analisar_saturacao(total_resultados):
    """
    Analisa a saturação baseada no número de resultados
    Retorna: nível de saturação, cor, recomendação
    """
    if total_resultados == 0:
        return {
            "nivel": "Sem dados",
            "cor": "gray",
            "recomendacao": "Produto não encontrado no mercado"
        }
    elif total_resultados < 50:
        return {
            "nivel": "🟢 Baixa saturação",
            "cor": "green",
            "recomendacao": "✅ Ótimo! Pouca concorrência. Aproveite!"
        }
    elif total_resultados < 200:
        return {
            "nivel": "🟡 Média saturação",
            "cor": "yellow",
            "recomendacao": "📊 Concorrência moderada. Diferencie seu conteúdo."
        }
    elif total_resultados < 500:
        return {
            "nivel": "🟠 Alta saturação",
            "cor": "orange",
            "recomendacao": "⚠️ Muita concorrência. Foque em nichos específicos."
        }
    else:
        return {
            "nivel": "🔴 Saturação extrema",
            "cor": "red",
            "recomendacao": "🚨 Mercado saturado! Busque variações menos competitivas."
        }

# ===== FUNÇÕES DE ANÁLISE =====
def get_mes_atual():
    return datetime.now().strftime("%m")

def get_dia_atual():
    return datetime.now().strftime("%d")

def get_dados_historicos_mes(mes):
    return DADOS_HISTORICOS.get(mes, DADOS_HISTORICOS["01"])

def verificar_data_comemorativa(mes, dia):
    dados_mes = get_dados_historicos_mes(mes)
    data_atual = f"{mes}-{dia}"
    
    for evento in dados_mes.get("eventos", []):
        if evento.get("data") == data_atual:
            return evento
    return None

def buscar_tendencias_por_periodo(mes, limite=10):
    dados_mes = get_dados_historicos_mes(mes)
    tendencias = dados_mes.get("tendencias", [])
    
    if not tendencias:
        tendencias = [
            "smartwatch", "fone bluetooth", "caixa de som", "carregador portátil",
            "camisa", "vestido", "tênis", "bolsa", "mochila",
            "cadeira gamer", "luminária", "perfume", "brinquedo"
        ]
    
    return tendencias[:limite]

def analisar_produto_completo(termo):
    """Análise completa: produtos + saturação"""
    produtos_ml = buscar_produtos_mercadolivre(termo, 3)
    produtos_shopee = buscar_produtos_shopee(termo, 3)
    
    total_ml = buscar_total_resultados_ml(termo)
    total_shopee = buscar_total_resultados_shopee(termo)
    total_resultados = total_ml + total_shopee
    
    saturacao = analisar_saturacao(total_resultados)
    
    score = 0
    if produtos_ml:
        score += 2
    if produtos_shopee:
        score += 2
    if len(produtos_ml) + len(produtos_shopee) >= 4:
        score += 1
    
    # Ajusta score baseado na saturação
    if total_resultados < 50:
        score += 2  # Bônus por baixa concorrência
    elif total_resultados > 500:
        score -= 1  # Penalidade por saturação
    
    # Gera recomendação final
    if score >= 6:
        recomendacao = "🔥 OPORTUNIDADE EXCELENTE - Alta demanda, baixa concorrência!"
    elif score >= 4:
        recomendacao = "⭐ BOA OPORTUNIDADE - Demanda moderada, concorrência média"
    elif score >= 2:
        recomendacao = "📊 OPORTUNIDADE MÉDIA - Avaliar se vale a pena"
    else:
        recomendacao = "⚠️ OPORTUNIDADE BAIXA - Mercado pode estar saturado"
    
    return {
        "termo": termo,
        "produtos_ml": produtos_ml,
        "produtos_shopee": produtos_shopee,
        "total_ml": total_ml,
        "total_shopee": total_shopee,
        "total_resultados": total_resultados,
        "saturacao": saturacao,
        "score": score,
        "recomendacao": recomendacao
    }

def minerar_produtos_em_alta():
    """Minera produtos em alta no Mercado Livre"""
    resultados = []
    
    # Busca produtos em alta por categoria
    for categoria, categoria_id in CATEGORIAS_ML.items():
        produtos = buscar_produtos_em_alta_ml(categoria_id, 3)
        
        for p in produtos:
            # Extrai termo principal do título
            palavras = p.get("palavras_chave", [])
            if palavras:
                termo = " ".join(palavras[:3])
                if len(termo) > 3:
                    analise = analisar_produto_completo(termo)
                    analise["categoria"] = categoria
                    analise["fonte"] = f"Mercado Livre - {categoria}"
                    resultados.append(analise)
        
        time.sleep(0.5)  # Delay para não sobrecarregar
    
    # Remove duplicatas
    resultados_unicos = {}
    for r in resultados:
        if r["termo"] not in resultados_unicos:
            resultados_unicos[r["termo"]] = r
    
    # Ordena por score
    resultados_finais = sorted(resultados_unicos.values(), key=lambda x: x["score"], reverse=True)
    
    return resultados_finais[:15]

# ===== INTERFACE =====
st.title("📊 Minerador Pro - Produtos em Alta")

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
    st.sidebar.info(f"📅 Licença expira: {st.session_state.data_expira}")
    if st.sidebar.button("Sair / Desconectar"):
        st.session_state.autenticado = False
        st.rerun()

    hoje = datetime.now()
    mes_atual = get_mes_atual()
    dia_atual = get_dia_atual()
    
    st.sidebar.markdown(f"**📅 Data:** {hoje.strftime('%d/%m/%Y')}")
    st.sidebar.markdown(f"**📊 Mês:** {hoje.strftime('%B').capitalize()}")
    
    evento_hoje = verificar_data_comemorativa(mes_atual, dia_atual)
    if evento_hoje:
        st.sidebar.success(f"🎉 {evento_hoje.get('nome')} hoje!")

    # ===== TABS =====
    tab1, tab2, tab3 = st.tabs(["📊 Em Alta Agora", "📅 Sugestões por Data", "🎯 Análise de Saturação"])

    # ===== TAB 1: EM ALTA AGORA =====
    with tab1:
        st.markdown("### 🚀 Produtos em Alta no Mercado Livre")
        st.caption("Baseado em busca de produtos novos com relevância")
        
        if st.button("🔄 Buscar Produtos em Alta", use_container_width=True):
            with st.spinner("Analisando produtos em alta no Mercado Livre..."):
                produtos_em_alta = minerar_produtos_em_alta()
                st.session_state.produtos_em_alta = produtos_em_alta
        
        if hasattr(st.session_state, 'produtos_em_alta') and st.session_state.produtos_em_alta:
            df_alta = pd.DataFrame([{
                "Produto": p["termo"],
                "Categoria": p.get("categoria", "Geral"),
                "Score": p["score"],
                "Resultados": p["total_resultados"],
                "Saturação": p["saturacao"]["nivel"],
                "Recomendação": p["recomendacao"]
            } for p in st.session_state.produtos_em_alta])
            
            st.dataframe(
                df_alta,
                column_config={
                    "Produto": "Produto",
                    "Categoria": "Categoria",
                    "Score": st.column_config.NumberColumn("Score", format="%d"),
                    "Resultados": "Total de Resultados",
                    "Saturação": "Nível de Saturação",
                    "Recomendação": "Recomendação"
                },
                use_container_width=True
            )
            
            # Detalhes dos produtos
            st.markdown("---")
            st.markdown("### 📦 Detalhamento dos Produtos em Alta")
            
            for p in st.session_state.produtos_em_alta[:5]:
                with st.expander(f"📦 {p['termo']} - Score: {p['score']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Resultados ML", p["total_ml"])
                        st.metric("Resultados Shopee", p["total_shopee"])
                    
                    with col2:
                        st.metric("Total Resultados", p["total_resultados"])
                        st.markdown(f"**Saturação:** {p['saturacao']['nivel']}")
                    
                    with col3:
                        st.metric("Score Oportunidade", f"{p['score']}/8")
                        st.info(p["recomendacao"])
                    
                    st.markdown("**🟢 Mercado Livre:**")
                    for prod in p["produtos_ml"][:2]:
                        st.markdown(f"- {prod.get('nome', '')}")
                        st.markdown(f"  💰 {prod.get('preco', '')} | 📦 {prod.get('vendas', 0)} vendidos")
                        if prod.get('link'):
                            st.markdown(f"  [🔗 Ver produto]({prod['link']})")
                        st.markdown("")
                    
                    st.markdown("**🟠 Shopee:**")
                    for prod in p["produtos_shopee"][:2]:
                        st.markdown(f"- {prod.get('nome', '')}")
                        st.markdown(f"  💰 {prod.get('preco', '')} | 📦 {prod.get('vendas', 0)} vendidos")
                        if prod.get('link'):
                            st.markdown(f"  [🔗 Ver produto]({prod['link']})")
                        st.markdown("")
                    
                    # Análise de saturação
                    st.markdown("---")
                    st.markdown("### 📊 Análise de Saturação")
                    
                    sat = p['saturacao']
                    if p['total_resultados'] < 50:
                        st.success(f"✅ **{sat['nivel']}** - {sat['recomendacao']}")
                    elif p['total_resultados'] < 200:
                        st.info(f"📊 **{sat['nivel']}** - {sat['recomendacao']}")
                    elif p['total_resultados'] < 500:
                        st.warning(f"⚠️ **{sat['nivel']}** - {sat['recomendacao']}")
                    else:
                        st.error(f"🚨 **{sat['nivel']}** - {sat['recomendacao']}")

    # ===== TAB 2: SUGESTÕES POR DATA =====
    with tab2:
        st.markdown("### 📅 Sugestões de Conteúdo por Data")
        
        # Busca tendências do mês atual
        tendencias_mes = buscar_tendencias_por_periodo(mes_atual, 10)
        
        if evento_hoje:
            st.info(f"🎉 **Hoje é {evento_hoje.get('nome')}!**")
            st.markdown(f"**Sugestão:** {evento_hoje.get('sugestao', '')}")
            
            # Sugestões específicas para o evento
            st.markdown("---")
            st.markdown("### 💡 Ideias de Conteúdo")
            
            if "Dia dos Namorados" in evento_hoje.get("nome", ""):
                sugestoes = [
                    "💝 Faça vídeo 'O que comprar para o Dia dos Namorados por R$100'",
                    "🎁 Crie uma lista dos 10 melhores presentes românticos",
                    "📦 Mostre unboxing de kits de presente",
                    "👗 Dicas de look para um jantar romântico"
                ]
            elif "Dia das Mães" in evento_hoje.get("nome", ""):
                sugestoes = [
                    "👩 'Presentes para mães que são úteis e baratos'",
                    "🎯 Sugestões por faixa de preço: R$50, R$100, R$200",
                    "📦 Unboxing de kits de beleza e perfumes"
                ]
            elif "Dia dos Pais" in evento_hoje.get("nome", ""):
                sugestoes = [
                    "👨 'O que seu pai realmente quer ganhar'",
                    "🔧 Mostre ferramentas e gadgets para homens",
                    "⏰ Ideias de presentes diferentes para pais"
                ]
            elif "Natal" in evento_hoje.get("nome", ""):
                sugestoes = [
                    "🎄 '10 brinquedos que vão esgotar no Natal'",
                    "🛍️ Lista de presentes por categoria",
                    "💰 Dicas de como economizar nas compras de Natal"
                ]
            else:
                sugestoes = [
                    f"📸 Faça vídeo sobre produtos para {evento_hoje.get('nome')}",
                    f"📊 Crie conteúdo 'O que comprar' para {evento_hoje.get('nome')}",
                    f"💡 Dicas de presentes para {evento_hoje.get('nome')}"
                ]
            
            for i, sug in enumerate(sugestoes[:5], 1):
                st.info(f"{i}. {sug}")
        
        else:
            st.markdown(f"### 📊 Tendências para {hoje.strftime('%B').capitalize()}")
            st.markdown("Com base no que as pessoas buscaram no mesmo mês do ano passado")
            
            # Produtos sugeridos para o mês
            st.markdown("---")
            st.markdown("### 🎯 Produtos em Tendência para este Mês")
            
            resultados_mes = []
            for termo in tendencias_mes[:8]:
                analise = analisar_produto_completo(termo)
                resultados_mes.append(analise)
                time.sleep(0.3)
            
            df_mes = pd.DataFrame([{
                "Produto": r["termo"],
                "Score": r["score"],
                "Resultados": r["total_resultados"],
                "Saturação": r["saturacao"]["nivel"],
                "Recomendação": r["recomendacao"]
            } for r in resultados_mes])
            
            st.dataframe(df_mes, use_container_width=True)
            
            # Sugestões de conteúdo para o mês
            st.markdown("---")
            st.markdown("### 💡 Sugestões de Conteúdo para o Mês")
            
            sugestoes_mes = [
                f"🎯 Crie vídeos mostrando: {', '.join(tendencias_mes[:3])}",
                "📊 Faça um 'Top 5' dos produtos mais procurados deste mês",
                "📦 Mostre unboxing dos produtos mais populares",
                "💰 Crie conteúdo sobre 'melhor custo-benefício' para cada categoria",
                "📱 Adapte o conteúdo para TikTok/Reels mostrando os produtos em uso"
            ]
            
            for i, sug in enumerate(sugestoes_mes[:5], 1):
                st.info(f"{i}. {sug}")

    # ===== TAB 3: ANÁLISE DE SATURAÇÃO =====
    with
