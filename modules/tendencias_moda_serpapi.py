"""Tendências de moda feminina baseadas em Google Shopping via SerpApi.

Este módulo não usa fallback estático, Pinterest ou projeções sazonais como se
fossem dados coletados. Sem uma resposta válida da API, a tela permanece sem
dados confirmados e informa o motivo ao usuário.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

CACHE_FILE = "moda_trends_serpapi_cache.json"
CACHE_TTL_HORAS = 6
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
SERPAPI_DOCS_URL = "https://serpapi.com/google-trends-api"

TERMOS_MODA_FEMININA = [
    "Saia Balonê",
    "Estilo Boho",
    "Quiet Luxury",
    "Calça Cargo",
    "Blazer Alfaiataria",
    "Vestido Midi",
    "Jeans Wide Leg",
    "Crop Top",
    "Mochila de Couro",
    "Tênis Branco",
]


def _cache_valido() -> bool:
    """Retorna True somente para cache recente e confirmado pela API."""
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as arquivo:
            cache = json.load(arquivo)
        timestamp = cache.get("timestamp")
        return bool(
            timestamp
            and cache.get("status_coleta") == "sucesso"
            and cache.get("fonte") == "Google Shopping (SerpApi)"
            and datetime.now() - datetime.fromisoformat(timestamp)
            < timedelta(hours=CACHE_TTL_HORAS)
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _carregar_cache() -> Optional[List[Dict[str, Any]]]:
    """Carrega somente dados já confirmados, sem renovar a rede."""
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as arquivo:
            cache = json.load(arquivo)
        if cache.get("status_coleta") != "sucesso":
            return None
        dados = cache.get("dados")
        return dados if isinstance(dados, list) and dados else None
    except (OSError, TypeError, json.JSONDecodeError):
        return None


def _salvar_cache(
    dados: List[Dict[str, Any]],
    periodo_base: str,
    periodo_atual: str,
) -> None:
    """Persiste a resposta confirmada, com proveniência e períodos consultados."""
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "data_coleta": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status_coleta": "sucesso",
        "fonte": "Google Shopping (SerpApi)",
        "fonte_url": SERPAPI_DOCS_URL,
        "periodo_base": periodo_base,
        "periodo_atual": periodo_atual,
        "dados": dados,
    }
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as arquivo:
            json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        logger.info("Cache de moda salvo: %s (%s termos)", CACHE_FILE, len(dados))
    except OSError as erro:
        logger.error("Erro ao salvar cache de moda: %s", erro)


def _periodos_comparacao() -> Tuple[str, str]:
    """Retorna períodos completos do ano anterior e do ano corrente até hoje."""
    hoje = datetime.now()
    ano_atual = hoje.year
    periodo_base = f"{ano_atual - 1}-01-01 {ano_atual - 1}-12-31"
    periodo_atual = f"{ano_atual}-01-01 {hoje.strftime('%Y-%m-%d')}"
    return periodo_base, periodo_atual


def _chave_serpapi() -> str:
    """Lê a chave sem gravá-la no código, cache ou logs."""
    chave = os.environ.get("SERPAPI_KEY", "")
    if chave:
        return chave
    try:
        import streamlit as st

        return st.secrets.get("SERPAPI_KEY", "")
    except Exception:
        return ""


def _consultar_google_shopping(
    query_string: str,
    periodo: str,
    chave: str,
) -> Dict[str, Any]:
    """Consulta o interesse no Google Shopping por até cinco termos."""
    resposta = requests.get(
        SERPAPI_ENDPOINT,
        params={
            "engine": "google_trends",
            "q": query_string,
            "date": periodo,
            "geo": "BR",
            "hl": "pt-br",
            "tz": "-180",
            "gprop": "froogle",
            "data_type": "TIMESERIES",
            "api_key": chave,
        },
        timeout=30,
    )
    resposta.raise_for_status()
    payload = resposta.json()
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    return payload


def _extrair_medias(payload: Dict[str, Any]) -> Dict[str, float]:
    """Extrai as médias documentadas pelo endpoint de interesse ao longo do tempo."""
    medias: Dict[str, float] = {}
    for item in payload.get("interest_over_time", {}).get("averages", []):
        termo = item.get("query")
        valor = item.get("extracted_value", item.get("value", 0))
        if not termo:
            continue
        try:
            medias[termo] = float(valor)
        except (TypeError, ValueError):
            medias[termo] = 0.0
    return medias


def _registro(termo: str, base: float, atual: float) -> Dict[str, Any]:
    if base <= 0 and atual <= 0:
        status = "Sem dados"
        variacao = "N/D"
        variacao_num = None
    elif atual > base:
        status = "Em Alta"
        variacao_num = round(((atual - base) / max(base, 1)) * 100, 1)
        variacao = f"+{variacao_num:.1f}%"
    else:
        status = "Em Queda"
        variacao_num = round(((atual - base) / max(base, 1)) * 100, 1)
        variacao = f"{variacao_num:.1f}%"

    return {
        "termo": termo,
        "interesse_ano_anterior": round(base, 2),
        "interesse_ano_atual": round(atual, 2),
        "status": status,
        "variacao": variacao,
        "variacao_num": variacao_num,
        "categoria": "Moda Feminina",
        "fonte": "Google Shopping (SerpApi)",
        "fonte_url": SERPAPI_DOCS_URL,
        "metrica_verificada": True,
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def obter_tendencias_moda_serpapi(
    forcar_atualizacao: bool = False,
) -> List[Dict[str, Any]]:
    """Obtém dados reais do Google Shopping ou retorna lista vazia, sem fallback."""
    if not forcar_atualizacao and _cache_valido():
        dados_cache = _carregar_cache()
        if dados_cache:
            logger.info("Tendências de moda: cache recente confirmado")
            return dados_cache

    chave = _chave_serpapi()
    if not chave:
        logger.warning("SERPAPI_KEY não configurada; nenhum dado de moda será inventado")
        return []

    periodo_base, periodo_atual = _periodos_comparacao()
    medias_base: Dict[str, float] = {}
    medias_atual: Dict[str, float] = {}
    lotes = [
        TERMOS_MODA_FEMININA[indice : indice + 5]
        for indice in range(0, len(TERMOS_MODA_FEMININA), 5)
    ]

    try:
        for lote in lotes:
            query_string = ",".join(lote)
            medias_base.update(
                _extrair_medias(
                    _consultar_google_shopping(query_string, periodo_base, chave)
                )
            )
            medias_atual.update(
                _extrair_medias(
                    _consultar_google_shopping(query_string, periodo_atual, chave)
                )
            )
    except (requests.RequestException, RuntimeError, ValueError, TypeError) as erro:
        logger.error("Google Shopping indisponível: %s", erro)
        return []

    dados = [
        _registro(termo, medias_base.get(termo, 0), medias_atual.get(termo, 0))
        for termo in TERMOS_MODA_FEMININA
    ]
    if not any(item["status"] != "Sem dados" for item in dados):
        logger.warning("Google Shopping retornou zero dados para os termos de moda")
        return []

    _salvar_cache(dados, periodo_base, periodo_atual)
    return dados


def render_tendencias_moda_dashboard() -> None:
    """Renderiza apenas dados confirmados, sem gráficos ou previsões artificiais."""
    import pandas as pd
    import streamlit as st

    st.markdown("## 👗 Tendências de Moda Feminina — Google Shopping")
    st.caption(
        "Dados coletados do Google Trends com propriedade Google Shopping (SerpApi), "
        "sem fallback estático ou previsão editorial apresentada como tendência real."
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        atualizar = st.button("🔄 Atualizar dados", use_container_width=True)
    with col_info:
        cache_info = ""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as arquivo:
                    cache = json.load(arquivo)
                cache_info = (
                    f"Última coleta confirmada: {cache.get('data_coleta', 'N/A')} | "
                    f"Período atual: {cache.get('periodo_atual', 'N/A')}"
                )
            except (OSError, TypeError, json.JSONDecodeError):
                pass
        st.caption(cache_info or "Nenhuma coleta confirmada")

    dados = obter_tendencias_moda_serpapi(forcar_atualizacao=atualizar)
    if not dados:
        st.warning(
            "Nenhum dado confirmado de Google Shopping está disponível agora. "
            "A tela não usa cache antigo, Pinterest ou números estimados. "
            "Configure SERPAPI_KEY e execute a coleta diária."
        )
        return

    df = pd.DataFrame(dados)
    colunas = {
        "termo": "Busca",
        "interesse_ano_anterior": "Interesse ano anterior",
        "interesse_ano_atual": "Interesse ano atual",
        "status": "Status",
        "variacao": "Variação",
        "categoria": "Categoria",
        "atualizado": "Coletado em",
    }
    st.dataframe(
        df[list(colunas)].rename(columns=colunas),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        f"Fonte: Google Shopping via SerpApi | "
        f"[documentação da API]({SERPAPI_DOCS_URL}) | "
        f"{len(df)} termos confirmados"
    )
