"""TikTok Crescimento — planejamento editorial para setembro de 2026.

Os índices deste módulo são prioridades editoriais internas baseadas em sinais
públicos e sazonalidade brasileira. Eles não são métricas oficiais de alcance,
visualizações ou viralidade do TikTok.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

CACHE_FILE = "tiktok_crescimento_cache.json"
DATA_REFERENCIA = "2026-08-11"

# Índices internos de prioridade editorial, escala 0–100.
PROJECAO_SETEMBRO = [
    {
        "termo": "Vestido Floral Primavera",
        "cat": "Moda",
        "agosto": 72,
        "setembro_proj": 95,
        "motivo": "Início da primavera em 22/09 e sinais públicos de moda primavera/verão no Brasil.",
        "tipo_conteudo": "Transição de look de inverno para vestido floral, com três combinações e preço na tela.",
        "urgencia": "🔥 URGENTE",
        "janela": "08–22/set",
    },
    {
        "termo": "Cores Pastel e Azul Claro",
        "cat": "Moda",
        "agosto": 80,
        "setembro_proj": 94,
        "motivo": "Sinais públicos destacam azul claro, amarelo manteiga, pistache, rosa bebê e lavanda.",
        "tipo_conteudo": "Compare cinco combinações pastel usando uma mesma peça-chave.",
        "urgencia": "🚀 Alta",
        "janela": "01–30/set",
    },
    {
        "termo": "Penteados Diferentões",
        "cat": "Beleza",
        "agosto": 70,
        "setembro_proj": 90,
        "motivo": "Penteados aparecem entre os sinais públicos atuais do Pinterest e do TikTok Discover.",
        "tipo_conteudo": "Tutorial rápido, antes/depois e uma versão para cabelo cacheado.",
        "urgencia": "📈 Crescendo",
        "janela": "01–30/set",
    },
    {
        "termo": "Unhas Decoradas e Vampíricas",
        "cat": "Beleza",
        "agosto": 68,
        "setembro_proj": 88,
        "motivo": "Unhas decoradas e vampíricas aparecem como temas visuais recentes em Pinterest e TikTok.",
        "tipo_conteudo": "Aplicação em três etapas com close da textura, do brilho e do acabamento.",
        "urgencia": "📈 Crescendo",
        "janela": "01–22/set",
    },
    {
        "termo": "BookTok e Luz de Leitura",
        "cat": "Lifestyle",
        "agosto": 60,
        "setembro_proj": 82,
        "motivo": "Conteúdo de leitura e organização de estudos funciona como pauta de rotina e volta às atividades.",
        "tipo_conteudo": "Setup de leitura, ‘o que estou lendo’ e teste de luz de leitura portátil.",
        "urgencia": "📈 Crescendo",
        "janela": "01–15/set",
    },
    {
        "termo": "Outfit Check Brasil",
        "cat": "Moda",
        "agosto": 55,
        "setembro_proj": 80,
        "motivo": "Buscas públicas de moda no Brasil destacam outfit checks e referências de estilo brasileiro.",
        "tipo_conteudo": "Três outfit checks de sete segundos, com texto na tela e valor da composição.",
        "urgencia": "📈 Crescendo",
        "janela": "01–07/set",
    },
    {
        "termo": "Metalizados e Rendas",
        "cat": "Moda",
        "agosto": 50,
        "setembro_proj": 78,
        "motivo": "Sinais públicos de primavera/verão destacam texturas metalizadas e rendas.",
        "tipo_conteudo": "Uma peça, três ocasiões: casual, trabalho e evento.",
        "urgencia": "📊 Estável",
        "janela": "15–30/set",
    },
    {
        "termo": "Quarto Estilo Jardim",
        "cat": "Casa",
        "agosto": 48,
        "setembro_proj": 76,
        "motivo": "Quartos estilo jardim e organização de espaços pequenos aparecem nos sinais atuais do Pinterest.",
        "tipo_conteudo": "Transformação antes/depois com três produtos e custo total na tela.",
        "urgencia": "📊 Estável",
        "janela": "15–30/set",
    },
]


def obter_projecao_crescimento(forcar_atualizacao: bool = False) -> List[Dict[str, Any]]:
    """Retorna a prioridade editorial projetada para setembro de 2026."""
    if not forcar_atualizacao and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as arquivo:
                cache_data = json.load(arquivo)
            if cache_data.get("data_referencia") == DATA_REFERENCIA:
                dados = cache_data.get("dados", [])
                if isinstance(dados, list) and dados:
                    logger.info("TikTok Crescimento: cache atual de setembro")
                    return dados
        except (OSError, json.JSONDecodeError, TypeError) as erro:
            logger.error("Erro ao ler cache de crescimento do TikTok: %s", erro)

    dados_finais: List[Dict[str, Any]] = []
    for item in PROJECAO_SETEMBRO:
        agosto = item["agosto"]
        setembro = item["setembro_proj"]
        crescimento_pct = round(((setembro - agosto) / max(agosto, 1)) * 100, 1)
        dados_finais.append(
            {
                "termo": item["termo"],
                "categoria": item["cat"],
                "indice_agosto": agosto,
                "indice_setembro_proj": setembro,
                "crescimento_pct": crescimento_pct,
                "crescimento_fmt": f"+{crescimento_pct:.1f}%",
                "motivo": item["motivo"],
                "tipo_conteudo": item["tipo_conteudo"],
                "urgencia": item["urgencia"],
                "janela_ideal": item["janela"],
                "fonte": "TikTok Discover / Creative Center + Análise Sazonal Brasil",
                "fonte_url": "https://ads.tiktok.com/creative/creativeCenter/trends",
                "metrica_verificada": False,
                "tipo_indice": "prioridade_editorial",
                "data_referencia": DATA_REFERENCIA,
                "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
        )

    dados_finais.sort(key=lambda item: item["crescimento_pct"], reverse=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as arquivo:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "data_referencia": DATA_REFERENCIA,
                    "mes_alvo": "09/2026",
                    "metrica_verificada": False,
                    "dados": dados_finais,
                },
                arquivo,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as erro:
        logger.error("Erro ao salvar cache de crescimento do TikTok: %s", erro)

    return dados_finais


def render_tiktok_crescimento():
    """Renderiza a aba de crescimento editorial do TikTok para o próximo mês."""
    proximo_mes = (datetime.now().replace(day=1) + timedelta(days=32)).strftime("%B/%Y")
    meses_pt = {
        "January": "Janeiro", "February": "Fevereiro", "March": "Março",
        "April": "Abril", "May": "Maio", "June": "Junho",
        "July": "Julho", "August": "Agosto", "September": "Setembro",
        "October": "Outubro", "November": "Novembro", "December": "Dezembro",
    }
    for en, pt in meses_pt.items():
        proximo_mes = proximo_mes.replace(en, pt)

    st.markdown(f"## 📈 TikTok — Prioridades editoriais: {proximo_mes}")
    st.caption(
        "Prioridade editorial baseada em sinais públicos, sazonalidade brasileira e calendário de setembro. "
        "Não representa métrica oficial de alcance do TikTok."
    )

    col_atualizar, col_info = st.columns([1, 3])
    with col_atualizar:
        if st.button("🔄 Atualizar projeção", key="btn_recalcular_crescimento", use_container_width=True):
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            st.rerun()
    with col_info:
        st.info(
            f"📅 Planejamento para **{proximo_mes}** | "
            f"Referência dos sinais: {DATA_REFERENCIA}"
        )

    dados = obter_projecao_crescimento()
    if not dados:
        st.warning("⚠️ Nenhuma prioridade editorial disponível.")
        return

    df = pd.DataFrame(dados)
    st.markdown("### 🏆 Destaques do Próximo Mês")
    col1, col2, col3, col4 = st.columns(4)
    top = df.iloc[0]
    urgentes = df[df["urgencia"].str.contains("URGENTE|Alta", na=False)]

    with col1:
        st.metric("🥇 Maior prioridade", top["termo"][:25], delta=top["crescimento_fmt"])
    with col2:
        st.metric("🔥 Pautas prioritárias", f"{len(urgentes)} temas")
    with col3:
        st.metric("📊 Crescimento editorial médio", f"+{df['crescimento_pct'].mean():.1f}%")
    with col4:
        st.metric("🚀 Maior índice editorial", f"{df['indice_setembro_proj'].max()}/100")

    st.markdown("---")
    tab_grafico, tab_tabela, tab_estrategia = st.tabs([
        "📊 Prioridades", "📋 Tabela detalhada", "🎯 Estratégia de conteúdo"
    ])

    with tab_grafico:
        st.markdown("#### Comparativo: agosto (base editorial) vs setembro (prioridade)")
        chart_df = df[["termo", "indice_agosto", "indice_setembro_proj"]].set_index("termo")
        chart_df.columns = ["Agosto (base)", "Setembro (prioridade)"]
        st.bar_chart(chart_df, use_container_width=True)

    with tab_tabela:
        st.dataframe(
            df[
                [
                    "urgencia", "termo", "categoria", "indice_agosto",
                    "indice_setembro_proj", "crescimento_fmt", "janela_ideal",
                    "metrica_verificada",
                ]
            ].rename(
                columns={
                    "urgencia": "Prioridade",
                    "termo": "Tema",
                    "categoria": "Categoria",
                    "indice_agosto": "Índice Ago (base)",
                    "indice_setembro_proj": "Índice Set (prioridade)",
                    "crescimento_fmt": "Variação editorial",
                    "janela_ideal": "Janela ideal",
                    "metrica_verificada": "Métrica oficial",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    with tab_estrategia:
        st.markdown("#### 🎬 Guia de conteúdo — Setembro")
        st.caption("Priorize as pautas dentro da janela ideal e valide métricas nativas após publicar.")
        for _, row in df.iterrows():
            with st.expander(f"{row['urgencia']} **{row['termo']}** — {row['crescimento_fmt']} | {row['janela_ideal']}"):
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    st.markdown(f"**🏷️ Categoria:** {row['categoria']}")
                    st.markdown(f"**📅 Janela ideal:** {row['janela_ideal']}")
                    st.markdown(f"**📈 Variação editorial:** {row['crescimento_fmt']}")
                with col_b:
                    st.markdown("**💡 Fundamentação:**")
                    st.info(row["motivo"])
                    st.markdown("**🎬 Tipo de conteúdo:**")
                    st.success(row["tipo_conteudo"])

    st.markdown("---")
    st.caption(
        "🔍 Fonte: TikTok Discover / Creative Center + Análise Sazonal Brasil | "
        f"Referência: {DATA_REFERENCIA} | Métricas oficiais: não verificadas nesta sessão"
    )
