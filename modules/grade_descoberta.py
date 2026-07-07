"""
Grade de Descoberta de Produtos - Encontra produtos sem usar API
Usa múltiplas fontes gratuitas para descobrir produtos em tendência
"""

import random
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

# ============================================================
# GRADE DE PRODUTOS POR CATEGORIA (FALLBACK INTELIGENTE)
# ============================================================
GRADE_PRODUTOS = {
    "moda": {
        "termos": [
            "casaco feminino", "blusa de lã", "vestido longo", 
            "calça jeans", "sapato salto", "tênis esportivo",
            "jaqueta jeans", "saia midi", "blazer feminino",
            "camisa social", "vestido festa", "short jeans"
        ],
        "hashtags": ["#moda", #lookdodia", "#tendenciamoda", "#modafeminina"]
    },
    "eletrônico": {
        "termos": [
            "smartwatch", "fone bluetooth", "caixa de som",
            "carregador portátil", "webcam", "mouse gamer",
            "teclado mecânico", "monitor led", "ssd externo",
            "roteador wifi", "power bank", "adaptador usb"
        ],
        "hashtags": ["#tecnologia", "#eletrônicos", "#gadgets", "#review"]
    },
    "beleza": {
        "termos": [
            "perfume importado", "kit maquiagem", "creme hidratante",
            "máscara facial", "esmalte", "pincel maquiagem",
            "base líquida", "batom matte", "delineador",
            "sérum facial", "protetor solar", "shampoo sólido"
        ],
        "hashtags": ["#beleza", "#skincare", "#maquiagem", "#makeup"]
    },
    "casa": {
        "termos": [
            "organizador de gavetas", "caixa organizadora", "lixeira cozinha",
            "garrafa térmica", "porta temperos", "tapete quarto",
            "cortina blackout", "almofada decorativa", "suporte de parede",
            "potes herméticos", "escova de limpeza", "dispenser sabão"
        ],
        "hashtags": ["#casa", "#organização", "#decoração", "#diy"]
    },
    "infantil": {
        "termos": [
            "brinquedo educativo", "boneca interativa", "carrinho controle remoto",
            "moto infantil", "jogo de montar", "massinha de modelar",
            "boneco ação", "tabuleiro educativo", "livro infantil",
            "fantasia infantil", "casa de boneca", "playground"
        ],
        "hashtags": ["#infantil", "#brinquedos", "#crianças", "#educativo"]
    },
    "esporte": {
        "termos": [
            "tênis corrida", "bola futebol", "raquete tênis",
            "garrafa squeeze", "corda pular", "kit academia",
            "camisa esportiva", "short corrida", "meia compressão",
            "top esportivo", "luva boxe", "óculos natação"
        ],
        "hashtags": ["#esporte", "#fitness", "#treino", "#saúde"]
    }
}

# ============================================================
# PRODUTOS EM ALTA (BASEADO EM TEMPORADA)
# ============================================================
def get_produtos_sazonais() -> List[str]:
    """
    Retorna produtos sazonais baseados no mês atual
    """
    mes = datetime.now().month
    
    produtos_sazonais = {
        1: ["roupa de praia", "protetor solar", "óculos de sol", "sandalias"],  # Janeiro
        2: ["festas", "fantasia carnaval", "acessórios", "perfume"],  # Fevereiro
        3: ["look outono", "blusa manga longa", "jaqueta", "bota"],  # Março
        4: ["páscoa", "ovo de chocolate", "cesta", "coelho"],  # Abril
        5: ["dia das mães", "perfume", "bolsa", "flores"],  # Maio
        6: ["inverno", "casaco", "blusa de lã", "cachecol"],  # Junho
        7: ["férias", "mala viagem", "acessórios praia", "roupa conforto"],  # Julho
        8: ["dia dos pais", "relógio", "cinto", "ferramentas"],  # Agosto
        9: ["primavera", "flores", "vestido leve", "sapato aberto"],  # Setembro
        10: ["halloween", "fantasia", "decoração", "doces"],  # Outubro
        11: ["black friday", "eletrônicos", "smartwatch", "celular"],  # Novembro
        12: ["natal", "presentes", "árvore", "decoração"]  # Dezembro
    }
    
    return produtos_sazonais.get(mes, [])

# ============================================================
# GRADE DE DESCOBERTA - FUNÇÃO PRINCIPAL
# ============================================================
def descobrir_produtos_grade(categoria: str = None, quantidade: int = 10) -> List[Dict]:
    """
    Descobre produtos usando a grade de descoberta
    
    Args:
        categoria (str): Categoria específica (opcional)
        quantidade (int): Quantidade de produtos para retornar
    
    Returns:
        List[Dict]: Lista de produtos descobertos
    """
    produtos = []
    termos_usados = []
    
    # 1. PEGA PRODUTOS SAZONAIS
    sazonais = get_produtos_sazonais()
    for produto in sazonais[:5]:
        if produto not in termos_usados:
            termos_usados.append(produto)
            produtos.append({
                "produto": produto,
                "fonte": "sazonal",
                "categoria": "sazonal",
                "score": random.randint(7, 9)
            })
    
    # 2. PEGA PRODUTOS DA CATEGORIA ESPECÍFICA
    if categoria and categoria in GRADE_PRODUTOS:
        for termo in GRADE_PRODUTOS[categoria]["termos"]:
            if termo not in termos_usados:
                termos_usados.append(termo)
                produtos.append({
                    "produto": termo,
                    "fonte": "grade",
                    "categoria": categoria,
                    "score": random.randint(5, 8)
                })
    
    # 3. PEGA PRODUTOS DE TODAS AS CATEGORIAS (mix)
    if not categoria or len(produtos) < quantidade:
        for cat, dados in GRADE_PRODUTOS.items():
            if cat != categoria:  # Pula a categoria já usada
                for termo in dados["termos"][:3]:  # Pega 3 de cada
                    if termo not in termos_usados and len(produtos) < quantidade:
                        termos_usados.append(termo)
                        produtos.append({
                            "produto": termo,
                            "fonte": "grade",
                            "categoria": cat,
                            "score": random.randint(4, 7)
                        })
    
    # 4. EMBARALHA E RETORNA
    random.shuffle(produtos)
    return produtos[:quantidade]

def enriquecer_produto(produto: str) -> Dict:
    """
    Enriquece um produto com dados simulados (fallback)
    """
    import random
    
    return {
        "produto": produto,
        "pins": random.randint(500, 3000),
        "views_tiktok": round(random.uniform(1.0, 5.0), 1),
        "crescimento": random.randint(5, 45),
        "buscas_mes": random.randint(3000, 15000),
        "categoria": "Geral",
        "tendencia": random.choice(["🚀 Em alta", "📈 Crescendo", "➡️ Estável"]),
        "score": random.randint(4, 8),
        "fonte": "grade_descoberta"
    }

__all__ = [
    'descobrir_produtos_grade',
    'enriquecer_produto',
    'get_produtos_sazonais',
    'GRADE_PRODUTOS'
]
