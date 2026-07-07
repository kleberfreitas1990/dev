# modules/models.py

import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Importa sistema de produtos dinâmicos
from modules.produtos_dinamicos import obter_produtos_dinamicos, PRODUTOS_FALLBACK

# ============================================================
# ARQUIVOS DE DADOS (NA RAIZ)
# ============================================================
ARQUIVO_APOIADORES = "apoiadores.json"  # <-- NA RAIZ

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
def obter_dados_completos(forcar_atualizacao: bool = False) -> Dict:
    """
    Obtém dados completos de produtos (dinâmicos)
    
    Args:
        forcar_atualizacao (bool): Força atualização
        
    Returns:
        Dict: Dados completos dos produtos
    """
    return obter_produtos_dinamicos(forcar_atualizacao)

# ============================================================
# PALAVRAS CHAVE
# ============================================================
PALAVRAS_CHAVE_CAUDA_LONGA = {
    "casaco": {"palavra": "casaco feminino inverno 2026", "hashtags": ["#casacofeminino", "#inverno2026", "#lookinverno"]},
    "blusa de lã": {"palavra": "blusa de lã feminina elegante", "hashtags": ["#blusadelã", "#modainverno", "#lookelegante"]},
    "smartwatch": {"palavra": "smartwatch feminino elegante", "hashtags": ["#smartwatch", "#tecnologia", "#eletrônicos"]},
    "fone bluetooth": {"palavra": "fone bluetooth JBL original", "hashtags": ["#fonebluetooth", "#áudio", "#tecnologia"]},
    "perfume": {"palavra": "perfume importado feminino", "hashtags": ["#perfumeimportado", "#belezafeminina", "#presentes"]}
}

def obter_palavra_chave(produto: str) -> Dict:
    """Obtém palavra-chave para um produto"""
    produto_lower = produto.lower()
    for chave, dados in PALAVRAS_CHAVE_CAUDA_LONGA.items():
        if chave in produto_lower:
            return dados
    return {
        "palavra": f"{produto} tendência 2026",
        "hashtags": ["#tendência", "#moda", "#2026"]
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
    
    # Score mínimo 1, máximo 10
    return max(1, min(score, 10))

def gerar_top10_produtos(forcar_atualizacao: bool = False) -> List[Dict]:
    """Gera top 10 produtos com dados dinâmicos"""
    dados_completos = obter_dados_completos(forcar_atualizacao)
    
    resultados = []
    for produto, dados in dados_completos.items():
        score = dados.get("score", calcular_score(produto, dados))
        
        if score >= 8:
            potencial = "🟢 Alto"
        elif score >= 5:
            potencial = "🟡 Médio"
        else:
            potencial = "🔴 Baixo"
        
        resultados.append({
            "Produto": produto.capitalize(),
            "Categoria": dados.get("categoria", "Geral"),
            "Evento": dados.get("evento", "Tendência"),
            "Potencial": potencial,
            "Score": score,
            "Pins": f"{dados.get('pins', 0):,}",
            "Crescimento": f"+{dados.get('crescimento', 0)}%",
            "Views TikTok": f"{dados.get('views_tiktok', 0)}M",
            "Buscas no Mês": f"{dados.get('buscas_mes', 0):,}",
            "Resultados ML": f"{dados.get('resultados_ml', 0):,}",
            "Variação": f"+{dados.get('variacao', 0):.1f}%",
            "Tendência": dados.get('tendencia', '➡️ Estável')
        })
    
    # Ordena por score e retorna top 10
    return sorted(resultados, key=lambda x: x["Score"], reverse=True)[:10]

def gerar_sugestoes_diarias(forcar_atualizacao: bool = False) -> List[Dict]:
    """Gera sugestões diárias (top 3)"""
    top10 = gerar_top10_produtos(forcar_atualizacao)
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
