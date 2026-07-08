import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Importa sistema de produtos dinâmicos
from modules.produtos_dinamicos import obter_produtos_dinamicos, PRODUTOS_FALLBACK

# ============================================================
# ARQUIVOS DE DADOS (NA RAIZ)
# ============================================================
ARQUIVO_APOIADORES = "apoiadores.json"

# ============================================================
# FUNÇÕES DE APOIADORES
# ============================================================
def carregar_apoiadores():
    """Carrega a lista de apoiadores do arquivo na raiz"""
    if os.path.exists(ARQUIVO_APOIADORES):
        try:
            with open(ARQUIVO_APOIADORES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Dados padrão
    apoiadores_padrao = {
        "mayara": {
            "nome": "Mayara Veloso",
            "ordem": 1,
            "email": "mayara@email.com",
            "coroinha": "👑",
            "cor": "#FF6B6B",
            "data_entrada": "2026-07-01",
            "royalties_recebidos": 0.0,
            "repasse_ativo": True,
            "plano": "Fundadora"
        },
        "iago": {
            "nome": "Iago Coelho",
            "ordem": 2,
            "email": "iago@email.com",
            "coroinha": "👑",
            "cor": "#4ECDC4",
            "data_entrada": "2026-07-05",
            "royalties_recebidos": 0.0,
            "repasse_ativo": True,
            "plano": "Apoiador"
        }
    }
    
    with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
        json.dump(apoiadores_padrao, f, ensure_ascii=False, indent=2)
    
    return apoiadores_padrao

def adicionar_apoiador(nome, email, plano="Apoiador"):
    """Adiciona um novo apoiador"""
    apoiadores = carregar_apoiadores()
    
    ordem = max([a.get("ordem", 0) for a in apoiadores.values()]) + 1 if apoiadores else 1
    
    cores = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE"]
    cor = cores[(ordem - 1) % len(cores)]
    
    novo_apoiador = {
        "nome": nome,
        "ordem": ordem,
        "email": email,
        "coroinha": "👑",
        "cor": cor,
        "data_entrada": datetime.now().strftime("%Y-%m-%d"),
        "royalties_recebidos": 0.0,
        "repasse_ativo": True,
        "plano": plano
    }
    
    import uuid
    id_apoiador = str(uuid.uuid4())[:8]
    apoiadores[id_apoiador] = novo_apoiador
    
    with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
        json.dump(apoiadores, f, ensure_ascii=False, indent=2)
    
    return novo_apoiador

def remover_apoiador(id_apoiador):
    """Remove um apoiador pelo ID e reorganiza as ordens"""
    apoiadores = carregar_apoiadores()
    
    if id_apoiador not in apoiadores:
        return False
    
    del apoiadores[id_apoiador]
    
    ordem = 1
    for key in sorted(apoiadores.keys(), key=lambda x: apoiadores[x].get("ordem", 999)):
        apoiadores[key]["ordem"] = ordem
        ordem += 1
    
    with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
        json.dump(apoiadores, f, ensure_ascii=False, indent=2)
    
    return True

# ============================================================
# DADOS DE PRODUTOS (DINÂMICOS)
# ============================================================
def obter_dados_completos(forcar_atualizacao: bool = True) -> Dict:
    """
    Obtém dados completos de produtos (dinâmicos)
    SEMPRE FORÇA ATUALIZAÇÃO
    """
    return obter_produtos_dinamicos(forcar_atualizacao=True)

# ============================================================
# PALAVRAS CHAVE - EXPANDIDAS E ESPECÍFICAS
# ============================================================
PALAVRAS_CHAVE_CAUDA_LONGA = {
    # MODA
    "casaco": {
        "palavra": "casaco feminino inverno 2026",
        "hashtags": ["#casacofeminino", "#inverno2026", "#lookinverno", "#modainverno"]
    },
    "blusa": {
        "palavra": "blusa de lã elegante feminina",
        "hashtags": ["#blusadelã", "#modainverno", "#lookelegante", "#feminino"]
    },
    "blusa de lã": {
        "palavra": "blusa de lã elegante feminina",
        "hashtags": ["#blusadelã", "#modainverno", "#lookelegante", "#feminino"]
    },
    "vestido": {
        "palavra": "vestido longo festa verão 2026",
        "hashtags": ["#vestidofeminino", "#modaverao", "#lookfestival", "#verao2026"]
    },
    "sapato": {
        "palavra": "sapato salto alto feminino conforto",
        "hashtags": ["#sapatofeminino", "#moda", "#sapatoespecial", "#look"]
    },
    "sapateira": {
        "palavra": "sapateira organizadora de sapatos",
        "hashtags": ["#sapateira", "#organizador", "#casa", "#organização"]
    },
    "tênis": {
        "palavra": "tênis esportivo masculino conforto",
        "hashtags": ["#tenis", "#esporte", "#moda", "#conforto", "#corrida"]
    },
    "tenis": {
        "palavra": "tênis esportivo masculino conforto",
        "hashtags": ["#tenis", "#esporte", "#moda", "#conforto", "#corrida"]
    },
    "calça": {
        "palavra": "calça jeans feminina cintura alta",
        "hashtags": ["#calçajeans", "#modafeminina", "#jeans", "#look"]
    },
    "camisa": {
        "palavra": "camisa social masculina slim",
        "hashtags": ["#camisa", "#modamasculina", "#social", "#slim"]
    },
    "roupas": {
        "palavra": "roupas femininas elegantes",
        "hashtags": ["#roupasfemininas", "#moda", "#look", "#feminino"]
    },
    "roupa": {
        "palavra": "roupas femininas elegantes",
        "hashtags": ["#roupasfemininas", "#moda", "#look", "#feminino"]
    },
    "lingerie": {
        "palavra": "lingerie feminina sensual",
        "hashtags": ["#lingerie", "#feminino", "#sedução", "#modaintima"]
    },
    "espelho": {
        "palavra": "espelho decorativo para sala",
        "hashtags": ["#espelho", "#decoração", "#casa", "#sala"]
    },
    "bota": {
        "palavra": "bota feminina cano curto",
        "hashtags": ["#bota", "#modafeminina", "#inverno", "#look"]
    },
    # ELETRÔNICOS
    "smartwatch": {
        "palavra": "smartwatch feminino elegante 2026",
        "hashtags": ["#smartwatch", "#tecnologia", "#eletrônicos", "#mulherdigital"]
    },
    "fone": {
        "palavra": "fone bluetooth JBL original",
        "hashtags": ["#fonebluetooth", "#áudio", "#tecnologia", "#jbl"]
    },
    "fone bluetooth": {
        "palavra": "fone bluetooth JBL original",
        "hashtags": ["#fonebluetooth", "#áudio", "#tecnologia", "#jbl"]
    },
    "controle pc": {
        "palavra": "controle para PC gamer sem fio",
        "hashtags": ["#controlepc", "#gamer", "#pc", "#games"]
    },
    "controle": {
        "palavra": "controle para PC gamer sem fio",
        "hashtags": ["#controlepc", "#gamer", "#pc", "#games"]
    },
    "pc": {
        "palavra": "PC gamer completo setup",
        "hashtags": ["#pcgamer", "#setup", "#games", "#tecnologia"]
    },
    "celular": {
        "palavra": "celular smartphone 5G camera 108MP",
        "hashtags": ["#smartphone", "#tecnologia", "#5g", "#fotografia"]
    },
    "tablet": {
        "palavra": "tablet para estudos e trabalho 2026",
        "hashtags": ["#tablet", "#estudos", "#tecnologia", "#produtividade"]
    },
    "relógio": {
        "palavra": "relógio masculino elegante premium",
        "hashtags": ["#relogio", "#masculino", "#elegante", "#acessório"]
    },
    "ar condicionado": {
        "palavra": "ar condicionado portátil 12000 BTUs",
        "hashtags": ["#arcondicionado", "#climatizador", "#casa", "#conforto"]
    },
    "ar condicionado portátil": {
        "palavra": "ar condicionado portátil 12000 BTUs",
        "hashtags": ["#arcondicionado", "#climatizador", "#casa", "#conforto"]
    },
    "elgin": {
        "palavra": "ar condicionado Elgin 12000 BTUs",
        "hashtags": ["#elgin", "#arcondicionado", "#climatizador", "#casa"]
    },
    # BELEZA
    "perfume": {
        "palavra": "perfume importado floral feminino",
        "hashtags": ["#perfumeimportado", "#belezafeminina", "#presentes", "#floral"]
    },
    "perfume importado": {
        "palavra": "perfume importado floral feminino",
        "hashtags": ["#perfumeimportado", "#belezafeminina", "#presentes", "#floral"]
    },
    "maquiagem": {
        "palavra": "kit maquiagem profissional completo",
        "hashtags": ["#maquiagem", "#belezafeminina", "#makeup", "#profissional"]
    },
    "creme": {
        "palavra": "creme hidratante facial antissinais",
        "hashtags": ["#cremehidratante", "#skincare", "#belezafeminina", "#antiidade"]
    },
    "kit loreal": {
        "palavra": "kit L'Oréal Paris skincare",
        "hashtags": ["#loreal", "#skincare", "#beleza", "#cuidados"]
    },
    "loreal": {
        "palavra": "kit L'Oréal Paris skincare",
        "hashtags": ["#loreal", "#skincare", "#beleza", "#cuidados"]
    },
    # CASA E ORGANIZAÇÃO
    "organizador": {
        "palavra": "organizador de gavetas e armários",
        "hashtags": ["#organizador", "#casa", "#organização", "#decoração"]
    },
    "caixa": {
        "palavra": "caixa organizadora plástica empilhável",
        "hashtags": ["#caixaorganizadora", "#casa", "#organização", "#armazenamento"]
    },
    "caixa organizadora": {
        "palavra": "caixa organizadora plástica empilhável",
        "hashtags": ["#caixaorganizadora", "#casa", "#organização", "#armazenamento"]
    },
    "lixeira": {
        "palavra": "lixeira cozinha inox pedal",
        "hashtags": ["#lixeira", "#cozinha", "#inox", "#organização"]
    },
    "lixeira cozinha": {
        "palavra": "lixeira cozinha inox pedal",
        "hashtags": ["#lixeira", "#cozinha", "#inox", "#organização"]
    },
    "garrafa": {
        "palavra": "garrafa térmica inox 1L",
        "hashtags": ["#garrafatermica", "#casa", "#inox", "#hidratação"]
    },
    "garrafa térmica": {
        "palavra": "garrafa térmica inox 1L",
        "hashtags": ["#garrafatermica", "#casa", "#inox", "#hidratação"]
    },
    "sacola": {
        "palavra": "sacola personalizada ecobag",
        "hashtags": ["#sacola", "#ecobag", "#sustentável", "#personalizada"]
    },
    "sacola personalizada": {
        "palavra": "sacola personalizada ecobag",
        "hashtags": ["#sacola", "#ecobag", "#sustentável", "#personalizada"]
    },
    "kit cadeira": {
        "palavra": "kit cadeira e mesa para escritório",
        "hashtags": ["#cadeira", "#escritório", "#homeoffice", "#mobília"]
    },
    "cadeira": {
        "palavra": "cadeira gamer confortável",
        "hashtags": ["#cadeiragamer", "#games", "#setup", "#conforto"]
    },
    # INFANTIL
    "brinquedo": {
        "palavra": "brinquedo educativo infantil 2 anos",
        "hashtags": ["#brinquedo", "#infantil", "#educativo", "#crianças"]
    },
    "boneca": {
        "palavra": "boneca interativa falante",
        "hashtags": ["#boneca", "#infantil", "#brinquedo", "#presente"]
    },
    "carrinho": {
        "palavra": "carrinho de controle remoto",
        "hashtags": ["#carrinho", "#infantil", "#controle", "#brinquedo"]
    },
    "moto infantil": {
        "palavra": "moto infantil elétrica",
        "hashtags": ["#motoinfantil", "#crianças", "#brinquedo", "#elétrico"]
    },
    # ESPORTE E LAZER
    "chopeira": {
        "palavra": "chopeira elétrica 5L chopp",
        "hashtags": ["#chopeira", "#cerveja", "#chope", "#festa"]
    },
    "figurinha": {
        "palavra": "figurinha legend álbum completo",
        "hashtags": ["#figurinha", "#legend", "#coleção", "#álbum"]
    },
    "figurinha legend": {
        "palavra": "figurinha legend álbum completo",
        "hashtags": ["#figurinha", "#legend", "#coleção", "#álbum"]
    },
    "legend": {
        "palavra": "figurinha legend álbum completo",
        "hashtags": ["#figurinha", "#legend", "#coleção", "#álbum"]
    },
    "joia cobre": {
        "palavra": "joia de cobre elegante",
        "hashtags": ["#joia", "#cobre", "#bijuteria", "#elegante"]
    },
    "cobre": {
        "palavra": "joia de cobre elegante",
        "hashtags": ["#joia", "#cobre", "#bijuteria", "#elegante"]
    },
    "kenner": {
        "palavra": "tênis Kenner feminino",
        "hashtags": ["#kenner", "#tenis", "#moda", "#feminino"]
    },
    "kenner feminina": {
        "palavra": "tênis Kenner feminino",
        "hashtags": ["#kenner", "#tenis", "#moda", "#feminino"]
    },
    # PADRÃO (FALLBACK)
    "padrao": {
        "palavra": "produto tendência mercado 2026",
        "hashtags": ["#tendência", "#produto", "#2026", "#mercado"]
    }
}

def obter_palavra_chave(produto: str) -> Dict:
    """
    Obtém palavra-chave para um produto com busca inteligente
    """
    produto_lower = produto.lower().strip()
    
    # Remove palavras genéricas
    palavras_ignorar = [
        "produto", "novo", "lançamento", "tendência", "mercado",
        "kit", "com", "para", "de", "da", "do", "das", "dos", 
        "e", "em", "na", "no", "nas", "nos", "um", "uma", "uns", "umas",
        "a", "o", "as", "os", "ao", "aos", "à", "às"
    ]
    
    # 1. BUSCA EXATA
    if produto_lower in PALAVRAS_CHAVE_CAUDA_LONGA:
        return PALAVRAS_CHAVE_CAUDA_LONGA[produto_lower]
    
    # 2. BUSCA POR PALAVRA-CHAVE
    for chave, dados in PALAVRAS_CHAVE_CAUDA_LONGA.items():
        if chave in produto_lower:
            return dados
    
    # 3. BUSCA POR PALAVRAS INDIVIDUAIS
    palavras = [p for p in produto_lower.split() if p not in palavras_ignorar and len(p) > 2]
    
    for palavra in palavras:
        for chave, dados in PALAVRAS_CHAVE_CAUDA_LONGA.items():
            if palavra in chave or chave in palavra:
                return dados
    
    # 4. BUSCA POR CATEGORIA
    categorias = {
        "eletrônico": ["controle", "pc", "smartwatch", "fone", "celular", "tablet", "relógio", "ar condicionado", "elgin", "gamer", "tv", "monitor"],
        "moda": ["casaco", "blusa", "vestido", "sapato", "tênis", "tenis", "calça", "camisa", "roupa", "lingerie", "bota", "jaqueta", "saia", "short"],
        "casa": ["sapateira", "organizador", "caixa", "lixeira", "garrafa", "sacola", "cadeira", "espelho", "inox", "mesa", "sofá", "estante"],
        "beleza": ["perfume", "maquiagem", "creme", "loreal", "skincare", "makeup", "batom", "base", "rimel"],
        "infantil": ["brinquedo", "boneca", "carrinho", "moto", "crianças", "bebê", "nenê"],
        "esporte": ["chopeira", "figurinha", "legend", "kenner", "cerveja", "coleção", "bola", "chuteira"],
        "livro": ["livro", "leitura", "editora", "romance"],
        "ferramenta": ["furadeira", "parafusadeira", "serra", "chave", "alicate"]
    }
    
    for categoria, palavras_chave in categorias.items():
        for palavra_chave in palavras_chave:
            if palavra_chave in produto_lower:
                termo_base = produto_lower.replace(palavra_chave, "").strip()
                if termo_base and len(termo_base) > 2:
                    return {
                        "palavra": f"{palavra_chave} {termo_base} - {categoria}",
                        "hashtags": [f"#{palavra_chave}", f"#{categoria}", "#2026", "#tendência"]
                    }
                else:
                    return {
                        "palavra": f"{palavra_chave} - {categoria} 2026",
                        "hashtags": [f"#{palavra_chave}", f"#{categoria}", "#2026", "#tendência"]
                    }
    
    # 5. FALLBACK INTELIGENTE
    if len(palavras) > 0:
        termo_base = " ".join(palavras[:3])
        tipos = {
            "tecnologia": ["eletrônico", "digital", "tech", "gamer", "pc", "smart", "fone", "celular"],
            "moda": ["roupa", "vestuário", "look", "jeans", "sapato", "tenis", "camisa", "blusa", "casaco"],
            "decoração": ["casa", "decoração", "móvel", "organizador", "caixa", "espelho", "mesa"],
            "beleza": ["perfume", "makeup", "skincare", "maquiagem", "creme"],
            "infantil": ["brinquedo", "criança", "bebê", "boneca", "carrinho"]
        }
        
        tipo_encontrado = "produto"
        for tipo, palavras_tipo in tipos.items():
            for p in palavras_tipo:
                if p in produto_lower:
                    tipo_encontrado = tipo
                    break
            if tipo_encontrado != "produto":
                break
        
        return {
            "palavra": f"{termo_base} - {tipo_encontrado} 2026",
            "hashtags": [f"#{termo_base.replace(' ', '')}", f"#{tipo_encontrado}", "#2026", "#tendência"]
        }
    
    # 6. ÚLTIMO RECURSO
    nome_limpo = produto_lower
    for palavra in palavras_ignorar:
        nome_limpo = nome_limpo.replace(palavra, "").strip()
    
    if nome_limpo and len(nome_limpo) > 2:
        return {
            "palavra": f"{nome_limpo} - tendência 2026",
            "hashtags": [f"#{nome_limpo.replace(' ', '')}", "#tendência", "#2026"]
        }
    
    return {
        "palavra": f"{produto}",
        "hashtags": [f"#{produto.lower().replace(' ', '')}", "#tendência", "#2026"]
    }

# ============================================================
# CONSTANTES
# ============================================================
BUSCAS_DIARIAS = 3

# ============================================================
# FUNÇÕES DE CÁLCULO
# ============================================================
def calcular_score(produto: str, dados: Dict) -> int:
    """Calcula score para um produto"""
    score = 0
    
    if dados.get("pins", 0) > 2000:
        score += 3
    elif dados.get("pins", 0) > 1000:
        score += 2
    else:
        score += 1
    
    if dados.get("crescimento", 0) > 30:
        score += 2
    elif dados.get("crescimento", 0) > 15:
        score += 1
    
    if dados.get("views_tiktok", 0) > 3:
        score += 2
    elif dados.get("views_tiktok", 0) > 1:
        score += 1
    
    if dados.get("buscas_mes", 0) > 10000:
        score += 2
    elif dados.get("buscas_mes", 0) > 5000:
        score += 1
    
    if dados.get("variacao", 0) > 15:
        score += 1
    
    return max(1, min(score, 10))

def gerar_top10_produtos(forcar_atualizacao: bool = False) -> List[Dict]:
    """
    Gera top 10 produtos com dados dinâmicos.
    """
    dados_completos = obter_produtos_dinamicos(forcar_atualizacao=forcar_atualizacao)
    
    resultados = []
    for produto, dados in dados_completos.items():
        score = dados.get("score", calcular_score(produto, dados))
        
        if score >= 8:
            potencial = "🟢 Alto"
        elif score >= 5:
            potencial = "🟡 Médio"
        else:
            potencial = "🔴 Baixo"
        
        views_tiktok = dados.get('views_tiktok', 0)
        if isinstance(views_tiktok, float):
            views_tiktok = round(views_tiktok, 1)
        
        variacao = dados.get('variacao', 0)
        if isinstance(variacao, float):
            variacao = round(variacao, 1)
        
        dados_palavra = obter_palavra_chave(produto)
        palavra_chave = dados_palavra.get("palavra", f"{produto}")
        
        fonte_bruta = dados.get("fonte", "shopee")
        fonte_display = "Google" if fonte_bruta == "serper" else "Shopee"
        
        resultados.append({
            "Produto": produto.capitalize(),
            "Categoria": dados.get("categoria", "Geral"),
            "Evento": dados.get("evento", "Tendência"),
            "Fonte": fonte_display,
            "Potencial": potencial,
            "Score": score,
            "Pins": f"{dados.get('pins', 0):,}",
            "Crescimento": f"+{dados.get('crescimento', 0)}%",
            "Views TikTok": f"{views_tiktok}M",
            "Buscas no Mês": f"{dados.get('buscas_mes', 0):,}",
            "Resultados ML": f"{dados.get('resultados_ml', 0):,}",
            "Variação": f"+{variacao}%",
            "Tendência": dados.get('tendencia', '➡️ Estável'),
            "PalavraChave": palavra_chave
        })
    
    return sorted(resultados, key=lambda x: x["Score"], reverse=True)[:10]

def gerar_sugestoes_diarias(forcar_atualizacao: bool = False) -> List[Dict]:
    """Gera sugestões diárias (top 3)"""
    top10 = gerar_top10_produtos(forcar_atualizacao=forcar_atualizacao)
    return top10[:BUSCAS_DIARIAS]

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'carregar_apoiadores',
    'adicionar_apoiador',
    'remover_apoiador',
    'obter_dados_completos',
    'obter_palavra_chave',
    'PALAVRAS_CHAVE_CAUDA_LONGA',
    'calcular_score',
    'gerar_top10_produtos',
    'gerar_sugestoes_diarias',
    'BUSCAS_DIARIAS'
]
