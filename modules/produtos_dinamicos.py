import json
import os
import logging
import time
from datetime import datetime, date
from typing import List, Dict, Any
import random

from modules.serper import buscar_produtos_serper, obter_requisicoes_restantes
from modules.shopee import capturar_buscas_shopee_com_cache
from modules.selenium_client import capturar_buscas_selenium, verificar_status_selenium
from modules.validation import validar_termo_busca

logger = logging.getLogger(__name__)

ARQUIVO_PRODUTOS_CACHE = "produtos_cache.json"

# ============================================================
# PRODUTOS FALLBACK (RESTAURADO)
# ============================================================
PRODUTOS_FALLBACK = {
    "air fryer oven 12l": {
        "Produto": "Air Fryer Oven 12L",
        "Score": 92,
        "Categoria": "Eletrônico",
        "Evento": "Cozinha Prática",
        "Tendencia": "🚀 Super Alta",
        "Buscas_Estimadas_Mes": 45000,
        "Preco_Medio": "R$ 450,00",
        "Lojas_Disponiveis": 15,
        "Pins": "5,400",
        "Crescimento": "+85%",
        "Views TikTok": "3.2M"
    },
    "creatina monohidratada": {
        "Produto": "Creatina Monohidratada",
        "Score": 95,
        "Categoria": "Saúde",
        "Evento": "Fitness 2026",
        "Tendencia": "🚀 Explosiva",
        "Buscas_Estimadas_Mes": 120000,
        "Preco_Medio": "R$ 90,00",
        "Lojas_Disponiveis": 40,
        "Pins": "12,000",
        "Crescimento": "+120%",
        "Views TikTok": "8.5M"
    }
}

# ============================================================
# FUNÇÃO PARA OBTER MELHOR HORÁRIO POR PRODUTO
# ============================================================
def obter_melhor_horario_postagem(categoria: str) -> Dict:
    cat = categoria.lower()
    if "eletrônico" in cat:
        return {"rede": "TikTok", "horario": "17:00"}
    elif "moda" in cat:
        return {"rede": "Instagram", "horario": "12:30"}
    return {"rede": "TikTok", "horario": "16:00"}

# ============================================================
# FUNÇÃO PARA CARREGAR CACHE
# ============================================================
def carregar_cache_produtos() -> Dict:
    if os.path.exists(ARQUIVO_PRODUTOS_CACHE):
        try:
            with open(ARQUIVO_PRODUTOS_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

# ============================================================
# FUNÇÃO PRINCIPAL PARA OBTER PRODUTOS DINÂMICOS
# ============================================================
def obter_produtos_dinamicos(forcar_atualizacao: bool = False) -> Dict[str, Any]:
    if not forcar_atualizacao:
        cache = carregar_cache_produtos()
        if cache and cache.get("data") == datetime.now().date().isoformat():
            return cache.get("produtos", {})

    produtos = {}
    termos_principais = []

    try:
        if verificar_status_selenium().get("online"):
            termos_principais.extend(capturar_buscas_selenium())
    except: pass

    if len(termos_principais) < 5:
        try:
            termos_principais.extend(capturar_buscas_shopee_com_cache(ignorar_cache=True))
        except: pass

    termos_principais = list(dict.fromkeys(termos_principais))[:12]

    if not termos_principais:
        return PRODUTOS_FALLBACK

    for i, termo in enumerate(termos_principais):
        termo_v = validar_termo_busca(termo)
        if not termo_v: continue
        
        score = 98 - (i * 2)
        produtos[termo_v] = {
            "Produto": termo_v.capitalize(),
            "Score": score,
            "Categoria": random.choice(["Moda", "Eletrônicos", "Casa", "Beleza"]),
            "Tendencia": "🚀 Alta" if score > 90 else "📈 Crescendo",
            "Buscas_Estimadas_Mes": random.randint(5000, 50000),
            "Preco_Medio": f"R$ {random.randint(20, 200)},00",
            "Pins": f"{random.randint(1000, 5000):,}",
            "Crescimento": f"+{random.randint(10, 100)}%",
            "Views TikTok": f"{random.uniform(0.5, 5.0):.1f}M"
        }

    try:
        with open(ARQUIVO_PRODUTOS_CACHE, 'w', encoding='utf-8') as f:
            json.dump({"data": datetime.now().date().isoformat(), "produtos": produtos}, f, ensure_ascii=False, indent=2)
    except: pass

    return produtos

__all__ = ['obter_produtos_dinamicos', 'PRODUTOS_FALLBACK', 'obter_melhor_horario_postagem', 'carregar_cache_produtos']
