"""
Módulo de Apoio a Criadores de Conteúdo
Gera roteiros, títulos, scripts e estratégias para vídeos
"""

import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# ============================================================
# ARQUIVO DE CACHE DE CONTEÚDO
# ============================================================
ARQUIVO_CONTEUDO_CACHE = "conteudo_cache.json"

# ============================================================
# TEMPLATES DE ROTEIRO POR CATEGORIA
# ============================================================
TEMPLATES_ROTEIRO = {
    "moda": {
        "ganchos": [
            "Já pensou em arrasar nesse look sem gastar muito?",
            "O item que vai dominar o inverno 2026 chegou!",
            "Essa peça está fazendo sucesso e eu vou te mostrar por quê!",
            "Look do dia com 3 peças que você precisa ter!",
            "O que usar no frio sem parecer uma cebola? 🤔"
        ],
        "desenvolvimento": [
            "Mostre o produto em detalhes, destacando tecido e caimento.",
            "Faça 3 combinações diferentes com a mesma peça.",
            "Compare com marcas famosas e mostre o custo-benefício.",
            "Mostre como usar em diferentes ocasiões (trabalho, festa, dia a dia).",
            "Dê dicas de acessórios que combinam com a peça."
        ],
        "ctas": [
            "O link está aqui na descrição - corre porque está esgotando!",
            "Me conta nos comentários qual combinação você mais gostou!",
            "Já salva esse vídeo para comprar depois!",
            "Comenta EU QUERO se você também amou esse look!"
        ],
        "hashtags_modelo": ["#lookdodia", "#moda2026", "#tendenciamoda", "#lookinverno"]
    },
    
    "eletrônico": {
        "ganchos": [
            "Você realmente precisa desse novo gadget? Vamos testar!",
            "O aparelho que promete mudar sua rotina - será que vale?",
            "Comparativo: versão cara vs versão acessível!",
            "3 funções que você nem sabia que esse aparelho tinha!",
            "Isso é golpe ou o melhor custo-benefício do mercado?"
        ],
        "desenvolvimento": [
            "Faça unboxing mostrando todos os itens da caixa.",
            "Teste todas as funcionalidades em situações reais.",
            "Compare com outros produtos similares no mesmo preço.",
            "Mostre os prós e contras de forma honesta.",
            "Faça um teste de durabilidade ou resistência."
        ],
        "ctas": [
            "Já adiciona no carrinho - eu te garanto que vale a pena!",
            "Me diz nos comentários: você prefere esse ou o concorrente?",
            "Salva esse vídeo para comparar depois!",
            "Segue para mais reviews como esse!"
        ],
        "hashtags_modelo": ["#tecnologia", "#review", "#gadgets", "#unboxing"]
    },
    
    "beleza": {
        "ganchos": [
            "O segredo para uma pele perfeita em 3 passos!",
            "Esse produto de beleza está viralizando - será que funciona?",
            "Kit perfeito para presentear - spoiler: é BEM acessível!",
            "Rotina de beleza completa em 5 minutos? Vem ver!",
            "Maquiagem com produtos que você tem em casa - desafio!"
        ],
        "desenvolvimento": [
            "Mostre a textura e o cheiro do produto.",
            "Faça um teste na pele mostrando antes e depois.",
            "Mostre como aplicar corretamente para melhor resultado.",
            "Faça 3 looks diferentes com o mesmo produto.",
            "Mostre durabilidade após horas de uso."
        ],
        "ctas": [
            "Corre que eu garanto que vai esgotar!",
            "Qual desses looks você usaria? Me conta aqui!",
            "Salva esse vídeo para depois não esquecer!",
            "Segue para mais dicas de beleza!"
        ],
        "hashtags_modelo": ["#belezafeminina", "#skincare", "#maquiagem", "#tutorial"]
    },
    
    "casa": {
        "ganchos": [
            "Organize sua casa com essas dicas simples e baratas!",
            "O item que vai transformar seu ambiente - e é muito acessível!",
            "Decoração com menos de R$ 100 - você precisa ver!",
            "Minha rotina de limpeza com produtos AMIGOS do bolso!",
            "Antes e depois que vai te inspirar a organizar AGORA!"
        ],
        "desenvolvimento": [
            "Mostre o antes e depois da organização.",
            "Explique como instalar ou montar o produto.",
            "Dê dicas de onde colocar para maximizar espaço.",
            "Mostre o produto em diferentes ambientes.",
            "Compare com outras opções de mercado."
        ],
        "ctas": [
            "Já salva e compartilha com quem precisa organizar a casa!",
            "Me conta: qual dica você vai aplicar hoje?",
            "Link na descrição - corre antes que acabe!",
            "Segue para mais dicas de organização!"
        ],
        "hashtags_modelo": ["#organizacao", "#decoraçãocasa", "#casa", "#diy"]
    },
    
    "infantil": {
        "ganchos": [
            "O brinquedo que vai salvar seu dia com as crianças!",
            "Meu filho AMOU e eu também - olha que presente incrível!",
            "3 brinquedos educativos para crianças de 2 a 5 anos!",
            "Como entreter as crianças sem gastar muito? Vem ver!",
            "O brinquedo que é sucesso garantido - testei e aprovei!"
        ],
        "desenvolvimento": [
            "Mostre a criança interagindo com o brinquedo.",
            "Explique os benefícios educativos do produto.",
            "Mostre diferentes formas de brincar.",
            "Fale sobre segurança e faixa etária.",
            "Compare com outros brinquedos similares."
        ],
        "ctas": [
            "Salva esse vídeo para a próxima compra de presente!",
            "Seu filho vai amar - me conta qual ele gostou mais!",
            "Link na descrição - presente perfeito!",
            "Segue para mais dicas de presentes infantis!"
        ],
        "hashtags_modelo": ["#brinquedos", "#infantil", "#educativo", "#presentes"]
    },
    
    "esporte": {
        "ganchos": [
            "O item que todo atleta precisa ter!",
            "Teste: será que vale o investimento?",
            "Melhores produtos para começar no esporte!",
            "3 produtos que vão transformar seu treino!",
            "Descubra o que os profissionais usam e o custo-benefício!"
        ],
        "desenvolvimento": [
            "Mostre o produto em ação durante o esporte.",
            "Teste todas as funcionalidades.",
            "Compare com versões mais caras.",
            "Mostre durabilidade e resistência.",
            "Dê dicas de manutenção e cuidados."
        ],
        "ctas": [
            "Já se inscreve para mais conteúdo de esporte!",
            "Qual desses você já usou? Comenta aqui!",
            "Link na bio - não perde essa chance!",
            "Salva pra ver depois com calma!"
        ],
        "hashtags_modelo": ["#esporte", "#fitness", "#treino", "#performance"]
    }
}

# ============================================================
# TEMPLATES DE TÍTULOS POR PLATAFORMA
# ============================================================
TEMPLATES_TITULOS = {
    "tiktok": [
        "🔥 {produto} - vale a pena? {emoji}",
        "NUNCA VI {produto} por esse preço 😱",
        "{produto}: o segredo que ninguém te contou 🤫",
        "{produto} em 2026 - É golpe? 👀",
        "ISSO MUDOU MINHA VIDA: {produto}",
        "ABRE O CORAÇÃO: {produto} que eu AMEI 💗",
        "VOCÊ TEM que ver isso: {produto}",
        "A MAIOR PROMOÇÃO de {produto} do ano!",
        "TCHAU {produto concorrente}, OLÁ {produto}!",
        "Desafio: {produto} em 30 segundos ⏰"
    ],
    "reels": [
        "O que ninguém te conta sobre {produto}",
        "Vale a pena comprar {produto}? Review completo!",
        "{produto}: antes e depois que vai te surpreender",
        "3 motivos pra COMPRAR {produto} (e 1 motivo pra NÃO)",
        "A verdade sobre {produto} que vendedores escondem",
        "Testei {produto} e o resultado foi...",
        "Meninas, vocês PRECISAM conhecer {produto}!",
        "Esqueça {produto concorrente}, compre {produto}!",
        "Como usar {produto} do jeito certo",
        "MEU DEUS! {produto} é realmente BOM?"
    ],
    "shorts": [
        "🚀 {produto} MUDOU TUDO!",
        "🤯 {produto} VALE O INVESTIMENTO?",
        "💎 O SEGREDO REVELADO: {produto}",
        "❗ ISSO É GOLPE? {produto}",
        "🔥 TOP 1 {produto} DO MUNDO!",
        "✅ {produto} APROVADO OU NÃO?"
    ]
}

# ============================================================
# TEMPLATES DE SCRIPTS COMPLETOS
# ============================================================
def gerar_script_completo(produto: str, categoria: str, duracao: str = "curto") -> Dict:
    """
    Gera script completo para vídeo
    
    Args:
        produto (str): Nome do produto
        categoria (str): Categoria do produto
        duracao (str): curto (15-30s), medio (30-60s), longo (60-90s)
    
    Returns:
        Dict: Script completo com cenas e falas
    """
    
    template = TEMPLATES_ROTEIRO.get(categoria, TEMPLATES_ROTEIRO["moda"])
    
    gancho = random.choice(template["ganchos"])
    desenvolvimento = random.choice(template["desenvolvimento"])
    cta = random.choice(template["ctas"])
    hashtags = template["hashtags_modelo"]
    
    # Define estrutura baseada na duração
    if duracao == "curto":
        cenas = [
            {"cena": 1, "enquadramento": "Close-up no produto", "duracao": "3s", "fala": gancho},
            {"cena": 2, "enquadramento": "Produto em uso", "duracao": "5s", "fala": desenvolvimento[:100]},
            {"cena": 3, "enquadramento": "Mostra resultado", "duracao": "3s", "fala": cta}
        ]
        total_duracao = 15
    elif duracao == "medio":
        cenas = [
            {"cena": 1, "enquadramento": "Abertura chamativa", "duracao": "5s", "fala": gancho},
            {"cena": 2, "enquadramento": "Apresentação do produto", "duracao": "10s", "fala": f"Vamos analisar o {produto} em detalhes..."},
            {"cena": 3, "enquadramento": "Teste/uso do produto", "duracao": "15s", "fala": desenvolvimento},
            {"cena": 4, "enquadramento": "Opinião final", "duracao": "10s", "fala": cta}
        ]
        total_duracao = 40
    else:  # longo
        cenas = [
            {"cena": 1, "enquadramento": "Gancho forte", "duracao": "5s", "fala": gancho},
            {"cena": 2, "enquadramento": "Unboxing", "duracao": "15s", "fala": f"Hoje vamos abrir esse {produto} e ver se vale o hype..."},
            {"cena": 3, "enquadramento": "Análise técnica", "duracao": "20s", "fala": "Vamos analisar cada detalhe..."},
            {"cena": 4, "enquadramento": "Teste real", "duracao": "25s", "fala": desenvolvimento},
            {"cena": 5, "enquadramento": "Comparação", "duracao": "15s", "fala": "Comparando com outros produtos do mercado..."},
            {"cena": 6, "enquadramento": "Conclusão e CTA", "duracao": "10s", "fala": cta}
        ]
        total_duracao = 90
    
    return {
        "produto": produto,
        "categoria": categoria,
        "duracao_total": total_duracao,
        "hashtags": hashtags,
        "cenas": cenas,
        "link_shopee": f"https://shopee.com.br/search?keyword={produto.replace(' ', '%20')}"
    }

# ============================================================
# GERAR SUGESTÕES DE TÍTULOS
# ============================================================
def gerar_titulos(produto: str, categoria: str = "moda", qtd: int = 5) -> List[str]:
    """
    Gera títulos chamativos para o produto
    
    Args:
        produto (str): Nome do produto
        categoria (str): Categoria do produto
        qtd (int): Quantidade de títulos
    
    Returns:
        List[str]: Lista de títulos
    """
    titulos = []
    emojis = ["🔥", "😱", "🤯", "💎", "🚀", "⭐", "❤️", "💥", "✨", "🎯"]
    
    # Títulos baseados na categoria
    if categoria == "moda":
        templates_moda = [
            "O LOOK QUE TODO MUNDO VAI USAR: {produto}",
            "{produto} - A PEÇA QUE VOCÊ PRECISA TER!",
            "COMO USAR {produto} EM 3 LOOKS DIFERENTES",
            "{produto} VALERÁ A PENA? Review honesto",
            "Meninas, {produto} é OBBBBBB {emoji}",
            "TCHAU CARTÃO, OLÁ {produto}!",
            "O SEGREDO DO LOOK PERFEITO: {produto}",
            "VOCÊ VAI AMAR {produto}! Testei e aprovei",
            "ESTILO COM {produto} - como fazer acontecer",
            "{produto}: A TENDÊNCIA QUE VOCÊ NÃO PODE PERDER"
        ]
        templates = templates_moda
    elif categoria in ["eletrônico", "eletronicos"]:
        templates_elec = [
            "REVIEW COMPLETO: {produto} VALE?",
            "{produto} - O que ninguém te conta!",
            "COMPREI {produto} - teste e opinião",
            "{produto} vs {produto concorrente}: quem ganha?",
            "3 COISAS QUE AMEI NO {produto}",
            "{produto} É GOLPE OU OPORTUNIDADE?",
            "UNBOXING {produto} - veio tudo certinho?",
            "O MELHOR {produto} DO MERCADO? Descubra!",
            "{produto} - será que vale o investimento?",
            "Testei {produto} por 1 semana - o resultado..."
        ]
        templates = templates_elec
    elif categoria in ["beleza", "skincare", "maquiagem"]:
        templates_beleza = [
            "ROTINA DE BELEZA: {produto}",
            "{produto} - vai mudar sua pele!",
            "ANTES E DEPOIS usando {produto}",
            "O segredo da pele perfeita: {produto}",
            "TESTEI {produto} e não esperava isso!",
            "MAKE COM {produto} - tutorial fácil",
            "MEU DEUS, {produto} é muito BOM!",
            "VOCÊ PRECISA DE {produto} - olha isso!",
            "KIT DE BELEZA: {produto} + acessórios",
            "ESSE {produto} VAI MUDAR SUA ROTINA"
        ]
        templates = templates_beleza
    else:
        templates = [
            "CONHEÇA {produto} - você vai se surpreender!",
            "{produto} - antes e depois",
            "TESTAMOS {produto} - veja o que achamos",
            "VOCÊ JÁ VIU {produto}?",
            "A VERDADE SOBRE {produto}",
            "VALE A PENA? {produto}",
            "TUDO SOBRE {produto} - review completo",
            "Descobri {produto} e não quero mais viver sem",
            "VOCÊ PRECISA VER {produto}",
            "O MELHOR {produto} DO MUNDO?"
        ]
    
    # Preenche os templates
    for i in range(min(qtd, len(templates))):
        titulo = templates[i % len(templates)].format(
            produto=produto.upper(),
            produto_concorrente=random.choice(["concorrente", "outra marca", "versão cara"]),
            emoji=random.choice(emojis)
        )
        
        # Adiciona um ou dois emojis extras em alguns títulos
        if i % 2 == 0:
            titulo = f"{random.choice(emojis)} {titulo}"
        if i % 3 == 0:
            titulo = f"{titulo} {random.choice(emojis)}"
        
        titulos.append(titulo)
    
    return titulos[:qtd]

# ============================================================
# GERAR DICAS DE GRAVAÇÃO
# ============================================================
def gerar_dicas_gravacao(produto: str, categoria: str) -> Dict:
    """
    Gera dicas de gravação para o vídeo
    
    Args:
        produto (str): Nome do produto
        categoria (str): Categoria do produto
    
    Returns:
        Dict: Dicas de gravação
    """
    # Cenários sugeridos
    cenarios = {
        "moda": [
            "Use um fundo neutro para destacar a peça",
            "Coloque luz natural (janela) em um ângulo de 45°",
            "Mostre o produto em movimento (andar, girar)",
            "Use espelho grande para mostrar o look completo",
            "Faça close nos detalhes do tecido/estampa"
        ],
        "eletrônico": [
            "Grave em uma mesa com luz branca/natural",
            "Mostre o produto de todos os ângulos",
            "Use iluminação adicional para evitar sombras",
            "Grave em slow motion para detalhes técnicos",
            "Mostre o produto funcionando com cenário real"
        ],
        "beleza": [
            "Use luz natural (ou ring light) para mostrar a pele",
            "Grave em um local com boa iluminação",
            "Mostre a textura do produto antes e depois",
            "Use um espelho ampliador para detalhes",
            "Mantenha o fundo limpo e neutro"
        ],
        "casa": [
            "Mostre o ambiente completo antes/depois",
            "Use luz natural para realçar o produto",
            "Mostre o produto em diferentes ângulos",
            "Faça um plano detalhado do produto",
            "Mostre a praticidade do uso diário"
        ],
        "infantil": [
            "Grave em um ambiente colorido e lúdico",
            "Mostre a criança brincando naturalmente",
            "Use luz natural para evitar pontos brancos",
            "Capte a reação genuína da criança",
            "Mostre detalhes de segurança do brinquedo"
        ],
        "esporte": [
            "Grave em um ambiente que remeta ao esporte",
            "Mostre o produto em movimento/ação",
            "Use luz natural para evitar sombras",
            "Mostre detalhes de ergonomia e conforto",
            "Grave de diferentes ângulos (câmera dinâmica)"
        ]
    }
    
    # Dicas de áudio
    dicas_audio = [
        "Use um microfone de lapela para melhor qualidade de áudio",
        "Evite ambientes com muito eco",
        "Mantenha o volume da música de fundo baixo",
        "Grave em um local silencioso",
        "Adicione música de acordo com o nicho do produto"
    ]
    
    # Melhores horários
    melhores_horarios = [
        "Manhã: 8h-10h (público mais engajado)",
        "Tarde: 14h-16h (pico de visualizações)",
        "Noite: 19h-21h (maior retenção)",
        "Final de semana: 10h-12h (maior engajamento)"
    ]
    
    return {
        "produto": produto,
        "categoria": categoria,
        "cenarios_sugeridos": random.sample(cenarios.get(categoria, cenarios["moda"]), min(3, len(cenarios.get(categoria, [])))),
        "dicas_audio": dicas_audio[:3],
        "melhores_horarios": melhores_horarios,
        "duracao_sugerida": random.choice(["15-30 segundos", "30-45 segundos", "45-60 segundos"]),
        "legendas_sugeridas": [
            f"📍 {produto} disponível no link da bio!",
            f"💡 Dica: Use {produto} com...",
            f"💰 Vale cada centavo: {produto}"
        ]
    }

# ============================================================
# ANALISAR CONCORRÊNCIA
# ============================================================
def analisar_concorrencia(produto: str) -> Dict:
    """
    Simula análise da concorrência para um produto
    
    Args:
        produto (str): Nome do produto
    
    Returns:
        Dict: Análise da concorrência
    """
    
    # Dados simulados baseados no produto
    palavras_chave = produto.lower().split()
    
    # Concorrentes simulados
    concorrentes = [
        {"nome": f"{produto} Pro", "preco": random.randint(200, 600), "avaliacao": random.uniform(3.5, 5.0)},
        {"nome": f"{produto} Premium", "preco": random.randint(100, 400), "avaliacao": random.uniform(3.0, 4.5)},
        {"nome": f"{produto} Lite", "preco": random.randint(50, 200), "avaliacao": random.uniform(2.5, 4.0)}
    ]
    
    # Diferenciais sugeridos
    diferenciais = [
        "Melhor custo-benefício da categoria",
        "Design mais moderno e funcional",
        "Maior durabilidade comprovada",
        "Garantia estendida de fábrica",
        "Mais acessível que os concorrentes",
        "Material de qualidade premium"
    ]
    
    return {
        "produto": produto,
        "concorrentes": concorrentes,
        "diferenciais_sugeridos": random.sample(diferenciais, 3),
        "posicionamento_sugerido": f"{produto} é ideal para quem busca qualidade sem pagar o preço das marcas famosas.",
        "ponto_forte": random.choice([
            f"O {produto} tem o melhor custo-benefício",
            f"A qualidade do {produto} surpreende",
            f"O {produto} é mais durável que os concorrentes"
        ])
    }

# ============================================================
# FUNÇÃO PRINCIPAL - GERAR CONTEÚDO COMPLETO
# ============================================================
def gerar_conteudo_completo(produto: str, categoria: str = "moda", duracao: str = "medio") -> Dict:
    """
    Gera conteúdo completo para o criador
    
    Args:
        produto (str): Nome do produto
        categoria (str): Categoria do produto
        duracao (str): curto, medio, longo
    
    Returns:
        Dict: Conteúdo completo com roteiro, títulos, dicas
    """
    
    return {
        "produto": produto,
        "categoria": categoria,
        "timestamp": datetime.now().isoformat(),
        "script": gerar_script_completo(produto, categoria, duracao),
        "titulos": gerar_titulos(produto, categoria),
        "dicas_gravacao": gerar_dicas_gravacao(produto, categoria),
        "analise_concorrencia": analisar_concorrencia(produto),
        "hashtags_sugeridas": [
            f"#{produto.lower().replace(' ', '')}",
            "#review",
            "#viral",
            f"#{categoria.lower()}",
            "#valeapena",
            "#compras",
            "#tendencia"
        ]
    }

# ============================================================
# FUNÇÕES DE CACHE
# ============================================================
def salvar_conteudo_cache(conteudo: Dict) -> bool:
    """Salva conteúdo gerado em cache"""
    try:
        if os.path.exists(ARQUIVO_CONTEUDO_CACHE):
            with open(ARQUIVO_CONTEUDO_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        else:
            cache = {}
        
        chave = f"{conteudo['produto']}_{datetime.now().date().isoformat()}"
        cache[chave] = conteudo
        
        with open(ARQUIVO_CONTEUDO_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def carregar_conteudo_cache(produto: str) -> Dict:
    """Carrega conteúdo do cache"""
    try:
        if os.path.exists(ARQUIVO_CONTEUDO_CACHE):
            with open(ARQUIVO_CONTEUDO_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            chave = f"{produto}_{datetime.now().date().isoformat()}"
            if chave in cache:
                return cache[chave]
    except:
        pass
    return None

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'gerar_script_completo',
    'gerar_titulos',
    'gerar_dicas_gravacao',
    'analisar_concorrencia',
    'gerar_conteudo_completo',
    'salvar_conteudo_cache',
    'carregar_conteudo_cache'
]
