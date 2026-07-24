"""Pipeline de composição da grade de produtos.

As fontes Mercado Livre e Amazon são adicionadas somente pelos respectivos
coletores oficiais. Este módulo não cria termos, métricas ou categorias de
fallback para essas duas fontes.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Mantidas vazias somente para compatibilidade com importações legadas. A grade
# não pode usar listas estáticas como se fossem resultados de fontes oficiais.
TERMOS_PRINT: tuple[str, ...] = ()
TERMOS_ML: tuple[str, ...] = ()

ARQUIVO_PRODUTOS_CACHE = "produtos_cache_v48.json"
ARQUIVO_SHOPEE_CACHE = "shopee_trends.json"
ARQUIVO_AMAZON_CACHE = "amazon_trends.json"  # Compatibilidade com integrações legadas.
ARQUIVO_SHOPEE_LIVE_CACHE = "shopee_live_cache.json"
DIRETORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_PRODUTOS_CACHE = os.path.join(DIRETORIO_RAIZ, ARQUIVO_PRODUTOS_CACHE)
CAMINHO_SHOPEE_CACHE = os.path.join(DIRETORIO_RAIZ, ARQUIVO_SHOPEE_CACHE)
CAMINHO_AMAZON_CACHE = os.path.join(DIRETORIO_RAIZ, ARQUIVO_AMAZON_CACHE)
CAMINHO_SHOPEE_LIVE_CACHE = os.path.join(DIRETORIO_RAIZ, ARQUIVO_SHOPEE_LIVE_CACHE)


def _ler_cache_produtos() -> Dict[str, Any]:
    """Lê o cache agregado usado pelo painel, sem o injetar automaticamente na grade."""
    if not os.path.exists(CAMINHO_PRODUTOS_CACHE):
        return {}
    try:
        with open(CAMINHO_PRODUTOS_CACHE, "r", encoding="utf-8") as arquivo:
            cache = json.load(arquivo)
        return cache if isinstance(cache, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError) as erro:
        logger.warning("Não foi possível carregar o cache de produtos: %s", erro)
        return {}


def _carregar_shopee_live() -> Dict[str, Any]:
    """Converte o cache de atualização da Shopee para o schema da grade."""
    if not os.path.exists(CAMINHO_SHOPEE_LIVE_CACHE):
        return {}

    try:
        with open(CAMINHO_SHOPEE_LIVE_CACHE, "r", encoding="utf-8") as arquivo:
            payload = json.load(arquivo)
    except (OSError, json.JSONDecodeError, TypeError) as erro:
        logger.warning("Não foi possível carregar o cache Shopee Live: %s", erro)
        return {}

    itens = payload.get("dados", []) if isinstance(payload, dict) else []
    if not isinstance(itens, list):
        return {}

    produtos: Dict[str, Any] = {}
    for posicao, item in enumerate(itens):
        if not isinstance(item, dict):
            continue
        nome = str(item.get("termo", "")).strip()
        if not nome:
            continue

        produtos[nome] = {
            "pins": 0,
            "pins_historico": 0,
            "crescimento": max(40, 180 - (posicao * 4)),
            "views_tiktok": 0,
            "resultados_ml": 0,
            "buscas_mes": 0,
            "buscas_historico": 0,
            "categoria": item.get("categoria", "Outros"),
            "evento": f"{item.get('vendas', 'Em alta')} vendas na Shopee",
            "variacao": max(20, 80 - (posicao * 2)),
            "tendencia": "Em alta",
            "score": max(1, 10 - (posicao // 10)),
            "fonte": "Shopee Live",
            "origem_coleta": item.get("origem_coleta", "cache_shopee_live"),
            "avaliacao": item.get("avaliacao"),
            "preco": item.get("preco"),
            "atualizado": item.get("atualizado"),
        }

    return produtos


def _carregar_shopee_legacy() -> Dict[str, Any]:
    """Carrega o cache legado da Shopee sem afetar a proveniência das outras fontes."""
    if not os.path.exists(CAMINHO_SHOPEE_CACHE):
        return {}
    try:
        with open(CAMINHO_SHOPEE_CACHE, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError) as erro:
        logger.warning("Falha ao carregar tendências da Shopee: %s", erro)
        return {}


def _adicionar_produtos(destino: Dict[str, Any], origem: Dict[str, Any]) -> None:
    """Acrescenta entradas íntegras, preservando a prioridade da fonte anterior."""
    for nome, dados in origem.items():
        nome_limpo = str(nome).strip()
        if nome_limpo and nome_limpo not in destino and isinstance(dados, dict):
            destino[nome_limpo] = dados


def _forcar_atualizacao_google_shopee() -> Any:
    """Carrega a integração opcional apenas quando uma atualização é solicitada."""
    from modules.google_shopee_trends import forcar_atualizacao_completa

    return forcar_atualizacao_completa()


def _atualizar_fontes_automaticas() -> None:
    """Solicita renovação aos coletores, que validam a origem antes de gravar cache."""
    try:
        _forcar_atualizacao_google_shopee()
    except Exception as erro:
        logger.warning("Falha ao atualizar fontes Google/Shopee: %s", erro)

    try:
        from modules.mercadolivre_scraper import forcar_atualizacao_ml

        forcar_atualizacao_ml()
    except Exception as erro:
        logger.warning("Falha ao atualizar tendências oficiais do Mercado Livre: %s", erro)

    try:
        from modules.amazon_scraper import capturar_bestsellers_amazon

        capturar_bestsellers_amazon(forcar=True)
    except Exception as erro:
        logger.warning("Falha ao atualizar Best Sellers oficiais da Amazon: %s", erro)


def obter_produtos_dinamicos(forcar_atualizacao: bool = False) -> Dict[str, Any]:
    """Compõe a grade exclusivamente com dados fornecidos pelos coletores ativos."""
    if forcar_atualizacao:
        _atualizar_fontes_automaticas()

    produtos: Dict[str, Any] = {}

    # A Shopee mantém sua prioridade operacional já existente.
    _adicionar_produtos(produtos, _carregar_shopee_live())
    _adicionar_produtos(produtos, _carregar_shopee_legacy())

    # Mercado Livre: somente página oficial ou cache da mesma página já validado.
    try:
        from modules.mercadolivre_scraper import obter_tendencias_ml_cache

        dados_ml = obter_tendencias_ml_cache()
        _adicionar_produtos(produtos, dados_ml)
        if dados_ml:
            logger.info("Mercado Livre oficial: %d termos carregados.", len(dados_ml))
    except Exception as erro:
        logger.warning("Falha ao carregar tendências oficiais do Mercado Livre: %s", erro)

    # Amazon: somente Best Sellers oficial ou cache da mesma página já validado.
    try:
        from modules.amazon_scraper import obter_amazon_trends_cache

        dados_amazon = obter_amazon_trends_cache()
        _adicionar_produtos(produtos, dados_amazon)
        if dados_amazon:
            logger.info("Amazon oficial: %d produtos carregados.", len(dados_amazon))
    except Exception as erro:
        logger.warning("Falha ao carregar Best Sellers oficiais da Amazon: %s", erro)

    # Pinterest: Tendências antecipadas de Moda
    try:
        from modules.pinterest_trends import obter_pinterest_trends_cache
        dados_pinterest = obter_pinterest_trends_cache()
        _adicionar_produtos(produtos, dados_pinterest)
        if dados_pinterest:
            logger.info("Pinterest Trends: %d tendências carregadas.", len(dados_pinterest))
    except Exception as erro:
        logger.warning("Falha ao carregar tendências do Pinterest: %s", erro)

    return produtos


def obter_produtos_marketplace_v49(forcar_atualizacao: bool = False) -> Dict[str, Any]:
    """Alias legado usado pelas telas existentes do dashboard."""
    return obter_produtos_dinamicos(forcar_atualizacao=forcar_atualizacao)


# Compatibilidade para módulos que importam esta constante. Não dispara coleta
# de rede no momento da importação, nem fornece termos artificiais.
PRODUTOS_FALLBACK: Dict[str, Any] = {}


def carregar_cache_produtos() -> Dict[str, Any]:
    """Retorna o cache agregado no formato esperado pelas telas administrativas."""
    return _ler_cache_produtos()


def salvar_cache_produtos(produtos: Dict[str, Any]) -> bool:
    """Persiste produtos de forma atômica para evitar arquivos parcialmente gravados."""
    if not isinstance(produtos, dict):
        logger.warning("Cache de produtos não salvo: conteúdo inválido.")
        return False

    cache = {
        "data": datetime.now().date().isoformat(),
        "produtos": produtos,
        "timestamp": datetime.now().isoformat(),
    }
    caminho_temporario = f"{CAMINHO_PRODUTOS_CACHE}.tmp"

    try:
        with open(caminho_temporario, "w", encoding="utf-8") as arquivo:
            json.dump(cache, arquivo, ensure_ascii=False, indent=2)
        os.replace(caminho_temporario, CAMINHO_PRODUTOS_CACHE)
        return True
    except OSError as erro:
        logger.error("Não foi possível salvar o cache de produtos: %s", erro)
        try:
            if os.path.exists(caminho_temporario):
                os.remove(caminho_temporario)
        except OSError:
            pass
        return False


def limpar_cache_produtos() -> bool:
    """Remove o cache persistente; a ausência do arquivo também conta como sucesso."""
    try:
        if os.path.exists(CAMINHO_PRODUTOS_CACHE):
            os.remove(CAMINHO_PRODUTOS_CACHE)
        return True
    except OSError as erro:
        logger.error("Não foi possível limpar o cache de produtos: %s", erro)
        return False


def verificar_data_cache() -> Dict[str, Any]:
    """Verifica a data e a quantidade de itens do cache persistente."""
    cache = carregar_cache_produtos()
    if not cache:
        return {
            "status": "Nenhum cache encontrado",
            "data": "Nunca",
            "total": 0,
            "cache_existe": False,
        }

    data_cache = cache.get("data", "Nunca")
    produtos = cache.get("produtos", {})
    total = len(produtos) if isinstance(produtos, dict) else 0
    hoje = datetime.now().date().isoformat()
    status = "Atualizado hoje" if data_cache == hoje else f"Última atualização: {data_cache}"

    return {
        "status": status,
        "data": data_cache,
        "total": total,
        "cache_existe": True,
    }
