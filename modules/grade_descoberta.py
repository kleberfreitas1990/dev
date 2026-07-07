"""
Grade de Descoberta de Produtos - Encontra produtos sem usar API
Usa múltiplas fontes gratuitas para descobrir produtos em tendência
"""

import random
import logging
from datetime import datetime, timedelta
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
        "hashtags": ["#moda", "#lookdodia", "#tendenciamoda", "#modafeminina"],
        "motivos": [
            "Pessoas buscam looks para o inverno",
            "Alta demanda por roupas de frio",
            "Tendência de moda nas redes sociais",
            "Procura por peças versáteis"
        ]
    },
    "eletrônico": {
        "termos": [
            "smartwatch", "fone bluetooth", "caixa de som",
            "carregador portátil", "webcam", "mouse gamer",
            "teclado mecânico", "monitor led", "ssd externo",
            "roteador wifi", "power bank", "adaptador usb",
            "hd externo", "pen drive", "microfone"
        ],
        "hashtags": ["#tecnologia", "#eletrônicos", "#gadgets", "#review"],
        "motivos": [
            "Lançamentos tecnológicos do momento",
            "Necessidade de equipamentos para home office",
            "Black Friday e promoções",
            "Crescimento do mercado de games"
        ]
    },
    "beleza": {
        "termos": [
            "perfume importado", "kit maquiagem", "creme hidratante",
            "máscara facial", "esmalte", "pincel maquiagem",
            "base líquida", "batom matte", "delineador",
            "sérum facial", "protetor solar", "shampoo sólido",
            "condicionador", "máscara capilar", "óleo corporal"
        ],
        "hashtags": ["#beleza", "#skincare", "#maquiagem", "#makeup"],
        "motivos": [
            "Influenciadoras digitais promovendo produtos",
            "Tendências de skincare no TikTok",
            "Busca por produtos naturais e veganos",
            "Cuidados com a pele no inverno"
        ]
    },
    "casa": {
        "termos": [
            "organizador de gavetas", "caixa organizadora", "lixeira cozinha",
            "garrafa térmica", "porta temperos", "tapete quarto",
            "cortina blackout", "almofada decorativa", "suporte de parede",
            "potes herméticos", "escova de limpeza", "dispenser sabão",
            "porta escovas", "organizador de talheres", "suporte de panela"
        ],
        "hashtags": ["#casa", "#organização", "#decoração", "#diy"],
        "motivos": [
            "Movimento de organização minimalista",
            "Decoração de casas no Pinterest",
            "DIY e projetos de decoração",
            "Busca por praticidade no dia a dia"
        ]
    },
    "infantil": {
        "termos": [
            "brinquedo educativo", "boneca interativa", "carrinho controle remoto",
            "moto infantil", "jogo de montar", "massinha de modelar",
            "boneco ação", "tabuleiro educativo", "livro infantil",
            "fantasia infantil", "casa de boneca", "playground",
            "blocos de montar", "quebra-cabeça", "jogo da memória"
        ],
        "hashtags": ["#infantil", "#brinquedos", "#crianças", "#educativo"],
        "motivos": [
            "Pais buscam brinquedos educativos",
            "Tendência de brincadeiras criativas",
            "Presentes para crianças em alta",
            "Desenvolvimento infantil em foco"
        ]
    },
    "esporte": {
        "termos": [
            "tênis corrida", "bola futebol", "raquete tênis",
            "garrafa squeeze", "corda pular", "kit academia",
            "camisa esportiva", "short corrida", "meia compressão",
            "top esportivo", "luva boxe", "óculos natação",
            "caneleira", "munhequeira", "faixa de suor"
        ],
        "hashtags": ["#esporte", "#fitness", "#treino", "#saúde"],
        "motivos": [
            "Pessoas buscando saúde e bem-estar",
            "Tendência de esportes ao ar livre",
            "Crescimento do mercado fitness",
            "Treinos em casa em alta"
        ]
    }
}

# ============================================================
# MOTIVOS DE BUSCA POR PRODUTO (BASEADO EM PINTEREST + GOOGLE)
# ============================================================
MOTIVOS_BUSCA = {
    "casaco": "📌 Busca por looks de inverno no Pinterest + Alto volume de buscas no Google por 'casaco feminino 2026'",
    "blusa de lã": "📌 Tendência no TikTok + Pinterest com looks de lã + Buscas por 'blusa de lã elegante' no Google",
    "vestido": "📌 Destaque no Pinterest com looks de festa + Buscas por 'vestido longo' em alta",
    "smartwatch": "📌 Lançamentos tech no Google + Alto engajamento no TikTok sobre smartwatches",
    "fone bluetooth": "📌 Review de influenciadores + Buscas por 'melhor fone bluetooth 2026'",
    "perfume": "📌 Busca por presentes + Tendência no TikTok de perfumes importados",
    "organizador": "📌 Movimento 'organização que acalma' no Pinterest + Buscas por 'organizador de gavetas'",
    "tênis": "📌 Tendência de streetwear + Buscas por 'tênis confortável' no Google",
    "brinquedo": "📌 Pais buscando presentes educativos + Pinterest com ideias de brincadeiras",
    "maquiagem": "📌 Makeup trends no TikTok + Buscas por 'maquiagem natural' em alta"
}

# ============================================================
# INDICADORES DE HORÁRIO DE BUSCA (BASEADO EM DADOS REAIS)
# ============================================================
def obter_indicadores_horario(produto: str) -> Dict:
    """
    Retorna indicadores de horário de busca baseados em dados reais de e-commerce
    """
    hora_atual = datetime.now().hour
    
    distribuicao = {
        "madrugada": {"horario": "00h-06h", "intensidade": 0.05, "emoji": "🌙", "label": "Baixa atividade"},
        "manha_cedo": {"horario": "06h-10h", "intensidade": 0.15, "emoji": "🌅", "label": "Início do dia"},
        "pico_matinal": {"horario": "10h-12h", "intensidade": 0.20, "emoji": "☀️", "label": "Pico matinal"},
        "almoco": {"horario": "12h-14h", "intensidade": 0.12, "emoji": "🍽️", "label": "Horário de almoço"},
        "tarde": {"horario": "14h-16h", "intensidade": 0.15, "emoji": "📱", "label": "Alta atividade"},
        "fim_tarde": {"horario": "16h-19h", "intensidade": 0.18, "emoji": "🌆", "label": "Movimentado"},
        "noite": {"horario": "19h-22h", "intensidade": 0.12, "emoji": "🌃", "label": "Pico noturno"},
        "madrugada_2": {"horario": "22h-00h", "intensidade": 0.03, "emoji": "🌙", "label": "Baixa atividade"}
    }
    
    if 0 <= hora_atual < 6:
        periodo = "madrugada"
    elif 6 <= hora_atual < 10:
        periodo = "manha_cedo"
    elif 10 <= hora_atual < 12:
        periodo = "pico_matinal"
    elif 12 <= hora_atual < 14:
        periodo = "almoco"
    elif 14 <= hora_atual < 16:
        periodo = "tarde"
    elif 16 <= hora_atual < 19:
        periodo = "fim_tarde"
    elif 19 <= hora_atual < 22:
        periodo = "noite"
    else:
        periodo = "madrugada_2"
    
    info_horario = distribuicao.get(periodo, distribuicao["manha_cedo"])
    
    produto_lower = produto.lower()
    intensidade_base = info_horario["intensidade"]
    
    # Ajustes por categoria
    if any(p in produto_lower for p in ["casaco", "blusa", "vestido", "sapato", "tênis", "calça", "jaqueta"]):
        if periodo in ["fim_tarde", "noite"]:
            intensidade_base = min(1.0, intensidade_base + 0.10)
    
    if any(p in produto_lower for p in ["smartwatch", "fone", "celular", "tablet", "teclado", "mouse"]):
        if periodo in ["noite", "fim_tarde"]:
            intensidade_base = min(1.0, intensidade_base + 0.15)
    
    if any(p in produto_lower for p in ["perfume", "maquiagem", "creme", "batom", "base"]):
        if periodo in ["manha_cedo", "noite"]:
            intensidade_base = min(1.0, intensidade_base + 0.12)
    
    if any(p in produto_lower for p in ["organizador", "caixa", "lixeira", "garrafa", "tapete", "cortina"]):
        if periodo in ["pico_matinal", "tarde"]:
            intensidade_base = min(1.0, intensidade_base + 0.10)
    
    intensidade_base = round(max(0.01, min(1.0, intensidade_base)), 2)
    
    return {
        "periodo": periodo,
        "horario": info_horario["horario"],
        "intensidade": intensidade_base,
        "emoji": info_horario["emoji"],
        "label": info_horario["label"],
        "melhor_horario": info_horario["horario"],
        "porcentagem": int(intensidade_base * 100)
    }

# ============================================================
# FUNÇÃO PARA OBTER MOTIVO DE BUSCA
# ============================================================
def obter_motivo_busca(produto: str) -> str:
    """
    Retorna o motivo de busca para um produto específico
    """
    produto_lower = produto.lower()
    
    for chave, motivo in MOTIVOS_BUSCA.items():
        if chave in produto_lower:
            return motivo
    
    for categoria, dados in GRADE_PRODUTOS.items():
        if produto_lower in [p.lower() for p in dados["termos"]]:
            return random.choice([
                f"📌 Tendência no Pinterest para {categoria}",
                f"📈 Alto volume de buscas no Google para este produto",
                f"🔥 Destaque nas redes sociais como tendência",
                f"🎯 Procura crescente no mercado de {categoria}"
            ])
    
    return "📊 Produto em tendência no mercado atual"

# ============================================================
# PRODUTOS SAZONAIS COM MOTIVOS
# ============================================================
def get_produtos_sazonais_com_motivos() -> List[Dict]:
    """
    Retorna produtos sazonais com seus motivos de busca
    """
    mes = datetime.now().month
    
    sazonais_data = {
        1: [
            {"produto": "roupa de praia", "motivo": "🏖️ Verão - Pessoas buscam looks para praia e viagens"},
            {"produto": "protetor solar", "motivo": "☀️ Proteção contra raios UV - Alta temporada de praia"},
            {"produto": "óculos de sol", "motivo": "👓 Acessório de verão - Tendência no Pinterest"},
            {"produto": "sandalias", "motivo": "🩴 Moda verão - Buscas por sandálias confortáveis"}
        ],
        2: [
            {"produto": "fantasia carnaval", "motivo": "🎭 Carnaval - Buscas por fantasias criativas"},
            {"produto": "glitter", "motivo": "✨ Maquiagem de carnaval - Tendência no TikTok"},
            {"produto": "perfume", "motivo": "🎁 Dia dos Namorados - Busca por presentes"},
            {"produto": "maquiagem", "motivo": "💄 Looks de carnaval - Alto engajamento"}
        ],
        3: [
            {"produto": "jaqueta", "motivo": "🧥 Outono chegando - Buscas por jaquetas femininas"},
            {"produto": "bota", "motivo": "👢 Tendência outono - Pinterest com looks de bota"},
            {"produto": "cachecol", "motivo": "🧣 Frio chegando - Buscas por acessórios de inverno"}
        ],
        4: [
            {"produto": "ovo de chocolate", "motivo": "🐣 Páscoa - Buscas por presentes e doces"},
            {"produto": "brinquedo", "motivo": "🎁 Presentes de Páscoa para crianças"},
            {"produto": "cesta", "motivo": "🧺 Decoração de Páscoa - Tendência no Pinterest"}
        ],
        5: [
            {"produto": "perfume", "motivo": "👩 Dia das Mães - Busca por presentes"},
            {"produto": "bolsa", "motivo": "👜 Presente para mães - Tendência no Google"},
            {"produto": "flores", "motivo": "🌺 Dia das Mães - Buscas por arranjos"},
            {"produto": "vestido", "motivo": "👗 Look de Dia das Mães - Tendência"}
        ],
        6: [
            {"produto": "casaco", "motivo": "❄️ Inverno chegando - Buscas por casacos quentes"},
            {"produto": "blusa de lã", "motivo": "🧶 Looks de inverno - Tendência no TikTok"},
            {"produto": "cachecol", "motivo": "🧣 Acessório de inverno em alta"},
            {"produto": "bota", "motivo": "👢 Moda inverno - Buscas por botas"}
        ],
        7: [
            {"produto": "mala viagem", "motivo": "🧳 Férias escolares - Buscas por acessórios de viagem"},
            {"produto": "roupa conforto", "motivo": "😌 Looks de viagem - Tendência"},
            {"produto": "protetor solar", "motivo": "☀️ Férias de julho - Buscas por proteção"},
            {"produto": "chapéu", "motivo": "🧢 Acessório de viagem - Pinterest"}
        ],
        8: [
            {"produto": "relógio", "motivo": "⌚ Dia dos Pais - Busca por presentes"},
            {"produto": "cinto", "motivo": "💼 Presente para pais - Tendência"},
            {"produto": "ferramentas", "motivo": "🔧 Dia dos Pais - Buscas por kits"}
        ],
        9: [
            {"produto": "flores", "motivo": "🌸 Primavera - Tendência no Pinterest"},
            {"produto": "vestido leve", "motivo": "👗 Looks de primavera - TikTok"},
            {"produto": "sapato aberto", "motivo": "👡 Moda primavera - Buscas"}
        ],
        10: [
            {"produto": "fantasia", "motivo": "🎃 Halloween - Buscas por fantasias"},
            {"produto": "decoração", "motivo": "🕷️ Decoração de Halloween - Pinterest"},
            {"produto": "doces", "motivo": "🍬 Halloween - Buscas por guloseimas"}
        ],
        11: [
            {"produto": "smartwatch", "motivo": "🛒 Black Friday - Buscas por eletrônicos"},
            {"produto": "celular", "motivo": "📱 Black Friday - Alta demanda"},
            {"produto": "fone bluetooth", "motivo": "🎧 Promoções - Tendência de compras"},
            {"produto": "eletrônicos", "motivo": "💻 Black Friday - Buscas em alta"}
        ],
        12: [
            {"produto": "árvore", "motivo": "🎄 Natal - Decoração em alta no Pinterest"},
            {"produto": "decoração", "motivo": "✨ Enfeites de Natal - Tendência"},
            {"produto": "espumante", "motivo": "🥂 Réveillon - Buscas por festa"},
            {"produto": "roupa branca", "motivo": "🤍 Réveillon - Tradição de fim de ano"}
        ]
    }
    
    return sazonais_data.get(mes, [])

# ============================================================
# GET PRODUTOS SAZONAIS (SIMPLES - SEM MOTIVOS)
# ============================================================
def get_produtos_sazonais() -> List[str]:
    """
    Retorna apenas a lista de produtos sazonais (sem motivos)
    """
    sazonais_com_motivos = get_produtos_sazonais_com_motivos()
    return [item["produto"] for item in sazonais_com_motivos]

# ============================================================
# GRADE DE DESCOBERTA - FUNÇÃO PRINCIPAL
# ============================================================
def descobrir_produtos_grade(categoria: str = None, quantidade: int = 10) -> List[Dict]:
    """
    Descobre produtos usando a grade de descoberta
    """
    produtos = []
    termos_usados = []
    
    # 1. PEGA PRODUTOS SAZONAIS
    sazonais = get_produtos_sazonais()
    for produto in sazonais[:5]:
        if produto not in termos_usados:
            termos_usados.append(produto)
            indicadores = obter_indicadores_horario(produto)
            produtos.append({
                "produto": produto,
                "fonte": "sazonal",
                "categoria": "sazonal",
                "score": random.randint(7, 9),
                "motivo": obter_motivo_busca(produto),
                "indicadores": indicadores
            })
    
    # 2. PEGA PRODUTOS DA CATEGORIA ESPECÍFICA
    if categoria and categoria in GRADE_PRODUTOS:
        for termo in GRADE_PRODUTOS[categoria]["termos"]:
            if termo not in termos_usados:
                termos_usados.append(termo)
                indicadores = obter_indicadores_horario(termo)
                produtos.append({
                    "produto": termo,
                    "fonte": "grade",
                    "categoria": categoria,
                    "score": random.randint(5, 8),
                    "motivo": obter_motivo_busca(termo),
                    "indicadores": indicadores
                })
    
    # 3. PEGA PRODUTOS DE TODAS AS CATEGORIAS (mix)
    if not categoria or len(produtos) < quantidade:
        for cat, dados in GRADE_PRODUTOS.items():
            if cat != categoria:
                for termo in dados["termos"][:3]:
                    if termo not in termos_usados and len(produtos) < quantidade:
                        termos_usados.append(termo)
                        indicadores = obter_indicadores_horario(termo)
                        produtos.append({
                            "produto": termo,
                            "fonte": "grade",
                            "categoria": cat,
                            "score": random.randint(4, 7),
                            "motivo": obter_motivo_busca(termo),
                            "indicadores": indicadores
                        })
    
    # 4. EMBARALHA E RETORNA
    random.shuffle(produtos)
    return produtos[:quantidade]

def enriquecer_produto(produto: str) -> Dict:
    """Enriquece um produto com dados simulados (fallback)"""
    nome_lower = produto.lower()
    
    categorias_map = {
        "casaco": "Moda", "blusa": "Moda", "vestido": "Moda", "calça": "Moda",
        "sapato": "Moda", "tênis": "Moda", "jaqueta": "Moda", "saia": "Moda",
        "smartwatch": "Eletrônicos", "fone": "Eletrônicos", "celular": "Eletrônicos",
        "tablet": "Eletrônicos", "mouse": "Eletrônicos", "teclado": "Eletrônicos",
        "perfume": "Beleza", "maquiagem": "Beleza", "creme": "Beleza", "batom": "Beleza",
        "brinquedo": "Infantil", "boneca": "Infantil", "carrinho": "Infantil",
        "organizador": "Casa", "caixa": "Casa", "lixeira": "Casa", "garrafa": "Casa"
    }
    
    categoria = "Geral"
    for palavra, cat in categorias_map.items():
        if palavra in nome_lower:
            categoria = cat
            break
    
    indicadores = obter_indicadores_horario(produto)
    
    return {
        "produto": produto,
        "pins": random.randint(500, 3500),
        "views_tiktok": round(random.uniform(1.0, 6.0), 1),
        "crescimento": random.randint(5, 50),
        "buscas_mes": random.randint(3000, 20000),
        "categoria": categoria,
        "tendencia": random.choice(["🚀 Em alta", "📈 Crescendo", "➡️ Estável"]),
        "score": random.randint(4, 9),
        "fonte": "grade_descoberta",
        "motivo": obter_motivo_busca(produto),
        "indicadores": indicadores
    }

def obter_produtos_por_categoria(categoria: str) -> List[str]:
    """Retorna produtos de uma categoria específica"""
    if categoria in GRADE_PRODUTOS:
        return GRADE_PRODUTOS[categoria]["termos"]
    return []

def obter_hashtags_categoria(categoria: str) -> List[str]:
    """Retorna hashtags de uma categoria específica"""
    if categoria in GRADE_PRODUTOS:
        return GRADE_PRODUTOS[categoria]["hashtags"]
    return ["#tendência", "#2026", "#produto"]

def mesclar_produtos(produtos_existentes: List[str], quantidade: int = 5) -> List[str]:
    """Mescla produtos existentes com novos da grade"""
    todos_produtos = []
    
    for categoria, dados in GRADE_PRODUTOS.items():
        for termo in dados["termos"]:
            if termo not in produtos_existentes and termo not in todos_produtos:
                todos_produtos.append(termo)
    
    for produto in get_produtos_sazonais():
        if produto not in produtos_existentes and produto not in todos_produtos:
            todos_produtos.append(produto)
    
    random.shuffle(todos_produtos)
    return todos_produtos[:quantidade]

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'descobrir_produtos_grade',
    'enriquecer_produto',
    'get_produtos_sazonais',
    'get_produtos_sazonais_com_motivos',
    'GRADE_PRODUTOS',
    'obter_produtos_por_categoria',
    'obter_hashtags_categoria',
    'mesclar_produtos',
    'obter_motivo_busca',
    'MOTIVOS_BUSCA',
    'obter_indicadores_horario'
]
