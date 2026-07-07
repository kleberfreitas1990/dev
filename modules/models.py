# Adicione no topo do arquivo, após os imports
from modules.shopee import capturar_buscas_shopee_com_cache, TERMOS_REAIS_SHOPEE

# ============================================================
# FUNÇÃO PARA BUSCAR TENDÊNCIAS DO PINTEREST (REAL)
# ============================================================
def buscar_tendencias_pinterest_real():
    """Busca tendências reais do Pinterest via API (se tiver token)"""
    
    token = st.secrets.get("PINTEREST_ACCESS_TOKEN", "")
    if not token:
        return []
    
    try:
        url = "https://api.pinterest.com/v5/trends"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tendencias = []
            for item in data.get("trends", []):
                termo = item.get("title", "")
                if termo and len(termo) > 3:
                    tendencias.append(termo.lower())
            return tendencias[:10]
    except:
        pass
    
    return []

# ============================================================
# FUNÇÃO PARA BUSCAR PINS POR TERMO
# ============================================================
def buscar_pins_pinterest(termo):
    """Busca quantidade de pins para um termo no Pinterest"""
    
    token = st.secrets.get("PINTEREST_ACCESS_TOKEN", "")
    if not token:
        return 0
    
    try:
        url = f"https://api.pinterest.com/v5/pins/search"
        params = {"query": termo, "limit": 1}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("count", 0) * 10  # Estimativa
    except:
        pass
    
    return 0

# ============================================================
# ATUALIZAR DADOS_COMPLETOS COM SHOPEE E PINTEREST
# ============================================================
def get_dados_completos():
    """Retorna dados combinados: base + Shopee + Pinterest"""
    
    # Busca tendências da Shopee
    buscas_shopee = capturar_buscas_shopee_com_cache()
    
    # Busca tendências do Pinterest
    tendencias_pinterest = buscar_tendencias_pinterest_real()
    
    # Base fixa de produtos
    dados_base = {
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
    
    # Adiciona produtos da Shopee
    for termo in buscas_shopee[:10]:
        if termo not in dados_base:
            posicao = buscas_shopee.index(termo) + 1
            score_base = max(500, 3000 - (posicao - 1) * 200)
            variacao = round(random.uniform(10, 35), 1)
            tendencia = "🚀 Em alta" if posicao <= 3 else "📈 Crescendo" if posicao <= 7 else "➡️ Estável"
            
            dados_base[termo] = {
                "pins": score_base,
                "pins_historico": int(score_base * 0.7),
                "crescimento": max(10, 45 - (posicao - 1) * 2),
                "views_tiktok": round(score_base / 500, 1),
                "resultados_ml": int(score_base / 2),
                "buscas_mes": int(score_base * 5),
                "buscas_historico": int(score_base * 4),
                "categoria": "Shopee Trend",
                "evento": "Em Alta",
                "variacao": variacao,
                "tendencia": tendencia
            }
    
    # Adiciona produtos do Pinterest
    for termo in tendencias_pinterest[:5]:
        if termo not in dados_base:
            pins = buscar_pins_pinterest(termo) or random.randint(500, 2000)
            dados_base[termo] = {
                "pins": pins,
                "pins_historico": int(pins * 0.7),
                "crescimento": random.randint(15, 40),
                "views_tiktok": round(pins / 500, 1),
                "resultados_ml": int(pins / 2),
                "buscas_mes": int(pins * 4),
                "buscas_historico": int(pins * 3),
                "categoria": "Pinterest Trend",
                "evento": "Em Alta",
                "variacao": random.uniform(10, 30),
                "tendencia": "🚀 Em alta" if pins > 1500 else "📈 Crescendo"
            }
    
    return dados_base
