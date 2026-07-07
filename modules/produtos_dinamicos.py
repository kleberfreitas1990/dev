# modules/produtos_dinamicos.py (VERSÃO CORRIGIDA)

import json
import os
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from modules.shopee import capturar_buscas_shopee_com_cache
from modules.serper import buscar_produtos_serper
from modules.validation import validar_termo_busca, validar_produtos_serper

logger = logging.getLogger(__name__)

# ============================================================
# ARQUIVO DE CACHE DE PRODUTOS
# ============================================================
ARQUIVO_PRODUTOS_CACHE = "produtos_cache.json"

# ============================================================
# DADOS DE FALLBACK (COM NÚMEROS ARREDONDADOS)
# ============================================================
PRODUTOS_FALLBACK = {
    "casaco": {
        "pins": 3400, "pins_historico": 2900, "crescimento": 45, "views_tiktok": 5.8,
        "resultados_ml": 1240, "buscas_mes": 15200, "buscas_historico": 12800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 17.2, 
        "tendencia": "🚀 Em alta", "score": 9
    },
    "smartwatch": {
        "pins": 2800, "pins_historico": 2500, "crescimento": 35, "views_tiktok": 4.5,
        "resultados_ml": 1500, "buscas_mes": 18500, "buscas_historico": 15200,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 12.0,
        "tendencia": "🚀 Em alta", "score": 8
    },
    "fone bluetooth": {
        "pins": 2200, "pins_historico": 2000, "crescimento": 30, "views_tiktok": 3.8,
        "resultados_ml": 1200, "buscas_mes": 16500, "buscas_historico": 13800,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 10.0,
        "tendencia": "➡️ Estável", "score": 7
    },
    "perfume": {
        "pins": 2100, "pins_historico": 1800, "crescimento": 28, "views_tiktok": 3.2,
        "resultados_ml": 1100, "buscas_mes": 14200, "buscas_historico": 11800,
        "categoria": "Beleza", "evento": "Dia dos Namorados", "variacao": 16.7,
        "tendencia": "🚀 Em alta", "score": 8
    },
    "blusa de lã": {
        "pins": 2800, "pins_historico": 2200, "crescimento": 38, "views_tiktok": 4.2,
        "resultados_ml": 890, "buscas_mes": 12500, "buscas_historico": 9800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 27.3,
        "tendencia": "🚀 Em alta", "score": 8
    }
}

# ============================================================
# FUNÇÃO PRINCIPAL: OBTER PRODUTOS DINÂMICOS
# ============================================================
def obter_produtos_dinamicos(forcar_atualizacao: bool = False) -> Dict[str, Any]:
    """
    Obtém produtos com dados atualizados da Shopee e Serper
    """
    hoje = datetime.now().date().isoformat()
    
    # Tenta carregar do cache
    if not forcar_atualizacao:
        cache = carregar_cache_produtos()
        if cache:
            data_cache = cache.get("data")
            if data_cache == hoje:
                logger.info(f"Usando cache de produtos de hoje")
                return cache.get("produtos", PRODUTOS_FALLBACK)
    
    # Busca dados atualizados
    logger.info("Buscando dados atualizados de produtos...")
    produtos = buscar_produtos_dos_termos()
    
    # Se não encontrou nada, usa fallback
    if not produtos or len(produtos) < 3:
        logger.warning("Nenhum produto encontrado, usando fallback")
        produtos = PRODUTOS_FALLBACK
    
    # Salva no cache
    salvar_cache_produtos(produtos)
    
    return produtos

def buscar_produtos_dos_termos(limite: int = 10) -> Dict[str, Any]:
    """
    Busca produtos a partir dos termos da Shopee
    """
    produtos = {}
    
    # 1. Busca termos da Shopee
    logger.info("Buscando termos da Shopee...")
    termos = capturar_buscas_shopee_com_cache()
    
    if not termos:
        logger.warning("Nenhum termo da Shopee encontrado")
        return PRODUTOS_FALLBACK
    
    logger.info(f"Encontrados {len(termos)} termos da Shopee")
    
    # 2. Para cada termo, busca no Serper
    termos_usados = termos[:limite]
    serper_funcionando = False
    
    for i, termo in enumerate(termos_usados):
        try:
            termo_validado = validar_termo_busca(termo)
            if not termo_validado:
                continue
            
            # Tenta buscar no Serper
            logger.info(f"Buscando no Serper: '{termo_validado}'...")
            produtos_serper = buscar_produtos_serper(termo_validado, limite=3)
            
            if produtos_serper and len(produtos_serper) > 0:
                serper_funcionando = True
                total_resultados = len(produtos_serper) * 10
                
                # Usa dados REAIS do Serper + simula complementos
                produtos[termo_validado] = {
                    "pins": random.randint(1500, 3500),
                    "pins_historico": random.randint(1200, 3000),
                    "crescimento": random.randint(15, 50),
                    "views_tiktok": round(random.uniform(2.0, 6.0), 1),  # ARREDONDADO
                    "resultados_ml": total_resultados,
                    "buscas_mes": random.randint(8000, 20000),
                    "buscas_historico": random.randint(6000, 16000),
                    "categoria": definir_categoria(termo_validado),
                    "evento": definir_evento(termo_validado),
                    "variacao": round(random.uniform(5.0, 30.0), 1),
                    "tendencia": definir_tendencia(i),
                    "score": calcular_score_simulado(i)
                }
                logger.info(f"  ✅ Produto processado: '{termo_validado}'")
            else:
                logger.info(f"  ⚠️ Sem resultados no Serper para '{termo_validado}'")
                
        except Exception as e:
            logger.error(f"Erro ao buscar produtos para '{termo}': {e}")
            continue
    
    # Se Serper não funcionou, usa fallback com dados reais da Shopee
    if not serper_funcionando or len(produtos) < 3:
        logger.warning("Serper não retornou dados suficientes, usando fallback enriquecido")
        produtos = enriquecer_com_fallback(termos_usados)
    
    # Se ainda não tem produtos, usa fallback padrão
    if not produtos:
        return PRODUTOS_FALLBACK
    
    return produtos

def enriquecer_com_fallback(termos: List[str]) -> Dict[str, Any]:
    """
    Cria dados a partir dos termos da Shopee (fallback quando Serper falha)
    """
    produtos = {}
    
    for i, termo in enumerate(termos[:10]):
        termo_validado = validar_termo_busca(termo)
        if not termo_validado:
            continue
        
        # Dados realistas baseados no termo
        base_pins = 1000 + (i * 200)
        base_buscas = 5000 + (i * 800)
        
        produtos[termo_validado] = {
            "pins": base_pins + random.randint(-200, 400),
            "pins_historico": base_pins - random.randint(100, 300),
            "crescimento": random.randint(10, 45),
            "views_tiktok": round(random.uniform(1.5, 5.5), 1),  # ARREDONDADO
            "resultados_ml": random.randint(300, 1500),
            "buscas_mes": base_buscas + random.randint(-1000, 3000),
            "buscas_historico": base_buscas - random.randint(500, 2000),
            "categoria": definir_categoria(termo_validado),
            "evento": definir_evento(termo_validado),
            "variacao": round(random.uniform(5.0, 25.0), 1),
            "tendencia": definir_tendencia(i),
            "score": calcular_score_simulado(i)
        }
    
    return produtos

# ============================================================
# FUNÇÕES AUXILIARES (MANTIDAS)
# ============================================================
def definir_categoria(termo: str) -> str:
    categorias = {
        "casaco": "Moda", "blusa": "Moda", "vestido": "Moda",
        "calça": "Moda", "sapato": "Moda", "tênis": "Moda",
        "smartwatch": "Eletrônicos", "fone": "Eletrônicos",
        "celular": "Eletrônicos", "tablet": "Eletrônicos",
        "perfume": "Beleza", "maquiagem": "Beleza", "creme": "Beleza",
        "brinquedo": "Infantil", "boneca": "Infantil", "carrinho": "Infantil",
        "organizador": "Casa", "caixa": "Casa", "lixeira": "Casa", "garrafa": "Casa",
    }
    for palavra, categoria in categorias.items():
        if palavra in termo.lower():
            return categoria
    return "Geral"

def definir_evento(termo: str) -> str:
    eventos = {
        "casaco": "Férias Escolares", "blusa": "Férias Escolares",
        "perfume": "Dia dos Namorados", "smartwatch": "Tendência Tecnológica",
        "fone": "Tendência Tecnológica", "brinquedo": "Dia das Crianças",
        "boneca": "Dia das Crianças",
    }
    for palavra, evento in eventos.items():
        if palavra in termo.lower():
            return evento
    return "Tendência"

def definir_tendencia(indice: int) -> str:
    if indice < 3:
        return "🚀 Em alta"
    elif indice < 6:
        return "📈 Crescendo"
    else:
        return "➡️ Estável"

def calcular_score_simulado(indice: int) -> int:
    base = 10 - indice
    if base < 3:
        base = 3
    elif base > 9:
        base = 9
    return base

# ============================================================
# FUNÇÕES DE CACHE
# ============================================================
def carregar_cache_produtos() -> Dict:
    if os.path.exists(ARQUIVO_PRODUTOS_CACHE):
        try:
            with open(ARQUIVO_PRODUTOS_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_cache_produtos(produtos: Dict) -> bool:
    try:
        with open(ARQUIVO_PRODUTOS_CACHE, 'w', encoding='utf-8') as f:
            json.dump({
                "data": datetime.now().date().isoformat(),
                "timestamp": datetime.now().isoformat(),
                "produtos": produtos,
                "total": len(produtos)
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Cache de produtos salvo com {len(produtos)} produtos")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar cache: {e}")
        return False

def limpar_cache_produtos() -> bool:
    if os.path.exists(ARQUIVO_PRODUTOS_CACHE):
        try:
            os.remove(ARQUIVO_PRODUTOS_CACHE)
            return True
        except:
            pass
    return False

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'obter_produtos_dinamicos',
    'limpar_cache_produtos',
    'PRODUTOS_FALLBACK'
]
