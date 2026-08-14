"""Grade de Descoberta de Produtos baseada em fontes de marketplace.

A grade não preenche lacunas com produtos estáticos, pontuações aleatórias,
Pinterest, TikTok, Google ou métricas simuladas. Quando não houver uma coleta
verificável disponível, ela retorna menos itens em vez de inventar sinais.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from modules.adult_content_filter import eh_termo_adulto
from modules.produtos_dinamicos import obter_produtos_marketplace_v49

logger = logging.getLogger(__name__)

# Mantido para compatibilidade com telas legadas. Não serve como fallback de dados.
GRADE_PRODUTOS: Dict[str, Dict[str, List[str]]] = {}
MOTIVOS_BUSCA: Dict[str, str] = {}

FONTES_COMERCIAIS = (
    "Shopee Daily",
    "Shopee Live",
    "Shopee Real-Time Scraping",
    "Mercado Livre Trends",
    "Amazon Bestsellers",
)


def obter_indicadores_horario(produto: str) -> Dict[str, Any]:
    """Informa somente o horário da geração; não estima volume de audiência."""
    agora = datetime.now()
    return {
        "periodo": "coleta atual",
        "horario": agora.strftime("%H:%M"),
        "intensidade": None,
        "emoji": "🕒",
        "label": "Horário da consulta",
        "melhor_horario": "Não informado pela fonte",
        "porcentagem": None,
    }


def obter_motivo_busca(produto: str) -> str:
    """Evita atribuir um motivo quando a fonte não publica essa informação."""
    return "Sinal comercial confirmado na fonte de marketplace exibida."


def get_produtos_sazonais_com_motivos() -> List[Dict[str, str]]:
    """Não fornece recomendações sazonais sem uma fonte comercial atual."""
    return []


def get_produtos_sazonais() -> List[str]:
    """Compatibilidade com chamadas legadas, sem inserir dados estimados."""
    return []


def _item_comercial_permitido(termo: str, dados: Dict[str, Any]) -> bool:
    if not termo or eh_termo_adulto(termo):
        return False
    fonte = str(dados.get("fonte", ""))
    return fonte in FONTES_COMERCIAIS


def descobrir_produtos_grade(categoria: str = None, quantidade: int = 20) -> List[Dict[str, Any]]:
    """Retorna exclusivamente itens coletados de marketplaces verificáveis."""
    dados_dinamicos = obter_produtos_marketplace_v49()
    produtos: List[Dict[str, Any]] = []
    termos_usados = set()

    for fonte in FONTES_COMERCIAIS:
        for termo, dados in dados_dinamicos.items():
            if len(produtos) >= quantidade:
                break
            if termo in termos_usados or not isinstance(dados, dict):
                continue
            if not _item_comercial_permitido(termo, dados):
                continue
            categoria_item = str(dados.get("categoria", "Marketplace"))
            if categoria and categoria_item.lower() != categoria.lower():
                continue

            termos_usados.add(termo)
            indicador = str(dados.get("evento", "Destaque de marketplace"))
            produtos.append({
                "produto": termo,
                "fonte": fonte,
                "categoria": categoria_item,
                "score": dados.get("score") if dados.get("score") is not None else "Não informado",
                "motivo": f"{indicador}.",
                "indicadores": obter_indicadores_horario(termo),
                "origem_coleta": dados.get("origem_coleta", "Não informado"),
                "atualizado": dados.get("atualizado", "Não informado"),
            })
        if len(produtos) >= quantidade:
            break

    if not produtos:
        logger.info("Nenhuma fonte atual de marketplace disponível para a Grade de Descoberta.")
    return produtos


def enriquecer_produto(produto: str) -> Dict[str, Any]:
    """Retorna um registro neutro; não cria métricas de Pinterest, TikTok ou Google."""
    return {
        "produto": produto,
        "pins": None,
        "views_tiktok": None,
        "crescimento": None,
        "buscas_mes": None,
        "categoria": "Não informado",
        "tendencia": "Sem fonte comercial confirmada",
        "score": "Não informado",
        "fonte": "Sem fonte comercial confirmada",
        "motivo": "Este produto não foi enriquecido por dados verificáveis de marketplace.",
        "indicadores": obter_indicadores_horario(produto),
    }


def obter_produtos_por_categoria(categoria: str) -> List[str]:
    """A grade estática foi removida; use descobrir_produtos_grade para dados atuais."""
    return []


def obter_hashtags_categoria(categoria: str) -> List[str]:
    return ["#marketplace", "#produto", "#oferta"]


def mesclar_produtos(produtos_existentes: List[str], quantidade: int = 5) -> List[str]:
    """Completa listas apenas com termos provenientes das fontes comerciais atuais."""
    encontrados = descobrir_produtos_grade(quantidade=quantidade * 3)
    novos = [item["produto"] for item in encontrados if item["produto"] not in produtos_existentes]
    return novos[:quantidade]


__all__ = [
    "descobrir_produtos_grade",
    "enriquecer_produto",
    "get_produtos_sazonais",
    "get_produtos_sazonais_com_motivos",
    "GRADE_PRODUTOS",
    "obter_produtos_por_categoria",
    "obter_hashtags_categoria",
    "mesclar_produtos",
    "obter_motivo_busca",
    "MOTIVOS_BUSCA",
    "obter_indicadores_horario",
]
