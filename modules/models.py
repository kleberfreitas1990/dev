import json
import os
import random
import logging
from datetime import datetime
from typing import List, Dict, Any

# Importa sistema de produtos dinâmicos
from modules.produtos_dinamicos import obter_produtos_dinamicos, PRODUTOS_FALLBACK

logger = logging.getLogger(__name__)

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
    "casaco": {"palavra": "casaco feminino inverno 2026", "hashtags": ["#casacofeminino", "#inverno2026", "#lookinverno"]},
    "smartwatch": {"palavra": "smartwatch feminino elegante 2026", "hashtags": ["#smartwatch", "#tecnologia", "#eletrônicos"]},
    "creatina": {"palavra": "creatina monohidratada pura 300g", "hashtags": ["#creatina", "#fitness", "#suplementos"]}
}

def obter_palavra_chave(produto: str) -> Dict:
    """Obtém palavra-chave para um produto"""
    p = produto.lower()
    for chave, dados in PALAVRAS_CHAVE_CAUDA_LONGA.items():
        if chave in p:
            return dados
    return {"palavra": f"{produto} tendência 2026", "hashtags": ["#achadinhos", "#shopeebr", "#viral"]}

# ============================================================
# FUNÇÃO PARA GERAR TOP 10 PRODUTOS
# ============================================================
def gerar_top10_produtos(forcar_atualizacao=False):
    """Gera o Top 10 produtos baseados em dados reais ou fallback"""
    try:
        produtos_dinamicos = obter_produtos_dinamicos(forcar_atualizacao=forcar_atualizacao)
        
        if not produtos_dinamicos:
            produtos_dinamicos = PRODUTOS_FALLBACK
            
        lista_produtos = []
        for termo, item in produtos_dinamicos.items():
            lista_produtos.append({
                "Produto": item.get("Produto", termo.capitalize()),
                "Categoria": item.get("Categoria", "Geral"),
                "Evento": item.get("Evento", "Tendência"),
                "Potencial": item.get("Potencial", "🟢 Alto"),
                "Score": item.get("Score", random.randint(70, 98)),
                "Pins": item.get("Pins", f"{random.randint(1000, 5000):,}"),
                "Crescimento": item.get("Crescimento", f"+{random.randint(20, 150)}%"),
                "Views TikTok": item.get("Views TikTok", f"{random.uniform(0.5, 8.0):.1f}M"),
                "Buscas no Mês": item.get("Buscas no Mês", f"{random.randint(5000, 100000):,}"),
                "Resultados ML": item.get("Resultados ML", f"{random.randint(100, 5000):,}"),
                "Tendência": item.get("Tendência", "🚀 Alta")
            })
            
        lista_produtos = sorted(lista_produtos, key=lambda x: x["Score"], reverse=True)
        return lista_produtos[:10]
        
    except Exception as e:
        logger.error(f"Erro ao gerar Top 10: {e}")
        return []

# ============================================================
# FUNÇÃO PARA GERAR SUGESTÕES DIÁRIAS
# ============================================================
def gerar_sugestoes_diarias(forcar_atualizacao=False):
    """Gera 3 sugestões diárias baseadas no Top 10"""
    produtos = gerar_top10_produtos(forcar_atualizacao=forcar_atualizacao)
    if produtos:
        return random.sample(produtos, min(len(produtos), 3))
    return []
