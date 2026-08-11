"""Tendências públicas do Pinterest Brasil para o calendário de conteúdo.

Os termos abaixo são sinais editoriais observados na página pública de tendências do
Pinterest Brasil em 11/08/2026. Eles não representam volume de buscas nem métricas
proprietárias; o score é apenas uma prioridade editorial interna para o painel.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

ARQUIVO_PINTEREST_CACHE = "pinterest_trends_cache.json"
DATA_REFERENCIA = "2026-08-11"
FONTE_URL = "https://br.pinterest.com/today/"


def obter_tendencias_pinterest() -> Dict[str, Dict[str, Any]]:
    """Retorna sinais atuais do Pinterest Brasil com proveniência explícita."""
    raw_data = {
        "Azul gelo no look": {
            "termo": "Azul gelo no look",
            "score": 9.4,
            "categoria": "Moda Feminina",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "look azul gelo primavera verão 2026",
            "hashtags": ["#azulgelo", "#lookazul", "#modaprimavera", "#lookfeminino"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
        "Penteados diferentões": {
            "termo": "Penteados diferentões",
            "score": 9.2,
            "categoria": "Beleza",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "penteados diferentes fáceis 2026",
            "hashtags": ["#penteados", "#penteadocriativo", "#cabelos", "#belezafeminina"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
        "Unhas vampíricas": {
            "termo": "Unhas vampíricas",
            "score": 8.9,
            "categoria": "Beleza",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "unhas vampíricas nail art 2026",
            "hashtags": ["#unhasvampiricas", "#nailart", "#unhasdecoradas", "#nailinspo"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
        "Casamentos rendados": {
            "termo": "Casamentos rendados",
            "score": 8.6,
            "categoria": "Moda e Eventos",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "vestido renda casamento inspiração 2026",
            "hashtags": ["#casamentorendado", "#vestidoderenda", "#noivas", "#weddinginspo"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
        "Quartos estilo jardim": {
            "termo": "Quartos estilo jardim",
            "score": 8.4,
            "categoria": "Casa e Decoração",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "quarto estilo jardim decoração primavera",
            "hashtags": ["#quartojardim", "#decoracao", "#quartocriativo", "#casainspiradora"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
        "Quartos e apartamentos pequenos": {
            "termo": "Quartos e apartamentos pequenos",
            "score": 8.2,
            "categoria": "Casa e Organização",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "organização apartamento pequeno soluções",
            "hashtags": ["#apartamentopequeno", "#organizacao", "#quartopequeno", "#decoracao"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
        "Edições que fazem o look brilhar": {
            "termo": "Edições que fazem o look brilhar",
            "score": 8.0,
            "categoria": "Moda e Conteúdo",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "edição vídeo look brilho transição",
            "hashtags": ["#lookbrilhante", "#edicaodevideo", "#transicao", "#moda2026"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
        "Ideias de ponto": {
            "termo": "Ideias de ponto",
            "score": 7.8,
            "categoria": "Artesanato e Moda",
            "evento": "Sinal atual do Pinterest Brasil",
            "palavra_chave": "crochê e ideias de ponto 2026",
            "hashtags": ["#croche", "#artesanato", "#feitoamao", "#modacriativa"],
            "sinal_publico": "Tema listado em Principais tendências de hoje",
        },
    }

    tendencias: Dict[str, Dict[str, Any]] = {}
    for nome, dados in raw_data.items():
        item = dict(dados)
        item.update(
            {
                "fonte": "Pinterest Brasil — Principais tendências de hoje",
                "fonte_url": FONTE_URL,
                "origem_coleta": "pagina_publica_pinterest_today",
                "data_referencia": DATA_REFERENCIA,
                "atualizado": DATA_REFERENCIA,
                "metrica_verificada": False,
                "score_tipo": "prioridade_editorial",
            }
        )
        tendencias[nome] = item
    return tendencias


def salvar_cache_pinterest(dados: Dict[str, Dict[str, Any]]) -> None:
    cache = {
        "timestamp": datetime.now().isoformat(),
        "data": DATA_REFERENCIA,
        "data_referencia": DATA_REFERENCIA,
        "dados": dados,
        "fonte_url": FONTE_URL,
    }
    with open(ARQUIVO_PINTEREST_CACHE, "w", encoding="utf-8") as arquivo:
        json.dump(cache, arquivo, ensure_ascii=False, indent=2)


def obter_pinterest_trends_cache() -> Dict[str, Dict[str, Any]]:
    """Lê cache compatível e usa os dados atuais como fallback seguro."""
    if os.path.exists(ARQUIVO_PINTEREST_CACHE):
        try:
            with open(ARQUIVO_PINTEREST_CACHE, "r", encoding="utf-8") as arquivo:
                cache = json.load(arquivo)
            if cache.get("data") == DATA_REFERENCIA:
                dados = cache.get("dados", {})
                if isinstance(dados, dict) and dados:
                    return dados
        except (OSError, json.JSONDecodeError, TypeError) as erro:
            logger.error("Erro ao ler cache do Pinterest: %s", erro)
    return obter_tendencias_pinterest()
