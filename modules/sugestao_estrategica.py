"""
Sugestão Estratégica - Produtos com Alto Potencial no Próximo Mês
=================================================================
Cruza o calendário de datas comemorativas e eventos sazonais com
os dados reais de tendências para sugerir produtos com alto potencial
de vendas no próximo mês.

Autor: Sistema Minerador de Produtos
Versão: 1.0.0
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import List, Dict, Optional


# ============================================================
# CALENDÁRIO COMPLETO DE EVENTOS E DATAS COMEMORATIVAS (BR)
# ============================================================
CALENDARIO_EVENTOS = {
    1: [
        {
            "dia": 1,
            "nome": "Ano Novo / Réveillon",
            "emoji": "🥂",
            "tipo": "feriado",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "roupa branca", "categoria": "Moda", "score": 10, "motivo": "Tradição do Réveillon — buscas explodem na última semana de dezembro"},
                {"nome": "espumante", "categoria": "Bebidas", "score": 9, "motivo": "Bebida símbolo do Ano Novo — alta demanda em todo o Brasil"},
                {"nome": "decoração réveillon", "categoria": "Casa", "score": 8, "motivo": "Enfeites e itens de festa para a virada"},
                {"nome": "sandália feminina", "categoria": "Moda", "score": 8, "motivo": "Moda verão — looks de festa na praia e em casa"},
            ]
        },
        {
            "dia": 6,
            "nome": "Dia de Reis",
            "emoji": "👑",
            "tipo": "data_comemorativa",
            "urgencia": "media",
            "produtos": [
                {"nome": "brinquedo infantil", "categoria": "Brinquedos", "score": 8, "motivo": "Tradição de presentes para crianças no Dia de Reis"},
                {"nome": "kit de doces", "categoria": "Alimentos", "score": 7, "motivo": "Guloseimas e presentes simbólicos"},
            ]
        },
        {
            "dia": 25,
            "nome": "Verão / Alta Temporada de Praia",
            "emoji": "🏖️",
            "tipo": "sazonal",
            "urgencia": "alta",
            "produtos": [
                {"nome": "protetor solar", "categoria": "Beleza", "score": 10, "motivo": "Campeão de vendas no verão — buscas massivas em janeiro"},
                {"nome": "roupa de praia", "categoria": "Moda", "score": 9, "motivo": "Pico de vendas de biquíni e maiô em janeiro"},
                {"nome": "óculos de sol", "categoria": "Acessórios", "score": 9, "motivo": "Acessório de verão — tendência no Pinterest e TikTok"},
                {"nome": "chinelo havaianas", "categoria": "Calçados", "score": 8, "motivo": "Calçado de verão com alto giro na Shopee"},
                {"nome": "ventilador portátil", "categoria": "Eletrodomésticos", "score": 8, "motivo": "Calor intenso — alta demanda por ventilação"},
            ]
        },
    ],
    2: [
        {
            "dia": 1,
            "nome": "Carnaval",
            "emoji": "🎭",
            "tipo": "feriado",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "fantasia carnaval", "categoria": "Fantasias", "score": 10, "motivo": "Produto mais buscado em fevereiro — pico 3 semanas antes"},
                {"nome": "glitter corporal", "categoria": "Beleza", "score": 9, "motivo": "Maquiagem de carnaval viral no TikTok"},
                {"nome": "abadá", "categoria": "Moda", "score": 9, "motivo": "Roupa de bloco — alta demanda nas regiões nordeste e sudeste"},
                {"nome": "maquiagem colorida", "categoria": "Beleza", "score": 8, "motivo": "Looks de carnaval — tendência em tutoriais"},
                {"nome": "pochete", "categoria": "Acessórios", "score": 8, "motivo": "Acessório prático para foliões — viral no TikTok"},
            ]
        },
        {
            "dia": 14,
            "nome": "Dia dos Namorados (Valentine's Day)",
            "emoji": "💕",
            "tipo": "data_comemorativa",
            "urgencia": "alta",
            "produtos": [
                {"nome": "perfume feminino", "categoria": "Beleza", "score": 10, "motivo": "Presente mais buscado para namoradas em fevereiro"},
                {"nome": "kit presente casal", "categoria": "Presentes", "score": 9, "motivo": "Kits românticos — alta conversão em datas comemorativas"},
                {"nome": "colar feminino", "categoria": "Joias", "score": 8, "motivo": "Joias e acessórios — presentes para namoradas"},
            ]
        },
    ],
    3: [
        {
            "dia": 8,
            "nome": "Dia Internacional da Mulher",
            "emoji": "👩",
            "tipo": "data_comemorativa",
            "urgencia": "alta",
            "produtos": [
                {"nome": "perfume feminino", "categoria": "Beleza", "score": 10, "motivo": "Presente clássico para o Dia da Mulher — buscas intensas"},
                {"nome": "kit beleza feminino", "categoria": "Beleza", "score": 9, "motivo": "Kits de skincare e maquiagem — tendência crescente"},
                {"nome": "flores artificiais", "categoria": "Decoração", "score": 8, "motivo": "Arranjos decorativos — presente simbólico e durável"},
                {"nome": "bolsa feminina", "categoria": "Moda", "score": 9, "motivo": "Acessório de moda — presente de alto valor percebido"},
            ]
        },
        {
            "dia": 20,
            "nome": "Início do Outono / Transição de Estação",
            "emoji": "🍂",
            "tipo": "sazonal",
            "urgencia": "media",
            "produtos": [
                {"nome": "jaqueta feminina", "categoria": "Moda", "score": 9, "motivo": "Outono chegando — buscas por jaquetas explodem em março"},
                {"nome": "bota feminina", "categoria": "Calçados", "score": 8, "motivo": "Tendência outono no Pinterest — looks com botas"},
                {"nome": "cachecol", "categoria": "Acessórios", "score": 7, "motivo": "Acessório de frio — buscas crescentes"},
                {"nome": "blusa de moletom", "categoria": "Moda", "score": 8, "motivo": "Conforto e estilo para o outono — viral no TikTok"},
            ]
        },
    ],
    4: [
        {
            "dia": 1,
            "nome": "Páscoa",
            "emoji": "🐣",
            "tipo": "feriado",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "ovo de páscoa", "categoria": "Alimentos", "score": 10, "motivo": "Produto símbolo da Páscoa — pico de vendas 3 semanas antes"},
                {"nome": "cesta de páscoa", "categoria": "Presentes", "score": 9, "motivo": "Presente para crianças e adultos — alta conversão"},
                {"nome": "brinquedo infantil", "categoria": "Brinquedos", "score": 8, "motivo": "Presentes de Páscoa para crianças — tendência"},
                {"nome": "kit chocolate", "categoria": "Alimentos", "score": 9, "motivo": "Chocolates artesanais — tendência crescente na Páscoa"},
            ]
        },
        {
            "dia": 22,
            "nome": "Dia da Terra / Produtos Sustentáveis",
            "emoji": "🌍",
            "tipo": "data_comemorativa",
            "urgencia": "media",
            "produtos": [
                {"nome": "ecobag", "categoria": "Sustentabilidade", "score": 7, "motivo": "Dia da Terra — tendência de produtos eco-friendly"},
                {"nome": "garrafa reutilizável", "categoria": "Casa", "score": 8, "motivo": "Produto sustentável — alta demanda por consciência ambiental"},
            ]
        },
    ],
    5: [
        {
            "dia": 11,
            "nome": "Dia das Mães",
            "emoji": "💐",
            "tipo": "data_comemorativa",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "perfume feminino", "categoria": "Beleza", "score": 10, "motivo": "Presente mais vendido no Dia das Mães — pico 2 semanas antes"},
                {"nome": "bolsa feminina", "categoria": "Moda", "score": 10, "motivo": "Presente de alto valor — tendência no Google Shopping"},
                {"nome": "vestido feminino", "categoria": "Moda", "score": 9, "motivo": "Look para o almoço do Dia das Mães — buscas intensas"},
                {"nome": "kit skincare", "categoria": "Beleza", "score": 9, "motivo": "Cuidados com a pele — presente moderno e desejado"},
                {"nome": "flores artificiais", "categoria": "Decoração", "score": 8, "motivo": "Arranjos florais — presente simbólico e duradouro"},
                {"nome": "colar feminino", "categoria": "Joias", "score": 9, "motivo": "Joia como presente — alta conversão no Dia das Mães"},
            ]
        },
        {
            "dia": 1,
            "nome": "Dia do Trabalho / Promoções",
            "emoji": "👷",
            "tipo": "data_comemorativa",
            "urgencia": "media",
            "produtos": [
                {"nome": "tênis masculino", "categoria": "Calçados", "score": 8, "motivo": "Promoções de Dia do Trabalho — alta demanda por calçados"},
                {"nome": "ferramentas", "categoria": "Ferramentas", "score": 7, "motivo": "Presente simbólico para trabalhadores"},
            ]
        },
    ],
    6: [
        {
            "dia": 12,
            "nome": "Dia dos Namorados (Brasil)",
            "emoji": "❤️",
            "tipo": "data_comemorativa",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "perfume masculino", "categoria": "Beleza", "score": 10, "motivo": "Presente mais buscado para namorados — pico em junho"},
                {"nome": "perfume feminino", "categoria": "Beleza", "score": 10, "motivo": "Presente clássico para namoradas — buscas massivas"},
                {"nome": "kit casal", "categoria": "Presentes", "score": 9, "motivo": "Kits românticos — alta conversão em 12/06"},
                {"nome": "relógio masculino", "categoria": "Acessórios", "score": 9, "motivo": "Presente premium — tendência no Google Shopping"},
                {"nome": "colar feminino", "categoria": "Joias", "score": 8, "motivo": "Joia como presente — alta conversão"},
                {"nome": "vinho", "categoria": "Bebidas", "score": 8, "motivo": "Jantar romântico — buscas por vinhos especiais"},
            ]
        },
        {
            "dia": 21,
            "nome": "Início do Inverno",
            "emoji": "❄️",
            "tipo": "sazonal",
            "urgencia": "alta",
            "produtos": [
                {"nome": "casaco feminino", "categoria": "Moda", "score": 10, "motivo": "Inverno chegando — produto mais buscado em junho"},
                {"nome": "blusa de lã", "categoria": "Moda", "score": 9, "motivo": "Looks de inverno — tendência no TikTok e Pinterest"},
                {"nome": "bota feminina", "categoria": "Calçados", "score": 9, "motivo": "Moda inverno — buscas por botas explodem"},
                {"nome": "cobertor casal", "categoria": "Casa", "score": 8, "motivo": "Conforto no inverno — alta demanda"},
                {"nome": "meia térmica", "categoria": "Moda", "score": 7, "motivo": "Acessório de frio — produto de alto giro"},
            ]
        },
    ],
    7: [
        {
            "dia": 1,
            "nome": "Férias Escolares de Julho",
            "emoji": "🎒",
            "tipo": "sazonal",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "mala de viagem", "categoria": "Viagem", "score": 10, "motivo": "Férias de julho — pico de vendas de malas e bagagens"},
                {"nome": "casaco de frio", "categoria": "Moda", "score": 9, "motivo": "Inverno pleno — casacos em alta demanda"},
                {"nome": "kit viagem", "categoria": "Viagem", "score": 9, "motivo": "Acessórios de viagem — tendência nas férias"},
                {"nome": "almofada de pescoço", "categoria": "Viagem", "score": 8, "motivo": "Conforto em viagens — produto de alto giro em julho"},
                {"nome": "bota de frio", "categoria": "Calçados", "score": 8, "motivo": "Moda inverno — buscas intensas em julho"},
            ]
        },
        {
            "dia": 9,
            "nome": "Independência de São Paulo / Feriado Regional",
            "emoji": "📅",
            "tipo": "feriado",
            "urgencia": "baixa",
            "produtos": [
                {"nome": "apostila enem 2026", "categoria": "Educação", "score": 9, "motivo": "Sazonalidade ENEM — estudantes em preparação intensa nas férias"},
                {"nome": "livro didático", "categoria": "Educação", "score": 7, "motivo": "Período de estudos — alta demanda por materiais educativos"},
            ]
        },
    ],
    8: [
        {
            "dia": 10,
            "nome": "Dia dos Pais",
            "emoji": "👨",
            "tipo": "data_comemorativa",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "relógio masculino", "categoria": "Acessórios", "score": 10, "motivo": "Presente mais buscado para pais — pico 2 semanas antes"},
                {"nome": "perfume masculino", "categoria": "Beleza", "score": 10, "motivo": "Presente clássico para pais — buscas massivas em agosto"},
                {"nome": "kit ferramentas", "categoria": "Ferramentas", "score": 9, "motivo": "Presente prático para pais — tendência no Google Shopping"},
                {"nome": "cinto masculino", "categoria": "Moda", "score": 8, "motivo": "Acessório masculino — presente de alto giro"},
                {"nome": "tênis masculino", "categoria": "Calçados", "score": 9, "motivo": "Calçado masculino — presente de alto valor percebido"},
                {"nome": "carteira masculina", "categoria": "Acessórios", "score": 8, "motivo": "Acessório prático — presente popular para pais"},
            ]
        },
        {
            "dia": 21,
            "nome": "Início da Primavera (Hemisfério Sul)",
            "emoji": "🌸",
            "tipo": "sazonal",
            "urgencia": "media",
            "produtos": [
                {"nome": "vestido leve", "categoria": "Moda", "score": 8, "motivo": "Primavera chegando — looks florais em alta"},
                {"nome": "sapato aberto", "categoria": "Calçados", "score": 8, "motivo": "Moda primavera — sandálias e sapatos abertos em alta"},
                {"nome": "protetor solar", "categoria": "Beleza", "score": 9, "motivo": "Preparação para o verão — skincare em alta"},
            ]
        },
    ],
    9: [
        {
            "dia": 7,
            "nome": "Independência do Brasil",
            "emoji": "🇧🇷",
            "tipo": "feriado",
            "urgencia": "media",
            "produtos": [
                {"nome": "camiseta brasil", "categoria": "Moda", "score": 8, "motivo": "Feriado nacional — buscas por produtos patrióticos"},
                {"nome": "bandeira do brasil", "categoria": "Decoração", "score": 7, "motivo": "Decoração patriótica — tendência no 7 de setembro"},
            ]
        },
        {
            "dia": 22,
            "nome": "Início da Primavera",
            "emoji": "🌺",
            "tipo": "sazonal",
            "urgencia": "alta",
            "produtos": [
                {"nome": "vestido floral", "categoria": "Moda", "score": 9, "motivo": "Primavera — looks florais em alta no Pinterest e TikTok"},
                {"nome": "sandália feminina", "categoria": "Calçados", "score": 8, "motivo": "Moda primavera — calçados abertos em alta"},
                {"nome": "perfume floral", "categoria": "Beleza", "score": 8, "motivo": "Fragrâncias de primavera — tendência crescente"},
                {"nome": "protetor solar", "categoria": "Beleza", "score": 9, "motivo": "Pré-verão — cuidados com a pele em alta"},
            ]
        },
    ],
    10: [
        {
            "dia": 12,
            "nome": "Dia das Crianças",
            "emoji": "🧸",
            "tipo": "data_comemorativa",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "brinquedo infantil", "categoria": "Brinquedos", "score": 10, "motivo": "Dia das Crianças — maior pico de vendas de brinquedos no ano"},
                {"nome": "boneca", "categoria": "Brinquedos", "score": 10, "motivo": "Presente clássico para meninas — buscas massivas"},
                {"nome": "carrinho de controle remoto", "categoria": "Brinquedos", "score": 9, "motivo": "Presente para meninos — alta demanda"},
                {"nome": "kit escolar", "categoria": "Educação", "score": 8, "motivo": "Material escolar — presente educativo popular"},
                {"nome": "jogo de tabuleiro", "categoria": "Brinquedos", "score": 8, "motivo": "Entretenimento familiar — tendência crescente"},
                {"nome": "roupa infantil", "categoria": "Moda", "score": 8, "motivo": "Presente de moda para crianças — alta conversão"},
            ]
        },
        {
            "dia": 31,
            "nome": "Halloween",
            "emoji": "🎃",
            "tipo": "data_comemorativa",
            "urgencia": "alta",
            "produtos": [
                {"nome": "fantasia halloween", "categoria": "Fantasias", "score": 9, "motivo": "Halloween — buscas por fantasias explodem em outubro"},
                {"nome": "decoração halloween", "categoria": "Decoração", "score": 8, "motivo": "Decoração temática — tendência crescente no Brasil"},
                {"nome": "maquiagem artística", "categoria": "Beleza", "score": 8, "motivo": "Maquiagem de Halloween — viral no TikTok e YouTube"},
            ]
        },
    ],
    11: [
        {
            "dia": 28,
            "nome": "Black Friday",
            "emoji": "🛒",
            "tipo": "data_comemorativa",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "smartwatch", "categoria": "Eletrônicos", "score": 10, "motivo": "Black Friday — eletrônicos são os mais buscados do ano"},
                {"nome": "fone bluetooth", "categoria": "Eletrônicos", "score": 10, "motivo": "Produto de alto giro na Black Friday — pico de buscas"},
                {"nome": "celular", "categoria": "Eletrônicos", "score": 10, "motivo": "Smartphone — produto mais desejado na Black Friday"},
                {"nome": "notebook", "categoria": "Eletrônicos", "score": 9, "motivo": "Eletrônico de alto valor — alta demanda na Black Friday"},
                {"nome": "air fryer", "categoria": "Eletrodomésticos", "score": 9, "motivo": "Eletrodoméstico viral — Black Friday é o melhor momento"},
                {"nome": "tênis esportivo", "categoria": "Calçados", "score": 8, "motivo": "Moda esportiva — alta demanda em promoções"},
            ]
        },
        {
            "dia": 15,
            "nome": "Proclamação da República",
            "emoji": "🇧🇷",
            "tipo": "feriado",
            "urgencia": "baixa",
            "produtos": [
                {"nome": "eletrônicos", "categoria": "Eletrônicos", "score": 7, "motivo": "Feriado prolongado — boas oportunidades de vendas online"},
            ]
        },
    ],
    12: [
        {
            "dia": 25,
            "nome": "Natal",
            "emoji": "🎄",
            "tipo": "feriado",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "árvore de natal", "categoria": "Decoração", "score": 10, "motivo": "Natal — decoração é o produto mais buscado em dezembro"},
                {"nome": "kit presente natal", "categoria": "Presentes", "score": 10, "motivo": "Presentes de Natal — maior pico de vendas do ano"},
                {"nome": "perfume", "categoria": "Beleza", "score": 10, "motivo": "Presente clássico de Natal — buscas massivas"},
                {"nome": "brinquedo infantil", "categoria": "Brinquedos", "score": 9, "motivo": "Presente de Natal para crianças — alta demanda"},
                {"nome": "roupa de natal", "categoria": "Moda", "score": 8, "motivo": "Look natalino — tendência crescente"},
                {"nome": "ceia de natal", "categoria": "Alimentos", "score": 8, "motivo": "Itens para a ceia — alta demanda em dezembro"},
            ]
        },
        {
            "dia": 31,
            "nome": "Réveillon",
            "emoji": "🥂",
            "tipo": "feriado",
            "urgencia": "altissima",
            "produtos": [
                {"nome": "roupa branca", "categoria": "Moda", "score": 10, "motivo": "Tradição do Réveillon — roupa branca é obrigatória"},
                {"nome": "espumante", "categoria": "Bebidas", "score": 9, "motivo": "Bebida da virada — alta demanda em dezembro"},
                {"nome": "decoração réveillon", "categoria": "Casa", "score": 8, "motivo": "Festa de Ano Novo — decoração em alta"},
            ]
        },
    ],
}


# ============================================================
# CORES E ESTILOS POR TIPO DE URGÊNCIA
# ============================================================
ESTILOS_URGENCIA = {
    "altissima": {
        "cor": "#FF4444",
        "cor_fundo": "#FFF0F0",
        "badge": "🔴 URGENTE",
        "label": "Urgência Máxima",
        "emoji_barra": "🔥",
    },
    "alta": {
        "cor": "#FF8C00",
        "cor_fundo": "#FFF8F0",
        "badge": "🟠 ALTA",
        "label": "Alta Prioridade",
        "emoji_barra": "📈",
    },
    "media": {
        "cor": "#FFD700",
        "cor_fundo": "#FFFDF0",
        "badge": "🟡 MÉDIA",
        "label": "Prioridade Média",
        "emoji_barra": "📊",
    },
    "baixa": {
        "cor": "#4CAF50",
        "cor_fundo": "#F0FFF0",
        "badge": "🟢 BAIXA",
        "label": "Baixa Urgência",
        "emoji_barra": "📌",
    },
}

# Cores por tipo de evento
CORES_TIPO = {
    "feriado": "#667eea",
    "data_comemorativa": "#f093fb",
    "sazonal": "#4facfe",
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def _obter_proximo_mes() -> tuple:
    """Retorna (ano, mes) do próximo mês"""
    hoje = datetime.now()
    if hoje.month == 12:
        return hoje.year + 1, 1
    return hoje.year, hoje.month + 1


def _nome_mes(mes: int) -> str:
    """Retorna o nome do mês em português"""
    nomes = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    return nomes[mes]


def _dias_ate_evento(ano: int, mes: int, dia: int) -> int:
    """Calcula quantos dias faltam para um evento"""
    hoje = datetime.now().date()
    try:
        data_evento = datetime(ano, mes, dia).date()
        delta = (data_evento - hoje).days
        return max(0, delta)
    except ValueError:
        return 999


def _calcular_score_oportunidade(score_produto: int, dias_ate: int, urgencia: str) -> float:
    """
    Calcula o score de oportunidade combinando:
    - Score do produto (potencial de vendas)
    - Proximidade do evento (urgência temporal)
    - Tipo de urgência do evento
    """
    # Multiplicador de urgência
    mult_urgencia = {
        "altissima": 1.0,
        "alta": 0.85,
        "media": 0.70,
        "baixa": 0.55,
    }.get(urgencia, 0.70)

    # Multiplicador de proximidade (quanto mais próximo, maior a oportunidade)
    if dias_ate <= 7:
        mult_tempo = 1.0   # Semana crítica
    elif dias_ate <= 14:
        mult_tempo = 0.95  # Duas semanas
    elif dias_ate <= 21:
        mult_tempo = 0.90  # Três semanas
    elif dias_ate <= 30:
        mult_tempo = 0.85  # Um mês
    else:
        mult_tempo = 0.75  # Mais de um mês

    score_base = (score_produto / 10.0) * 10.0
    score_final = score_base * mult_urgencia * mult_tempo
    return round(min(10.0, score_final), 1)


def _enriquecer_com_dados_reais(produtos_evento: List[Dict]) -> List[Dict]:
    """
    Enriquece os produtos do evento com dados reais do marketplace quando disponíveis.
    """
    try:
        from modules.produtos_dinamicos import obter_produtos_marketplace_v49
        dados_reais = obter_produtos_marketplace_v49()
    except Exception:
        dados_reais = {}

    produtos_enriquecidos = []
    for produto in produtos_evento:
        nome = produto["nome"].lower()
        produto_enriquecido = produto.copy()

        # Tenta encontrar correspondência nos dados reais
        for termo_real, dados in dados_reais.items():
            if any(palavra in termo_real.lower() for palavra in nome.split()):
                produto_enriquecido["score"] = max(
                    produto["score"],
                    int(dados.get("score", produto["score"]))
                )
                produto_enriquecido["fonte_real"] = dados.get("fonte", "Marketplace")
                produto_enriquecido["crescimento_real"] = dados.get("crescimento", 0)
                produto_enriquecido["confirmado_dados_reais"] = True
                break
        else:
            produto_enriquecido["fonte_real"] = "Calendário Estratégico"
            produto_enriquecido["crescimento_real"] = 0
            produto_enriquecido["confirmado_dados_reais"] = False

        produtos_enriquecidos.append(produto_enriquecido)

    return produtos_enriquecidos


# ============================================================
# FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO
# ============================================================
def render_sugestao_estrategica():
    """
    Renderiza a aba de Sugestão Estratégica com produtos de alto potencial
    alinhados ao calendário do próximo mês.
    """
    ano_prox, mes_prox = _obter_proximo_mes()
    nome_mes_prox = _nome_mes(mes_prox)
    mes_atual = datetime.now().month
    nome_mes_atual = _nome_mes(mes_atual)

    # ============================================================
    # CABEÇALHO
    # ============================================================
    st.markdown("### 📌 Sugestões Estratégicas de Produtos")
    st.caption(
        f"Produtos com **alto potencial de vendas** alinhados ao calendário de "
        f"**{nome_mes_prox}/{ano_prox}** — Prepare-se com antecedência!"
    )

    # Banner informativo
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    ">
        <div style="font-size: 20px; font-weight: bold; margin-bottom: 6px;">
            📅 Próximo Mês: {nome_mes_prox} {ano_prox}
        </div>
        <div style="font-size: 14px; opacity: 0.9;">
            Antecipe suas vendas! Os produtos abaixo foram selecionados com base nos eventos
            e datas comemorativas de {nome_mes_prox}. Comece a criar conteúdo <strong>agora</strong>
            para maximizar suas conversões.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # SELETOR DE MÊS (permite ver outros meses também)
    # ============================================================
    col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
    with col_sel1:
        meses_opcoes = [
            f"{_nome_mes(m)} {ano_prox if m >= mes_prox else datetime.now().year}"
            for m in range(1, 13)
        ]
        idx_default = mes_prox - 1
        mes_escolhido_str = st.selectbox(
            "📅 Visualizar mês:",
            meses_opcoes,
            index=idx_default,
            key="sugestao_mes_selecionado",
            label_visibility="collapsed",
        )
        mes_visualizado = meses_opcoes.index(mes_escolhido_str) + 1

    with col_sel2:
        mostrar_todos = st.toggle(
            "Mostrar todos os eventos",
            value=False,
            key="sugestao_toggle_todos",
        )

    with col_sel3:
        apenas_alta_urgencia = st.toggle(
            "Só alta urgência",
            value=False,
            key="sugestao_toggle_urgencia",
        )

    ano_visualizado = ano_prox if mes_visualizado >= mes_prox else datetime.now().year

    # ============================================================
    # BUSCA EVENTOS DO MÊS SELECIONADO
    # ============================================================
    eventos_mes = CALENDARIO_EVENTOS.get(mes_visualizado, [])

    if apenas_alta_urgencia:
        eventos_mes = [e for e in eventos_mes if e["urgencia"] in ("altissima", "alta")]

    if not eventos_mes:
        st.info(f"📭 Nenhum evento estratégico mapeado para {_nome_mes(mes_visualizado)}.")
        return

    # ============================================================
    # MÉTRICAS DE RESUMO DO MÊS
    # ============================================================
    total_eventos = len(eventos_mes)
    total_produtos = sum(len(e["produtos"]) for e in eventos_mes)
    eventos_urgentes = sum(1 for e in eventos_mes if e["urgencia"] in ("altissima", "alta"))
    dias_ate_primeiro = _dias_ate_evento(ano_visualizado, mes_visualizado, eventos_mes[0]["dia"])

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("📅 Eventos no Mês", total_eventos, delta=f"{eventos_urgentes} urgentes")
    with col_m2:
        st.metric("📦 Produtos Sugeridos", total_produtos, delta="Alto potencial")
    with col_m3:
        st.metric("⏰ Dias até o 1º Evento", dias_ate_primeiro, delta="Prepare-se!")
    with col_m4:
        st.metric("📈 Mês Analisado", f"{_nome_mes(mes_visualizado)[:3]}/{ano_visualizado}")

    st.markdown("---")

    # ============================================================
    # RENDERIZA CADA EVENTO COM SEUS PRODUTOS
    # ============================================================
    for evento in eventos_mes:
        dias_ate = _dias_ate_evento(ano_visualizado, mes_visualizado, evento["dia"])
        estilo = ESTILOS_URGENCIA.get(evento["urgencia"], ESTILOS_URGENCIA["media"])
        cor_tipo = CORES_TIPO.get(evento["tipo"], "#667eea")

        # Enriquece produtos com dados reais
        produtos_enriquecidos = _enriquecer_com_dados_reais(evento["produtos"])

        # Ordena por score de oportunidade
        produtos_ordenados = sorted(
            produtos_enriquecidos,
            key=lambda p: _calcular_score_oportunidade(p["score"], dias_ate, evento["urgencia"]),
            reverse=True
        )

        # Limita a quantidade se não for "mostrar todos"
        if not mostrar_todos:
            produtos_ordenados = produtos_ordenados[:4]

        # ---- CABEÇALHO DO EVENTO ----
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {cor_tipo}22 0%, {cor_tipo}11 100%);
            border-left: 4px solid {cor_tipo};
            border-radius: 8px;
            padding: 12px 16px;
            margin: 12px 0 8px 0;
        ">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <span style="font-size: 28px;">{evento['emoji']}</span>
                <div>
                    <div style="font-size: 18px; font-weight: bold; color: #1a1a2e;">
                        {evento['nome']}
                    </div>
                    <div style="font-size: 13px; color: #555; margin-top: 2px;">
                        📅 Dia {evento['dia']:02d} de {_nome_mes(mes_visualizado)} &nbsp;|&nbsp;
                        ⏰ <strong>{dias_ate} dias</strong> restantes &nbsp;|&nbsp;
                        <span style="
                            background: {estilo['cor']};
                            color: white;
                            padding: 2px 8px;
                            border-radius: 12px;
                            font-size: 11px;
                            font-weight: bold;
                        ">{estilo['badge']}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- PRODUTOS DO EVENTO EM COLUNAS ----
        n_cols = min(len(produtos_ordenados), 4)
        if n_cols == 0:
            continue

        cols = st.columns(n_cols)
        for i, produto in enumerate(produtos_ordenados):
            score_oport = _calcular_score_oportunidade(
                produto["score"], dias_ate, evento["urgencia"]
            )
            confirmado = produto.get("confirmado_dados_reais", False)
            link_shopee = f"https://shopee.com.br/search?keyword={quote(produto['nome'])}"

            with cols[i]:
                with st.container(border=True):
                    # Badge de confirmação por dados reais
                    badge_real = "✅ Dados Reais" if confirmado else "📅 Calendário"
                    cor_badge = "#4CAF50" if confirmado else "#2196F3"

                    st.markdown(f"""
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        margin-bottom: 6px;
                    ">
                        <span style="font-weight: bold; font-size: 14px; color: #1a1a2e;">
                            {produto['nome'].title()}
                        </span>
                        <span style="
                            background: {cor_badge};
                            color: white;
                            font-size: 9px;
                            padding: 2px 6px;
                            border-radius: 8px;
                            white-space: nowrap;
                            margin-left: 4px;
                        ">{badge_real}</span>
                    </div>
                    <div style="font-size: 11px; color: #888; margin-bottom: 6px;">
                        🏷️ {produto['categoria']}
                    </div>
                    """, unsafe_allow_html=True)

                    # Barra de score de oportunidade
                    st.progress(
                        score_oport / 10.0,
                        text=f"{estilo['emoji_barra']} Oportunidade: {score_oport}/10",
                    )

                    # Motivo estratégico
                    st.caption(produto["motivo"])

                    # Crescimento real (se disponível)
                    cresc = produto.get("crescimento_real", 0)
                    if cresc and cresc > 0:
                        st.metric(
                            "Crescimento Real",
                            f"+{cresc}%",
                            delta=f"Fonte: {produto.get('fonte_real', 'Marketplace')}",
                            delta_color="normal",
                        )

                    # Link Shopee
                    st.markdown(
                        f'<a href="{link_shopee}" target="_blank" style="'
                        f'display: block; text-align: center; background: #EE4D2D; '
                        f'color: white; padding: 6px 10px; border-radius: 6px; '
                        f'font-size: 12px; font-weight: bold; text-decoration: none; '
                        f'margin-top: 6px;">🛒 Buscar na Shopee</a>',
                        unsafe_allow_html=True,
                    )

        st.markdown("")  # Espaçamento entre eventos

    # ============================================================
    # TABELA CONSOLIDADA DE TODOS OS PRODUTOS
    # ============================================================
    st.markdown("---")
    with st.expander("📊 Ver Tabela Consolidada de Todos os Produtos do Mês", expanded=False):
        todos_produtos = []
        for evento in eventos_mes:
            dias_ate = _dias_ate_evento(ano_visualizado, mes_visualizado, evento["dia"])
            produtos_enriquecidos = _enriquecer_com_dados_reais(evento["produtos"])
            for produto in produtos_enriquecidos:
                score_oport = _calcular_score_oportunidade(
                    produto["score"], dias_ate, evento["urgencia"]
                )
                link_shopee = f"https://shopee.com.br/search?keyword={quote(produto['nome'])}"
                todos_produtos.append({
                    "Produto": produto["nome"].title(),
                    "Evento": f"{evento['emoji']} {evento['nome']}",
                    "Dia do Evento": f"{evento['dia']:02d}/{mes_visualizado:02d}",
                    "Dias Restantes": dias_ate,
                    "Categoria": produto["categoria"],
                    "Score Oportunidade": score_oport,
                    "Urgência": ESTILOS_URGENCIA[evento["urgencia"]]["badge"],
                    "Dados Reais": "✅" if produto.get("confirmado_dados_reais") else "📅",
                    "Link Shopee": link_shopee,
                    "Motivo": produto["motivo"][:60] + "...",
                })

        if todos_produtos:
            df_todos = pd.DataFrame(todos_produtos)
            df_todos = df_todos.sort_values("Score Oportunidade", ascending=False)

            st.dataframe(
                df_todos,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Produto": st.column_config.TextColumn("Produto", width="medium"),
                    "Evento": st.column_config.TextColumn("Evento", width="large"),
                    "Dia do Evento": st.column_config.TextColumn("Data", width="small"),
                    "Dias Restantes": st.column_config.NumberColumn(
                        "⏰ Dias",
                        width="small",
                        format="%d dias",
                    ),
                    "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                    "Score Oportunidade": st.column_config.ProgressColumn(
                        "🎯 Score",
                        min_value=0,
                        max_value=10,
                        format="%.1f/10",
                        width="small",
                    ),
                    "Urgência": st.column_config.TextColumn("Urgência", width="small"),
                    "Dados Reais": st.column_config.TextColumn("Fonte", width="small"),
                    "Link Shopee": st.column_config.LinkColumn(
                        "🛒 Shopee",
                        help="Buscar produto na Shopee",
                        validate="^https://shopee\\.com\\.br/.*",
                        display_text="Buscar",
                        width="small",
                    ),
                    "Motivo": st.column_config.TextColumn("Motivo Estratégico", width="large"),
                },
            )
            st.caption(f"📊 {len(todos_produtos)} produtos estratégicos para {_nome_mes(mes_visualizado)}/{ano_visualizado}")

    # ============================================================
    # DICA ESTRATÉGICA FINAL
    # ============================================================
    st.markdown("---")
    st.info(
        f"💡 **Dica Estratégica:** Para maximizar vendas em **{_nome_mes(mes_visualizado)}**, "
        f"comece a criar conteúdo sobre esses produtos **agora**. "
        f"O algoritmo do TikTok e Reels leva de 7 a 14 dias para distribuir o conteúdo em escala. "
        f"Produtos com **🔴 Urgência Máxima** devem ser priorizados imediatamente!"
    )
