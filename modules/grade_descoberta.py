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
            "camisa social", "vestido festa", "short jeans",
            "cropped", "body feminino", "macacão"
        ],
        "hashtags": ["#moda", "#lookdodia", "#tendenciamoda", "#modafeminina"]
    },
    "eletrônico": {
        "termos": [
            "smartwatch", "fone bluetooth", "caixa de som",
            "carregador portátil", "webcam", "mouse gamer",
            "teclado mecânico", "monitor led", "ssd externo",
            "roteador wifi", "power bank", "adaptador usb",
            "hd externo", "pen drive", "microfone"
        ],
        "hashtags": ["#tecnologia", "#eletrônicos", "#gadgets", "#review"]
    },
    "beleza": {
        "termos": [
            "perfume importado", "kit maquiagem", "creme hidratante",
            "máscara facial", "esmalte", "pincel maquiagem",
            "base líquida", "batom matte", "delineador",
            "sérum facial", "protetor solar", "shampoo sólido",
            "condicionador", "máscara capilar", "óleo corporal"
        ],
        "hashtags": ["#beleza", "#skincare", "#maquiagem", "#makeup"]
    },
    "casa": {
        "termos": [
            "organizador de gavetas", "caixa organizadora", "lixeira cozinha",
            "garrafa térmica", "porta temperos", "tapete quarto",
            "cortina blackout", "almofada decorativa", "suporte de parede",
            "potes herméticos", "escova de limpeza", "dispenser sabão",
            "porta escovas", "organizador de talheres", "suporte de panela"
        ],
        "hashtags": ["#casa", "#organização", "#decoração", "#diy"]
    },
    "infantil": {
        "termos": [
            "brinquedo educativo", "boneca interativa", "carrinho controle remoto",
            "moto infantil", "jogo de montar", "massinha de modelar",
            "boneco ação", "tabuleiro educativo", "livro infantil",
            "fantasia infantil", "casa de boneca", "playground",
            "blocos de montar", "quebra-cabeça", "jogo da memória"
        ],
        "hashtags": ["#infantil", "#brinquedos", "#crianças", "#educativo"]
    },
    "esporte": {
        "termos": [
            "tênis corrida", "bola futebol", "raquete tênis",
            "garrafa squeeze", "corda pular", "kit academia",
            "camisa esportiva", "short corrida", "meia compressão",
            "top esportivo", "luva boxe", "óculos natação",
            "caneleira", "munhequeira", "faixa de suor"
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
        1: ["roupa de praia", "protetor solar", "óculos de sol", "sandalias", "chapéu"],  # Janeiro
        2: ["fantasia carnaval", "acessórios", "perfume", "glitter", "maquiagem"],  # Fevereiro
        3: ["look outono", "blusa manga longa", "jaqueta", "bota", "cachecol"],  # Março
        4: ["ovo de chocolate", "cesta", "coelho", "brinquedo", "presentes"],  # Abril
        5: ["perfume", "bolsa", "flores", "vestido", "jantar"],  # Maio - Dia das Mães
        6: ["casaco", "blusa de lã", "cachecol", "luva", "bota"],  # Junho - Inverno
        7: ["mala viagem", "acessórios praia", "roupa conforto", "protetor solar", "chapéu"],  # Julho - Férias
        8: ["relógio", "cinto", "ferramentas", "camisa", "perfume"],  # Agosto - Dia dos Pais
        9: ["flores", "vestido leve", "sapato aberto", "blusa", "acessórios"],  # Setembro - Primavera
        10: ["fantasia", "decoração", "doces", "maquiagem", "acessórios"],  # Outubro - Halloween
        11: ["eletrônicos", "smartwatch", "celular", "fone", "tv"],  # Novembro - Black Friday
        12: ["presentes", "árvore", "decoração", "espumante", "roupa branca"]  # Dezembro - Natal
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
    
    # Gera dados realistas baseados no nome do produto
    nome_lower = produto.lower()
    
    # Define categoria baseada no nome
    categoria = "Geral"
    categorias_map = {
        "casaco": "Moda", "blusa": "Moda", "vestido": "Moda", "calça": "Moda",
        "sapato": "Moda", "tênis": "Moda", "jaqueta": "Moda", "saia": "Moda",
        "smartwatch": "Eletrônicos", "fone": "Eletrônicos", "celular": "Eletrônicos",
        "tablet": "Eletrônicos", "mouse": "Eletrônicos", "teclado": "Eletrônicos",
        "perfume": "Beleza", "maquiagem": "Beleza", "creme": "Beleza", "batom": "Beleza",
        "brinquedo": "Infantil", "boneca": "Infantil", "carrinho": "Infantil",
        "organizador": "Casa", "caixa": "Casa", "lixeira": "Casa", "garrafa": "Casa"
    }
    
    for palavra, cat in categorias_map.items():
        if palavra in nome_lower:
            categoria = cat
            break
    
    return {
        "produto": produto,
        "pins": random.randint(500, 3500),
        "views_tiktok": round(random.uniform(1.0, 6.0), 1),
        "crescimento": random.randint(5, 50),
        "buscas_mes": random.randint(3000, 20000),
        "categoria": categoria,
        "tendencia": random.choice(["🚀 Em alta", "📈 Crescendo", "➡️ Estável"]),
        "score": random.randint(4, 9),
        "fonte": "grade_descoberta"
    }

def obter_produtos_por_categoria(categoria: str) -> List[str]:
    """
    Retorna produtos de uma categoria específica
    """
    if categoria in GRADE_PRODUTOS:
        return GRADE_PRODUTOS[categoria]["termos"]
    return []

def obter_hashtags_categoria(categoria: str) -> List[str]:
    """
    Retorna hashtags de uma categoria específica
    """
    if categoria in GRADE_PRODUTOS:
        return GRADE_PRODUTOS[categoria]["hashtags"]
    return ["#tendência", "#2026", "#produto"]

def mesclar_produtos(produtos_existentes: List[str], quantidade: int = 5) -> List[str]:
    """
    Mescla produtos existentes com novos da grade
    """
    todos_produtos = []
    
    # Adiciona produtos de todas as categorias
    for categoria, dados in GRADE_PRODUTOS.items():
        for termo in dados["termos"]:
            if termo not in produtos_existentes and termo not in todos_produtos:
                todos_produtos.append(termo)
    
    # Adiciona sazonais
    for produto in get_produtos_sazonais():
        if produto not in produtos_existentes and produto not in todos_produtos:
            todos_produtos.append(produto)
    
    # Embaralha e retorna
    random.shuffle(todos_produtos)
    return todos_produtos[:quantidade]

__all__ = [
    'descobrir_produtos_grade',
    'enriquecer_produto',
    'get_produtos_sazonais',
    'GRADE_PRODUTOS',
    'obter_produtos_por_categoria',
    'obter_hashtags_categoria',
    'mesclar_produtos'
]
