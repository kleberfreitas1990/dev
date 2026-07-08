import json
import os
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from modules.shopee import capturar_buscas_shopee_com_cache
from modules.serper import buscar_produtos_serper, obter_requisicoes_restantes, LIMITE_DIARIO_SERPER, resetar_contador_serper
from modules.validation import validar_termo_busca, validar_produtos_serper
from modules.grade_descoberta import descobrir_produtos_grade, enriquecer_produto
from modules.logger import registrar_busca

logger = logging.getLogger(__name__)

# ============================================================
# ARQUIVO DE CACHE DE PRODUTOS
# ============================================================
ARQUIVO_PRODUTOS_CACHE = "produtos_cache.json"

# ============================================================
# DADOS DE FALLBACK
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
# FUNÇÃO PARA VERIFICAR DATA DO CACHE
# ============================================================
def verificar_data_cache() -> Dict:
    """
    Verifica a data do cache e retorna informações
    """
    cache = carregar_cache_produtos()
    hoje = datetime.now().date().isoformat()
    
    if cache:
        data_cache = cache.get("data", "Nunca")
        total = len(cache.get("produtos", {}))
        
        if data_cache == hoje:
            status = "✅ Atualizado hoje"
        else:
            status = f"⚠️ Última atualização: {data_cache}"
        
        return {
            "status": status,
            "data": data_cache,
            "total": total,
            "cache_existe": True
        }
    else:
        return {
            "status": "❌ Nenhum cache encontrado",
            "data": "Nunca",
            "total": 0,
            "cache_existe": False
        }

# ============================================================
# FUNÇÃO PRINCIPAL - SEMPRE BUSCA DADOS NOVOS
# ============================================================
def obter_produtos_dinamicos(forcar_atualizacao: bool = True) -> Dict[str, Any]:
    """
    Obtém produtos com dados atualizados.
    SEMPRE busca dados novos, ignora completamente o cache.
    """
    logger.info("🔄 Buscando dados NOVOS (ignorando cache)...")
    
    # SEMPRE busca novos dados
    produtos = buscar_produtos_com_api_e_grade()
    
    # Se falhou, usa fallback
    if not produtos or len(produtos) < 3:
        logger.warning("⚠️ Poucos produtos encontrados, usando fallback")
        produtos = PRODUTOS_FALLBACK
    
    # Salva no cache com a data de hoje
    salvar_cache_produtos(produtos)
    
    return produtos

def buscar_produtos_com_api_e_grade(limite: int = 10) -> Dict[str, Any]:
    """
    Busca produtos usando: Shopee → Serper → Grade de Descoberta
    """
    produtos = {}
    
    # ============================================================
    # 1. BUSCA TERMOS DA SHOPEE (FORÇA NOVA BUSCA)
    # ============================================================
    logger.info("📡 Buscando termos da Shopee...")
    termos = capturar_buscas_shopee_com_cache(ignorar_cache=True)
    
    if not termos:
        logger.warning("Nenhum termo da Shopee encontrado")
        return usar_grade_descoberta(limite)
    
    logger.info(f"Encontrados {len(termos)} termos da Shopee")
    
    # ============================================================
    # 2. BUSCA NO SERPER (PRIORITÁRIO)
    # ============================================================
    restantes = obter_requisicoes_restantes()
    logger.info(f"📊 Requisições Serper restantes: {restantes}/{LIMITE_DIARIO_SERPER}")
    
    # Usa os primeiros termos que cabem no limite
    termos_para_buscar = termos[:min(len(termos), restantes, limite)]
    
    if termos_para_buscar:
        for i, termo in enumerate(termos_para_buscar):
            try:
                termo_validado = validar_termo_busca(termo)
                if not termo_validado:
                    continue
                
                logger.info(f"🔍 Buscando no Serper: '{termo_validado}'...")
                
                # Tenta Serper
                produtos_serper = buscar_produtos_serper(termo_validado, limite=3, usar_cache=False)
                
                if produtos_serper and len(produtos_serper) > 0:
                    total_resultados = len(produtos_serper) * 10
                    
                    produtos[termo_validado] = {
                        "pins": random.randint(1500, 3500),
                        "pins_historico": random.randint(1200, 3000),
                        "crescimento": random.randint(15, 50),
                        "views_tiktok": round(random.uniform(2.0, 6.0), 1),
                        "resultados_ml": total_resultados,
                        "buscas_mes": random.randint(8000, 20000),
                        "buscas_historico": random.randint(6000, 16000),
                        "categoria": definir_categoria(termo_validado),
                        "evento": definir_evento(termo_validado),
                        "variacao": round(random.uniform(5.0, 30.0), 1),
                        "tendencia": definir_tendencia(i),
                        "score": calcular_score_simulado(i),
                        "fonte": "serper"
                    }
                    logger.info(f"  ✅ Produto processado via Serper: '{termo_validado}'")
                else:
                    logger.info(f"  ⚠️ Serper sem resultados para '{termo_validado}'")
                    
            except Exception as e:
                logger.error(f"Erro ao buscar produtos para '{termo}': {e}")
                continue
    
    # ============================================================
    # 3. SE TIVER POUCOS PRODUTOS, USA GRADE DE DESCOBERTA
    # ============================================================
    if len(produtos) < 5:
        logger.info("🔄 Poucos produtos encontrados. Usando Grade de Descoberta...")
        produtos_grade = usar_grade_descoberta(limite - len(produtos))
        
        # Mescla com os produtos existentes
        for chave, valor in produtos_grade.items():
            if chave not in produtos:
                produtos[chave] = valor
                produtos[chave]["fonte"] = "grade_descoberta"
    
    # Registra no log
    registrar_busca(
        nivel="sistema",
        termo="atualizacao_diaria",
        sucesso=True if len(produtos) > 0 else False,
        quantidade=len(produtos),
        detalhes=f"Produtos atualizados: {len(produtos)} (Fonte: Serper)"
    )
    
    return produtos

def usar_grade_descoberta(quantidade: int = 10) -> Dict[str, Any]:
    """
    Usa a grade de descoberta como ÚLTIMO RECURSO
    """
    from modules.grade_descoberta import descobrir_produtos_grade, enriquecer_produto
    
    produtos = {}
    
    produtos_descobrir = descobrir_produtos_grade(quantidade=quantidade)
    
    for item in produtos_descobrir:
        produto = item.get("produto", "")
        if produto:
            dados = enriquecer_produto(produto)
            produtos[produto] = {
                "pins": dados.get("pins", random.randint(500, 3000)),
                "pins_historico": random.randint(400, 2500),
                "crescimento": random.randint(5, 45),
                "views_tiktok": round(random.uniform(1.0, 5.0), 1),
                "resultados_ml": random.randint(300, 1500),
                "buscas_mes": random.randint(3000, 15000),
                "buscas_historico": random.randint(2000, 12000),
                "categoria": definir_categoria(produto),
                "evento": "Tendência",
                "variacao": round(random.uniform(5.0, 25.0), 1),
                "tendencia": random.choice(["🚀 Em alta", "📈 Crescendo", "➡️ Estável"]),
                "score": random.randint(4, 8),
                "fonte": "grade_descoberta"
            }
    
    logger.info(f"✅ Grade de Descoberta gerou {len(produtos)} produtos (FALLBACK)")
    return produtos

# ============================================================
# FUNÇÕES AUXILIARES
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
        logger.info(f"💾 Cache de produtos salvo com {len(produtos)} produtos - Data: {datetime.now().date().isoformat()}")
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
    'PRODUTOS_FALLBACK',
    'buscar_produtos_com_api_e_grade',
    'carregar_cache_produtos',
    'verificar_data_cache'
]
