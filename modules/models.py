import json
import os
from datetime import datetime

# ============================================================
# ARQUIVOS DE DADOS
# ============================================================
ARQUIVO_APOIADORES = "apoiadores.json"

# ============================================================
# FUNÇÕES DE APOIADORES
# ============================================================
def carregar_apoiadores():
    """Carrega a lista de apoiadores do arquivo"""
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
# DADOS DE PRODUTOS
# ============================================================
DADOS_COMPLETOS = {
    "casaco": {
        "pins": 3400, "pins_historico": 2900, "crescimento": 45, "views_tiktok": 5.8,
        "resultados_ml": 1240, "buscas_mes": 15200, "buscas_historico": 12800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 17.2, "tendencia": "🚀 Em alta"
    },
    "blusa de lã": {
        "pins": 2800, "pins_historico": 2200, "crescimento": 38, "views_tiktok": 4.2,
        "resultados_ml": 890, "buscas_mes": 12500, "buscas_historico": 9800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 27.3, "tendencia": "🚀 Em alta"
    },
    "smartwatch": {
        "pins": 2800, "pins_historico": 2500, "crescimento": 35, "views_tiktok": 4.5,
        "resultados_ml": 1500, "buscas_mes": 18500, "buscas_historico": 15200,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 12.0, "tendencia": "🚀 Em alta"
    },
    "fone bluetooth": {
        "pins": 2200, "pins_historico": 2000, "crescimento": 30, "views_tiktok": 3.8,
        "resultados_ml": 1200, "buscas_mes": 16500, "buscas_historico": 13800,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 10.0, "tendencia": "➡️ Estável"
    },
    "perfume": {
        "pins": 2100, "pins_historico": 1800, "crescimento": 28, "views_tiktok": 3.2,
        "resultados_ml": 1100, "buscas_mes": 14200, "buscas_historico": 11800,
        "categoria": "Beleza", "evento": "Dia dos Namorados", "variacao": 16.7, "tendencia": "🚀 Em alta"
    }
}

PALAVRAS_CHAVE_CAUDA_LONGA = {
    "casaco": {"palavra": "casaco feminino inverno 2026", "hashtags": ["#casacofeminino", "#inverno2026", "#lookinverno"]},
    "blusa de lã": {"palavra": "blusa de lã feminina elegante", "hashtags": ["#blusadelã", "#modainverno", "#lookelegante"]},
    "smartwatch": {"palavra": "smartwatch feminino elegante", "hashtags": ["#smartwatch", "#tecnologia", "#eletrônicos"]},
    "fone bluetooth": {"palavra": "fone bluetooth JBL original", "hashtags": ["#fonebluetooth", "#áudio", "#tecnologia"]},
    "perfume": {"palavra": "perfume importado feminino", "hashtags": ["#perfumeimportado", "#belezafeminina", "#presentes"]}
}

BUSCAS_DIARIAS = 3

def calcular_score(produto, dados):
    score = 0
    if dados.get("pins", 0) > 2000: score += 3
    elif dados.get("pins", 0) > 1000: score += 2
    else: score += 1
    
    if dados.get("crescimento", 0) > 30: score += 2
    elif dados.get("crescimento", 0) > 15: score += 1
    
    if dados.get("views_tiktok", 0) > 3: score += 2
    elif dados.get("views_tiktok", 0) > 1: score += 1
    
    if dados.get("buscas_mes", 0) > 10000: score += 2
    elif dados.get("buscas_mes", 0) > 5000: score += 1
    
    if dados.get("variacao", 0) > 15: score += 1
    
    return min(score, 10)

def gerar_top10_produtos():
    resultados = []
    for produto, dados in DADOS_COMPLETOS.items():
        score = calcular_score(produto, dados)
        
        if score >= 8: potencial = "🟢 Alto"
        elif score >= 5: potencial = "🟡 Médio"
        else: potencial = "🔴 Baixo"
        
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
    
    return sorted(resultados, key=lambda x: x["Score"], reverse=True)[:10]

def gerar_sugestoes_diarias():
    return gerar_top10_produtos()[:BUSCAS_DIARIAS]
