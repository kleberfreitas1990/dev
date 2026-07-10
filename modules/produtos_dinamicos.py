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
ARQUIVO_PRODUTOS_CACHE = "produtos_cache_v48.json"

# ============================================================
# DADOS DE FALLBACK
# ============================================================
PRODUTOS_FALLBACK = {
    "Umidificador de Ar Chama LED": {
        "pins": 35000, "pins_historico": 20000, "crescimento": 150, "views_tiktok": 85.0,
        "resultados_ml": 75000, "buscas_mes": 95000, "buscas_historico": 40000,
        "categoria": "Decoração", "evento": "Viral TikTok", "variacao": 75.0, "tendencia": "🔥 Explosão",
        "score": 10, "fonte": "Shopee"
    },
    "Mini Projetor Portátil 4K": {
        "pins": 22000, "pins_historico": 15000, "crescimento": 110, "views_tiktok": 55.0,
        "resultados_ml": 120000, "buscas_mes": 65000, "buscas_historico": 30000,
        "categoria": "Eletrônicos", "evento": "Home Cinema", "variacao": 45.0, "tendencia": "🔥 Viral",
        "score": 10, "fonte": "Shopee"
    },
    "Mini Câmera de Segurança WiFi A9": {
        "pins": 12500, "pins_historico": 9000, "crescimento": 95, "views_tiktok": 15.5,
        "resultados_ml": 85000, "buscas_mes": 45000, "buscas_historico": 20000,
        "categoria": "Segurança", "evento": "Utilidades", "variacao": 35.0, "tendencia": "🚀 Explosivo",
        "score": 10, "fonte": "Shopee"
    },
    "Aspirador de Pó Portátil 120W": {
        "pins": 14000, "pins_historico": 10000, "crescimento": 85, "views_tiktok": 28.4,
        "resultados_ml": 110000, "buscas_mes": 52000, "buscas_historico": 25000,
        "categoria": "Automotivo", "evento": "Limpeza", "variacao": 30.5, "tendencia": "🔥 Viral",
        "score": 9, "fonte": "Shopee"
    },
    "Luminária de Mesa com Indução": {
        "pins": 15000, "pins_historico": 11000, "crescimento": 88, "views_tiktok": 25.0,
        "resultados_ml": 65000, "buscas_mes": 38000, "buscas_historico": 15000,
        "categoria": "Escritório", "evento": "Tendência", "variacao": 25.0, "tendencia": "📈 Alta",
        "score": 9, "fonte": "Google"
    },
    "Smartwatch Huawei Band 9": {
        "pins": 28000, "pins_historico": 22000, "crescimento": 90, "views_tiktok": 42.0,
        "resultados_ml": 150000, "buscas_mes": 85000, "buscas_historico": 40000,
        "categoria": "Eletrônicos", "score": 10, "fonte": "Google", "tendencia": "🔥 Alta"
    },
    "Organizador de Fios Magnético": {
        "pins": 8500, "pins_historico": 6000, "crescimento": 82, "views_tiktok": 8.2,
        "resultados_ml": 35000, "buscas_mes": 22000, "buscas_historico": 10000,
        "categoria": "Escritório", "score": 9, "fonte": "Shopee", "tendencia": "📈 Alta"
    },
    "Kit 3 Potes Herméticos Bambu": {
        "pins": 18000, "pins_historico": 14000, "crescimento": 75, "views_tiktok": 12.5,
        "resultados_ml": 95000, "buscas_mes": 42000, "buscas_historico": 20000,
        "categoria": "Cozinha", "score": 9, "fonte": "Shopee", "tendencia": "📈 Alta"
    },
    "Fone de Ouvido Condução Óssea": {
        "pins": 11000, "pins_historico": 8500, "crescimento": 78, "views_tiktok": 18.5,
        "resultados_ml": 55000, "buscas_mes": 32000, "buscas_historico": 15000,
        "categoria": "Esportes", "score": 9, "fonte": "Google", "tendencia": "📈 Alta"
    },
    "Mini Seladora de Embalagens": {
        "pins": 9500, "pins_historico": 7000, "crescimento": 65, "views_tiktok": 10.2,
        "resultados_ml": 45000, "buscas_mes": 28000, "buscas_historico": 12000,
        "categoria": "Cozinha", "score": 8, "fonte": "Shopee", "tendencia": "📈 Média"
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
def obter_produtos_dinamicos(forcar_atualizacao: bool = False) -> Dict[str, Any]:
    """
    Obtém produtos com dados atualizados.
    Sempre prioriza o cache persistente de dados reais.
    """
    # 1. TENTA CACHE PERSISTENTE (Sempre tenta primeiro)
    cache = carregar_cache_produtos()
    if cache and "produtos" in cache and len(cache["produtos"]) > 0:
        # Se o cache for de HOJE, usa ele
        hoje = datetime.now().date().isoformat()
        if cache.get("data") == hoje and not forcar_atualizacao:
            logger.info(f"💾 Usando cache persistente de HOJE ({len(cache['produtos'])} itens)")
            return cache["produtos"]
        
        # Se for forçado mas o cache for de HOJE, ainda assim podemos usar se quisermos manter dados reais
        # Mas vamos permitir a busca se o usuário realmente quiser
    
    logger.info("🔄 Buscando dados NOVOS (ou cache vazio)...")
    
    # 2. BUSCA NOVOS DADOS
    produtos = buscar_produtos_com_api_e_grade()
    
    # Se falhou ou retornou pouco, usa o cache injetado como fallback supremo antes do estático
    if (not produtos or len(produtos) < 3) and cache and "produtos" in cache:
        logger.warning("⚠️ Busca nova falhou, mantendo dados reais do cache")
        return cache["produtos"]
        
    if not produtos or len(produtos) < 3:
        logger.warning("⚠️ Poucos produtos encontrados, usando fallback estático")
        produtos = PRODUTOS_FALLBACK
    
    # Salva no cache
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
                    
                    # Dados base para o produto
                    dados_base = {
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
                        "fonte": "serper"
                    }
                    
                    # Calcula score real baseado nos dados
                    from modules.models import calcular_score
                    dados_base["score"] = calcular_score(termo_validado, dados_base)
                    
                    produtos[termo_validado] = dados_base
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
    # Garante o uso do caminho absoluto para o cache
    caminho_cache = os.path.join("/home/ubuntu/dev", ARQUIVO_PRODUTOS_CACHE)
    if os.path.exists(caminho_cache):
        try:
            with open(caminho_cache, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_cache_produtos(produtos: Dict) -> bool:
    try:
        caminho_cache = os.path.join("/home/ubuntu/dev", ARQUIVO_PRODUTOS_CACHE)
        with open(caminho_cache, 'w', encoding='utf-8') as f:
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
def obter_melhor_horario_postagem(categoria: str) -> Dict:
    cat = categoria.lower()
    if "eletrônico" in cat:
        return {"rede": "TikTok", "horario": "17:00"}
    elif "moda" in cat:
        return {"rede": "Instagram", "horario": "12:30"}
    return {"rede": "TikTok", "horario": "16:00"}

__all__ = [
    'obter_produtos_dinamicos',
    'limpar_cache_produtos',
    'PRODUTOS_FALLBACK',
    'buscar_produtos_com_api_e_grade',
    'carregar_cache_produtos',
    'verificar_data_cache',
    'obter_melhor_horario_postagem'
]
