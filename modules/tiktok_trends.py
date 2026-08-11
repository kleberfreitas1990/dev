"""Tendências públicas do TikTok Brasil para conteúdo e calendário.

O TikTok Creative Center exige navegação interativa/login para alguns rankings.
Por isso, este módulo usa sinais públicos recentes do TikTok Discover e do
Creative Center, sem apresentar índices inventados como métricas oficiais.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_FILE = "tiktok_trends_cache.json"
DATA_REFERENCIA = "2026-08-11"
FONTE_CENTRAL = "https://ads.tiktok.com/creative/creativeCenter/trends"

SINAIS_PUBLICOS = [
    {
        "termo": "Moda primavera/verão 2026",
        "categoria": "Moda",
        "prioridade": 9.4,
        "sinal_publico": "Conteúdos públicos destacam cores suaves, texturas metalizadas e rendas.",
        "dica_conteudo": "Monte três looks de transição de estação e compare cores, textura e preço.",
        "hashtags": ["#modaprimavera", "#modaverao2026", "#lookfeminino", "#modabrasileira"],
        "fonte_url": "https://www.tiktok.com/discover/tendencias-primavera-verano-2026-en-brasil",
    },
    {
        "termo": "Vestido floral",
        "categoria": "Moda",
        "prioridade": 9.2,
        "sinal_publico": "Tema recorrente nas buscas públicas de primavera/verão no Brasil.",
        "dica_conteudo": "Faça um vídeo de transição do look de inverno para o vestido floral de primavera.",
        "hashtags": ["#vestidofloral", "#lookprimavera", "#lookdodia", "#modafeminina"],
        "fonte_url": "https://www.tiktok.com/discover/tendencias-primavera-verano-2026-en-brasil",
    },
    {
        "termo": "Cores pastel e azul claro",
        "categoria": "Moda",
        "prioridade": 9.0,
        "sinal_publico": "Buscas públicas citam amarelo manteiga, azul claro, pistache, rosa bebê e lavanda.",
        "dica_conteudo": "Compare cinco combinações pastel usando uma mesma peça-chave.",
        "hashtags": ["#azulclaro", "#amarelomanteiga", "#lookpastel", "#tendenciamoda"],
        "fonte_url": "https://www.tiktok.com/discover/colores-en-tendencias-2026-en-brasil",
    },
    {
        "termo": "Penteados diferentões",
        "categoria": "Beleza",
        "prioridade": 8.9,
        "sinal_publico": "A busca pública de penteados tendência 2026 registra forte volume de publicações.",
        "dica_conteudo": "Publique tutorial rápido de penteado, antes/depois e versão para cabelo cacheado.",
        "hashtags": ["#penteados", "#penteadocriativo", "#cabelos", "#hairtok"],
        "fonte_url": "https://www.tiktok.com/discover/penteados-tend%C3%AAncia-de-2026-de-bf",
    },
    {
        "termo": "Unhas decoradas e vampíricas",
        "categoria": "Beleza",
        "prioridade": 8.7,
        "sinal_publico": "Tema de unhas aparece simultaneamente nos sinais públicos atuais de Pinterest e TikTok.",
        "dica_conteudo": "Mostre a aplicação em três etapas e finalize com close da textura e do brilho.",
        "hashtags": ["#unhasdecoradas", "#nailart", "#nailtok", "#unhasvampiricas"],
        "fonte_url": "https://br.pinterest.com/today/",
    },
    {
        "termo": "Looks com brilho, metalizados e rendas",
        "categoria": "Moda",
        "prioridade": 8.6,
        "sinal_publico": "Buscas públicas de primavera/verão destacam metalizados e rendas como direções de estilo.",
        "dica_conteudo": "Use o formato ‘uma peça, três ocasiões’ para demonstrar versatilidade.",
        "hashtags": ["#metalizado", "#rendafashion", "#lookbrilho", "#styletok"],
        "fonte_url": "https://www.tiktok.com/discover/tendencias-primavera-verano-2026-en-brasil",
    },
    {
        "termo": "Outfit check Brasil",
        "categoria": "Moda",
        "prioridade": 8.2,
        "sinal_publico": "Conteúdos públicos de moda no Brasil destacam outfit checks e peças amarelas.",
        "dica_conteudo": "Grave três outfit checks de 7 segundos com texto na tela e preço da composição.",
        "hashtags": ["#outfitcheck", "#lookbrasil", "#modabrasil", "#achadinhos"],
        "fonte_url": "https://www.tiktok.com/discover/summer-fashion-trends-in-brazil",
    },
    {
        "termo": "Organização de quarto e apartamento pequeno",
        "categoria": "Casa",
        "prioridade": 8.0,
        "sinal_publico": "Organização e quartos pequenos aparecem como temas atuais nas buscas públicas de inspiração.",
        "dica_conteudo": "Faça transformação antes/depois com três produtos e custo total na tela.",
        "hashtags": ["#organizacao", "#quartopequeno", "#apartamentopequeno", "#casatok"],
        "fonte_url": "https://br.pinterest.com/today/",
    },
]


def obter_tendencias_tiktok(forcar_atualizacao: bool = False) -> List[Dict[str, Any]]:
    """Retorna sinais públicos recentes sem simular métricas de viralidade."""
    if not forcar_atualizacao and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as arquivo:
                cache_data = json.load(arquivo)
            if cache_data.get("data_referencia") == DATA_REFERENCIA:
                dados = cache_data.get("dados", [])
                if isinstance(dados, list) and dados:
                    logger.info("TikTok Trends: dados atuais do cache")
                    return dados
        except (OSError, json.JSONDecodeError, TypeError) as erro:
            logger.error("Erro ao ler cache do TikTok: %s", erro)

    dados_finais = []
    for item in SINAIS_PUBLICOS:
        registro = dict(item)
        registro.update(
            {
                "status": "Sinal público",
                "prioridade_editorial": item["prioridade"],
                "metrica_verificada": False,
                "fonte": "TikTok Discover / Creative Center + sinais públicos",
                "fonte_central": FONTE_CENTRAL,
                "origem_coleta": "pagina_publica_sem_login",
                "data_referencia": DATA_REFERENCIA,
                "atualizado": DATA_REFERENCIA,
            }
        )
        dados_finais.append(registro)

    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as arquivo:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "data_referencia": DATA_REFERENCIA,
                    "dados": dados_finais,
                    "fonte": FONTE_CENTRAL,
                    "metrica_verificada": False,
                },
                arquivo,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as erro:
        logger.error("Erro ao salvar cache do TikTok: %s", erro)

    return dados_finais


def render_tiktok_dashboard():
    """Renderiza a seção do TikTok no Streamlit."""
    st.markdown("## 📱 Tendências TikTok — Sinais públicos atuais")
    st.caption(
        "Temas públicos observados para Brasil e primavera/verão 2026. "
        "A prioridade abaixo é editorial, não uma métrica oficial de alcance."
    )

    dados = obter_tendencias_tiktok()
    if not dados:
        st.warning("Nenhum dado do TikTok disponível no momento.")
        return

    df = pd.DataFrame(dados)
    df_grafico = df[["termo", "prioridade_editorial"]].set_index("termo")
    df_grafico.columns = ["Prioridade editorial"]

    tab_graf, tab_tabela = st.tabs(["📊 Prioridades de conteúdo", "📋 Grade detalhada"])
    with tab_graf:
        st.bar_chart(df_grafico, use_container_width=True)
        st.info(
            "Os rankings oficiais por país do TikTok Creative Center podem exigir login "
            "ou filtros interativos; por isso não são tratados como métricas nesta tela."
        )

    with tab_tabela:
        st.dataframe(
            df[
                [
                    "termo",
                    "categoria",
                    "status",
                    "prioridade_editorial",
                    "sinal_publico",
                    "dica_conteudo",
                    "data_referencia",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(f"Fonte central: {FONTE_CENTRAL} | Referência: {DATA_REFERENCIA}")
