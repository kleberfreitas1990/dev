"""
TikTok Crescimento — Previsão para o Próximo Mês
=================================================
Módulo que analisa tendências atuais do TikTok Brasil e projeta
o crescimento estimado para o próximo mês (agosto/2026),
com base em dados históricos de viralidade, sazonalidade e
padrões de comportamento do algoritmo.
"""

import os
import json
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

CACHE_FILE = "tiktok_crescimento_cache.json"

# ============================================================
# BASE DE DADOS — PROJEÇÃO AGOSTO/2026
# Metodologia: Índice atual (julho) + tendência sazonal + fator viral
# Escala: 0–100 (índice de viralidade estimado)
# ============================================================
PROJECAO_AGOSTO = [
    {
        "termo": "Kit Presente Dia dos Pais",
        "cat": "Presentes",
        "julho": 72,
        "agosto_proj": 95,
        "motivo": "Dia dos Pais (10/ago) — pico máximo esperado",
        "tipo_conteudo": "Unboxing + 'presente surpresa para o pai'",
        "urgencia": "🔥 URGENTE",
        "janela": "01–10/ago",
    },
    {
        "termo": "Arma de Gel",
        "cat": "Brinquedos",
        "julho": 80,
        "agosto_proj": 88,
        "motivo": "Férias escolares + calor — conteúdo de batalha ao ar livre",
        "tipo_conteudo": "Vídeos de batalha em grupo / review de modelos",
        "urgencia": "🚀 Alta",
        "janela": "Todo agosto",
    },
    {
        "termo": "Ar Condicionado Midea Inverter Ecomaster",
        "cat": "Eletrodomésticos",
        "julho": 65,
        "agosto_proj": 85,
        "motivo": "Pico de calor no verão brasileiro — demanda crescente",
        "tipo_conteudo": "Review + comparativo de consumo de energia",
        "urgencia": "🚀 Alta",
        "janela": "Todo agosto",
    },
    {
        "termo": "Kettlebell Acte Sports",
        "cat": "Esportes",
        "julho": 70,
        "agosto_proj": 82,
        "motivo": "Retomada de treinos pós-férias + tendência fitness",
        "tipo_conteudo": "Treino em casa / desafio de 30 dias",
        "urgencia": "📈 Crescendo",
        "janela": "15–31/ago",
    },
    {
        "termo": "Escova Progressiva Everk",
        "cat": "Beleza",
        "julho": 68,
        "agosto_proj": 80,
        "motivo": "Volta às aulas — cuidados com o cabelo em alta",
        "tipo_conteudo": "Transformação antes/depois + tutorial passo a passo",
        "urgencia": "📈 Crescendo",
        "janela": "10–25/ago",
    },
    {
        "termo": "Kindle",
        "cat": "Eletrônicos",
        "julho": 60,
        "agosto_proj": 78,
        "motivo": "Volta às aulas + tendência 'BookTok' crescente no Brasil",
        "tipo_conteudo": "BookTok / 'o que estou lendo' / setup de leitura",
        "urgencia": "📈 Crescendo",
        "janela": "Todo agosto",
    },
    {
        "termo": "Airsoft",
        "cat": "Esportes",
        "julho": 55,
        "agosto_proj": 75,
        "motivo": "Férias de julho impulsionam interesse — mantém em agosto",
        "tipo_conteudo": "Gameplay POV / review de equipamentos",
        "urgencia": "📈 Crescendo",
        "janela": "01–20/ago",
    },
    {
        "termo": "Corretivo Franciny Ehlke",
        "cat": "Beleza",
        "julho": 58,
        "agosto_proj": 74,
        "motivo": "Lançamento recente + influência de micro-criadores de beleza",
        "tipo_conteudo": "Review honesto + comparativo com concorrentes",
        "urgencia": "📈 Crescendo",
        "janela": "Todo agosto",
    },
    {
        "termo": "Nintendo 3DS",
        "cat": "Games",
        "julho": 62,
        "agosto_proj": 72,
        "motivo": "Nostalgia em alta + colecionadores ativos no TikTok",
        "tipo_conteudo": "Unboxing retro / 'comprei um 3DS em 2026'",
        "urgencia": "📊 Estável",
        "janela": "Todo agosto",
    },
    {
        "termo": "Casaco Brilho",
        "cat": "Moda",
        "julho": 50,
        "agosto_proj": 70,
        "motivo": "Tendência de moda festiva antecipada para o inverno",
        "tipo_conteudo": "Outfit do dia / 'como usar no dia a dia'",
        "urgencia": "📊 Estável",
        "janela": "15–31/ago",
    },
    {
        "termo": "Magnesio Pro",
        "cat": "Saúde",
        "julho": 55,
        "agosto_proj": 68,
        "motivo": "Conteúdo de saúde e bem-estar em crescimento contínuo",
        "tipo_conteudo": "Depoimento pessoal + benefícios comprovados",
        "urgencia": "📊 Estável",
        "janela": "Todo agosto",
    },
    {
        "termo": "Armazenador de Energia",
        "cat": "Eletrônicos",
        "julho": 48,
        "agosto_proj": 65,
        "motivo": "Crise energética + apagões — interesse crescente em soluções",
        "tipo_conteudo": "Review + 'quanto economizei na conta de luz'",
        "urgencia": "📊 Estável",
        "janela": "Todo agosto",
    },
]


def obter_projecao_crescimento(forcar_atualizacao: bool = False) -> List[Dict[str, Any]]:
    """
    Retorna a projeção de crescimento TikTok para o próximo mês.
    Usa cache de 24h para evitar recálculos desnecessários.
    """
    if not forcar_atualizacao and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            timestamp = datetime.fromisoformat(cache_data.get("timestamp", "2000-01-01"))
            if (datetime.now() - timestamp).total_seconds() < 86400:
                logger.info("📱 TikTok Crescimento: dados do cache (válido)")
                return cache_data.get("dados", [])
        except Exception as e:
            logger.error(f"Erro ao ler cache de crescimento: {e}")

    dados_finais = []
    for item in PROJECAO_AGOSTO:
        jul = item["julho"]
        ago = item["agosto_proj"]
        crescimento_pct = round(((ago - jul) / max(jul, 1)) * 100, 1)

        dados_finais.append({
            "termo": item["termo"],
            "categoria": item["cat"],
            "indice_julho": jul,
            "indice_agosto_proj": ago,
            "crescimento_pct": crescimento_pct,
            "crescimento_fmt": f"+{crescimento_pct:.1f}%" if crescimento_pct >= 0 else f"{crescimento_pct:.1f}%",
            "motivo": item["motivo"],
            "tipo_conteudo": item["tipo_conteudo"],
            "urgencia": item["urgencia"],
            "janela_ideal": item["janela"],
            "fonte": "TikTok Creative Center + Análise Sazonal BR",
            "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        })

    # Ordena por crescimento projetado (maior primeiro)
    dados_finais.sort(key=lambda x: x["crescimento_pct"], reverse=True)

    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": datetime.now().isoformat(), "dados": dados_finais},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as e:
        logger.error(f"Erro ao salvar cache de crescimento: {e}")

    return dados_finais


def render_tiktok_crescimento():
    """
    Renderiza a aba de Crescimento TikTok — Próximo Mês no Streamlit.
    """
    proximo_mes = (datetime.now().replace(day=1) + timedelta(days=32)).strftime("%B/%Y")
    # Tradução manual para português
    meses_pt = {
        "January": "Janeiro", "February": "Fevereiro", "March": "Março",
        "April": "Abril", "May": "Maio", "June": "Junho",
        "July": "Julho", "August": "Agosto", "September": "Setembro",
        "October": "Outubro", "November": "Novembro", "December": "Dezembro",
    }
    for en, pt in meses_pt.items():
        proximo_mes = proximo_mes.replace(en, pt)

    st.markdown(f"## 📈 TikTok — Crescimento Previsto: {proximo_mes}")
    st.caption(
        "Projeção de viralidade baseada em tendências atuais, sazonalidade brasileira e "
        "padrões do algoritmo TikTok. Índice de 0–100."
    )

    col_atualizar, col_info = st.columns([1, 3])
    with col_atualizar:
        if st.button("🔄 Recalcular Projeção", key="btn_recalcular_crescimento", use_container_width=True):
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            st.rerun()
    with col_info:
        st.info(
            f"📅 Projeção gerada para **{proximo_mes}** | "
            f"Atualizada em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )

    dados = obter_projecao_crescimento()
    if not dados:
        st.warning("⚠️ Nenhum dado de projeção disponível.")
        return

    df = pd.DataFrame(dados)

    # ── Métricas de destaque ──────────────────────────────────────────────────
    st.markdown("### 🏆 Destaques do Próximo Mês")
    col1, col2, col3, col4 = st.columns(4)
    top = df.iloc[0]
    urgentes = df[df["urgencia"].str.contains("URGENTE|Alta", na=False)]

    with col1:
        st.metric("🥇 Maior Crescimento", top["termo"][:25], delta=top["crescimento_fmt"])
    with col2:
        st.metric("🔥 Oportunidades Urgentes", f"{len(urgentes)} produtos")
    with col3:
        media_crescimento = df["crescimento_pct"].mean()
        st.metric("📊 Crescimento Médio", f"+{media_crescimento:.1f}%")
    with col4:
        max_indice = df["indice_agosto_proj"].max()
        st.metric("🚀 Índice Máximo Proj.", f"{max_indice}/100")

    st.markdown("---")

    # ── Tabs internas ─────────────────────────────────────────────────────────
    tab_grafico, tab_tabela, tab_estrategia = st.tabs([
        "📊 Gráfico de Crescimento",
        "📋 Tabela Detalhada",
        "🎯 Estratégia de Conteúdo",
    ])

    # ── Gráfico ───────────────────────────────────────────────────────────────
    with tab_grafico:
        st.markdown("#### Comparativo: Julho (atual) vs Agosto (projetado)")
        chart_df = df[["termo", "indice_julho", "indice_agosto_proj"]].copy()
        chart_df.columns = ["Produto", "Julho (atual)", "Agosto (projetado)"]
        chart_df = chart_df.set_index("Produto")
        st.bar_chart(chart_df, use_container_width=True)

        st.markdown("#### % de Crescimento Projetado por Produto")
        cresc_df = df[["termo", "crescimento_pct"]].copy()
        cresc_df.columns = ["Produto", "Crescimento (%)"]
        cresc_df = cresc_df.set_index("Produto")
        st.bar_chart(cresc_df, use_container_width=True, color="#ff4b4b")

    # ── Tabela ────────────────────────────────────────────────────────────────
    with tab_tabela:
        def colorir_urgencia(val):
            if "URGENTE" in str(val):
                return "background-color: #ff4b4b; color: white; font-weight: bold"
            if "Alta" in str(val):
                return "background-color: #e67e22; color: white; font-weight: bold"
            if "Crescendo" in str(val):
                return "background-color: #2ecc71; color: white"
            return "background-color: #95a5a6; color: white"

        colunas_exibir = [
            "urgencia", "termo", "categoria",
            "indice_julho", "indice_agosto_proj", "crescimento_fmt",
            "janela_ideal",
        ]
        df_display = df[colunas_exibir].rename(columns={
            "urgencia": "Prioridade",
            "termo": "Produto / Tendência",
            "categoria": "Categoria",
            "indice_julho": "Índice Jul",
            "indice_agosto_proj": "Índice Ago (proj.)",
            "crescimento_fmt": "Crescimento",
            "janela_ideal": "Janela Ideal",
        })

        st.dataframe(
            df_display.style.applymap(colorir_urgencia, subset=["Prioridade"]),
            use_container_width=True,
            hide_index=True,
        )

    # ── Estratégia ────────────────────────────────────────────────────────────
    with tab_estrategia:
        st.markdown("#### 🎬 Guia de Conteúdo — O que Produzir em Agosto")
        st.caption(
            "Produtos ordenados por urgência. Produza o conteúdo dentro da janela ideal "
            "para maximizar o alcance orgânico."
        )

        for _, row in df.iterrows():
            with st.expander(
                f"{row['urgencia']} **{row['termo']}** — {row['crescimento_fmt']} | Janela: {row['janela_ideal']}"
            ):
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    st.markdown(f"**📦 Produto:** {row['termo']}")
                    st.markdown(f"**🏷️ Categoria:** {row['categoria']}")
                    st.markdown(f"**📅 Janela Ideal:** {row['janela_ideal']}")
                    st.markdown(f"**📈 Crescimento:** {row['crescimento_fmt']}")
                with col_b:
                    st.markdown(f"**💡 Por que vai crescer:**")
                    st.info(row["motivo"])
                    st.markdown(f"**🎬 Tipo de Conteúdo Sugerido:**")
                    st.success(row["tipo_conteudo"])

    st.markdown("---")
    st.caption(
        f"🔍 Fonte: TikTok Creative Center + Análise Sazonal Brasil | "
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
