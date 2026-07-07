# modules/produtos_dinamicos.py

import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from modules.shopee import capturar_buscas_shopee_com_cache
from modules.serper import buscar_produtos_serper
from modules.validation import validar_termo_busca, validar_produtos_serper

logger = logging.getLogger(__name__)

# ============================================================
# ARQUIVO DE CACHE DE PRODUTOS (NA RAIZ)
# ============================================================
ARQUIVO_PRODUTOS_CACHE = "produtos_cache.json"  # <-- NA RAIZ

# ============================================================
# DADOS DE FALLBACK (usados se não houver dados reais)
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
    
    Args:
        forcar_atualizacao (bool): Força atualização mesmo com cache
        
    Returns:
        Dict: Dicionário de produtos com dados
    """
    hoje = datetime.now().date().isoformat()
    
    # Tenta carregar do cache
    if not forcar_atualizacao:
        cache = carregar_cache_produtos()
        if cache:
            data_cache = cache.get("data")
            
            # Se o cache é de hoje, usa
            if data_cache == hoje:
                logger.info(f"Usando cache de produtos de hoje ({len(cache.get('produtos', {}))} produtos)")
                return cache.get("produtos", PRODUTOS_FALLBACK)
            
            # Se o cache tem menos de 24h, ainda pode usar
            try:
                data_cache_dt = datetime.strptime(data_cache, "%Y-%m-%d").date()
                if (datetime.now().date() - data_cache_dt).days < 1:
                    logger.info(f"Usando cache de {data_cache} (menos de 24h)")
                    return cache.get("produtos", PRODUTOS_FALLBACK)
            except:
                pass
    
    # Busca dados atualizados
    logger.info("Buscando dados atualizados de produtos...")
    produtos = buscar_produtos_dos_termos()
    
    # Se não encontrou nada, usa fallback
    if not produtos:
        logger.warning("Nenhum produto encontrado, usando fallback")
        produtos = PRODUTOS_FALLBACK
    
    # Salva no cache
    salvar_cache_produtos(produtos)
    
    return produtos

def buscar_produtos_dos_termos(limite: int = 10) -> Dict[str, Any]:
    """
    Busca produtos a partir dos termos da Shopee
    
    Args:
        limite (int): Número máximo de produtos
        
    Returns:
        Dict: Dicionário de produtos
    """
    produtos = {}
    
    # 1. Busca termos da Shopee
    termos = capturar_buscas_shopee_com_cache()
    
    if not termos:
        logger.warning("Nenhum termo da Shopee encontrado")
        return PRODUTOS_FALLBACK
    
    # 2. Para cada termo, busca no Serper (ou usa dados simulados)
    termos_usados = termos[:limite]
    
    for i, termo in enumerate(termos_usados):
        try:
            termo_validado = validar_termo_busca(termo)
            if not termo_validado:
                continue
            
            # Busca produtos no Serper
            produtos_serper = buscar_produtos_serper(termo_validado, limite=3)
            
            if produtos_serper:
                # Extrai informações do Serper
                total_resultados = len(produtos_serper) * 10
                
                # Simula dados com base nos resultados
                produtos[termo_validado] = {
                    "pins": 1500 + (i * 300),
                    "pins_historico": 1200 + (i * 250),
                    "crescimento": 20 + (i * 3),
                    "views_tiktok": 2.5 + (i * 0.4),
                    "resultados_ml": total_resultados,
                    "buscas_mes": 8000 + (i * 1000),
                    "buscas_historico": 6000 + (i * 800),
                    "categoria": definir_categoria(termo_validado),
                    "evento": definir_evento(termo_validado),
                    "variacao": 10 + (i * 2),
                    "tendencia": definir_tendencia(i),
                    "score": calcular_score_simulado(i)
                }
            else:
                # Fallback: usa dados padrão com variação
                produtos[termo_validado] = gerar_dados_fallback(termo_validado, i)
                
        except Exception as e:
            logger.error(f"Erro ao buscar produtos para '{termo}': {e}")
            continue
    
    # Se não encontrou produtos, usa fallback
    if not produtos:
        return PRODUTOS_FALLBACK
    
    return produtos

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def definir_categoria(termo: str) -> str:
    """Define categoria com base no termo"""
    categorias = {
        "casaco": "Moda",
        "blusa": "Moda",
        "vestido": "Moda",
        "calça": "Moda",
        "sapato": "Moda",
        "tênis": "Moda",
        "smartwatch": "Eletrônicos",
        "fone": "Eletrônicos",
        "celular": "Eletrônicos",
        "tablet": "Eletrônicos",
        "perfume": "Beleza",
        "maquiagem": "Beleza",
        "creme": "Beleza",
        "brinquedo": "Infantil",
        "boneca": "Infantil",
        "carrinho": "Infantil",
        "organizador": "Casa",
        "caixa": "Casa",
        "lixeira": "Casa",
        "garrafa": "Casa",
    }
    
    for palavra, categoria in categorias.items():
        if palavra in termo.lower():
            return categoria
    
    return "Geral"

def definir_evento(termo: str) -> str:
    """Define evento com base no termo"""
    eventos = {
        "casaco": "Férias Escolares",
        "blusa": "Férias Escolares",
        "perfume": "Dia dos Namorados",
        "smartwatch": "Tendência Tecnológica",
        "fone": "Tendência Tecnológica",
        "brinquedo": "Dia das Crianças",
        "boneca": "Dia das Crianças",
    }
    
    for palavra, evento in eventos.items():
        if palavra in termo.lower():
            return evento
    
    return "Tendência"

def definir_tendencia(indice: int) -> str:
    """Define tendência com base no índice"""
    if indice < 3:
        return "🚀 Em alta"
    elif indice < 6:
        return "📈 Crescendo"
    else:
        return "➡️ Estável"

def calcular_score_simulado(indice: int) -> int:
    """Calcula score simulado"""
    base = 10 - indice
    if base < 3:
        base = 3
    elif base > 9:
        base = 9
    return base

def gerar_dados_fallback(termo: str, indice: int) -> Dict:
    """Gera dados fallback para um termo"""
    return {
        "pins": 1000 + (indice * 200),
        "pins_historico": 800 + (indice * 150),
        "crescimento": 15 + (indice * 2),
        "views_tiktok": 2.0 + (indice * 0.3),
        "resultados_ml": 500 + (indice * 100),
        "buscas_mes": 5000 + (indice * 500),
        "buscas_historico": 4000 + (indice * 400),
        "categoria": definir_categoria(termo),
        "evento": definir_evento(termo),
        "variacao": 8 + (indice * 1.5),
        "tendencia": definir_tendencia(indice),
        "score": calcular_score_simulado(indice)
    }

# ============================================================
# FUNÇÕES DE CACHE (NA RAIZ)
# ============================================================
def carregar_cache_produtos() -> Dict:
    """Carrega cache de produtos da raiz"""
    if os.path.exists(ARQUIVO_PRODUTOS_CACHE):
        try:
            with open(ARQUIVO_PRODUTOS_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_cache_produtos(produtos: Dict) -> bool:
    """Salva produtos no cache (na raiz)"""
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
        logger.error(f"Erro ao salvar cache de produtos: {e}")
        return False

def limpar_cache_produtos() -> bool:
    """Limpa cache de produtos"""
    if os.path.exists(ARQUIVO_PRODUTOS_CACHE):
        try:
            os.remove(ARQUIVO_PRODUTOS_CACHE)
            logger.info("Cache de produtos removido")
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
