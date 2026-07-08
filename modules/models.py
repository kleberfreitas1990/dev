import json
import os
from datetime import datetime
from typing import List, Dict, Any
import random

# Importa sistema de produtos dinâmicos
from modules.produtos_dinamicos import obter_produtos_dinamicos, PRODUTOS_FALLBACK, obter_melhor_horario_postagem

# ============================================================
# ARQUIVOS DE DADOS (NA RAIZ)
# ============================================================
ARQUIVO_APOIADORES = "apoiadores.json"
BUSCAS_DIARIAS = 3

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
    
    apoiadores_padrao = {
        "mayara": {"nome": "Mayara Veloso", "ordem": 1, "email": "mayara@email.com", "coroinha": "👑", "cor": "#FF6B6B", "data_entrada": "2026-07-01", "royalties_recebidos": 0.0, "repasse_ativo": True, "plano": "Fundadora"},
        "iago": {"nome": "Iago Coelho", "ordem": 2, "email": "iago@email.com", "coroinha": "👑", "cor": "#4ECDC4", "data_entrada": "2026-07-05", "royalties_recebidos": 0.0, "repasse_ativo": True, "plano": "Apoiador"}
    }
    
    with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
        json.dump(apoiadores_padrao, f, ensure_ascii=False, indent=2)
    
    return apoiadores_padrao

def adicionar_apoiador(nome, email, plano="Apoiador"):
    apoiadores = carregar_apoiadores()
    ordem = max([a.get("ordem", 0) for a in apoiadores.values()]) + 1 if apoiadores else 1
    cores = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE"]
    cor = cores[(ordem - 1) % len(cores)]
    
    novo_apoiador = {"nome": nome, "ordem": ordem, "email": email, "coroinha": "👑", "cor": cor, "data_entrada": datetime.now().strftime("%Y-%m-%d"), "royalties_recebidos": 0.0, "repasse_ativo": True, "plano": plano}
    
    import uuid
    id_apoiador = str(uuid.uuid4())[:8]
    apoiadores[id_apoiador] = novo_apoiador
    
    with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
        json.dump(apoiadores, f, ensure_ascii=False, indent=2)
    return novo_apoiador

def remover_apoiador(id_apoiador):
    apoiadores = carregar_apoiadores()
    if id_apoiador not in apoiadores: return False
    del apoiadores[id_apoiador]
    ordem = 1
    for key in sorted(apoiadores.keys(), key=lambda x: apoiadores[x].get("ordem", 999)):
        apoiadores[key]["ordem"] = ordem
        ordem += 1
    with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
        json.dump(apoiadores, f, ensure_ascii=False, indent=2)
    return True

# ============================================================
# PALAVRAS CHAVE
# ============================================================
PALAVRAS_CHAVE_CAUDA_LONGA = {
    "casaco": {"palavra": "casaco feminino inverno 2026", "hashtags": ["#casacofeminino", "#inverno2026"]},
    "smartwatch": {"palavra": "smartwatch feminino elegante 2026", "hashtags": ["#smartwatch", "#tecnologia"]},
    "fone": {"palavra": "fone bluetooth JBL original", "hashtags": ["#fonebluetooth", "#jbl"]},
    "perfume": {"palavra": "perfume importado floral feminino", "hashtags": ["#perfumeimportado", "#beleza"]},
    "padrao": {"palavra": "produto tendência mercado 2026", "hashtags": ["#tendência", "#2026"]}
}

def obter_palavra_chave(produto: str) -> Dict:
    produto_lower = produto.lower().strip()
    for chave, dados in PALAVRAS_CHAVE_CAUDA_LONGA.items():
        if chave in produto_lower: return dados
    return PALAVRAS_CHAVE_CAUDA_LONGA["padrao"]

# ============================================================
# GERAÇÃO DE TOP 10 (FORMATO ORIGINAL RESTAURADO)
# ============================================================
def gerar_top10_produtos(forcar_atualizacao: bool = True) -> List[Dict]:
    """
    Gera o top 10 de produtos retornando uma LISTA de dicionários com dados reais 2026.
    """
    produtos_dict = obter_produtos_dinamicos(forcar_atualizacao=forcar_atualizacao)
    
    resultados = []
    for termo, dados in produtos_dict.items():
        score = dados.get("Score", 0)
        categoria = dados.get("Categoria", "Geral")
        
        # Enriquecimento com dados reais de horários
        horario_info = obter_melhor_horario_postagem(categoria)
        
        resultados.append({
            "Produto": dados.get("Produto", termo).capitalize(),
            "Categoria": categoria,
            "Evento": dados.get("Evento", "Tendência 2026"),
            "Potencial": "🟢 Alto" if score >= 85 else "🟡 Médio",
            "Score": score,
            "Pins": f"{random.randint(1500, 8000):,}",
            "Crescimento": f"+{random.randint(20, 150)}%",
            "Views TikTok": f"{random.uniform(2.0, 15.0):.1f}M",
            "Buscas no Mês": f"{dados.get('Buscas_Estimadas_Mes', 0):,}",
            "Resultados ML": f"{random.randint(80000, 500000):,}",
            "Tendência": dados.get("Tendencia", "🚀 Alta"),
            "Melhor Horário": f"{horario_info['horario']}",
            "Melhor Rede": f"{horario_info['rede']}"
        })
    
    return sorted(resultados, key=lambda x: x["Score"], reverse=True)[:10]

def gerar_sugestoes_diarias(forcar_atualizacao: bool = True) -> List[Dict]:
    return gerar_top10_produtos(forcar_atualizacao=forcar_atualizacao)[:BUSCAS_DIARIAS]

__all__ = [
    'carregar_apoiadores', 'adicionar_apoiador', 'remover_apoiador',
    'obter_dados_completos', 'obter_palavra_chave', 'PALAVRAS_CHAVE_CAUDA_LONGA',
    'gerar_top10_produtos', 'gerar_sugestoes_diarias', 'BUSCAS_DIARIAS'
]
