#!/usr/bin/env python3
"""
O Que Postar Hoje — Dados Reais Automáticos
============================================
Módulo que coleta dados REAIS de tendências do dia para sugerir
o que postar hoje nas redes sociais.

Fontes:
- Google Trends Brasil (via scraping do HTML renderizado)
- Google News Brasil (RSS)
- Termos de e-commerce do TERMOS_REAIS_SHOPEE (cruzamento)

Atualizado automaticamente a cada acesso (cache de 4h).
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CACHE_FILE = "o_que_postar_hoje_cache.json"
CACHE_TTL_HORAS = 4  # Cache válido por 4 horas

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}


def _parse_trending_volume(text: str) -> int:
    """Extrai o número de buscas. Suporta inglês (1M+, 500K+) e português (1 mi+, 500 mil+).
    O Google usa \xa0 (non-breaking space) entre número e unidade."""
    # Normalizar non-breaking spaces
    text_norm = text.replace('\xa0', ' ')
    # Inglês: 1M+ ou 500K+
    match_en = re.search(r'\b(\d+\.?\d*)\s*([KkMm])\+', text_norm)
    if match_en:
        num = float(match_en.group(1))
        suffix = match_en.group(2).upper()
        if suffix == 'M':
            return int(num * 1_000_000)
        elif suffix == 'K':
            return int(num * 1_000)
    # Português: 1 mi+ ou 500 mil+
    match_pt = re.search(r'\b(\d+\.?\d*)\s*(mi|mil)\+', text_norm, re.IGNORECASE)
    if match_pt:
        num = float(match_pt.group(1))
        suffix = match_pt.group(2).lower()
        if suffix == 'mi':
            return int(num * 1_000_000)
        else:
            return int(num * 1_000)
    return 0


def _parse_variacao(text: str) -> int:
    """Extrai a variação percentual de uma string tipo '+1,000%' ou '+1.000%'."""
    match = re.search(r'([\d.,]+)%', text)
    if match:
        return int(match.group(1).replace(',', '').replace('.', ''))
    return 0


def _parse_tempo(text: str) -> str:
    """Extrai o tempo relativo de uma string tipo '13 hours ago'."""
    match = re.search(r'(\d+\s*(?:hours?|minutes?|days?)\s*ago)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return text[:20]


def _obter_google_trends_reais() -> List[Dict[str, Any]]:
    """Extrai trending searches REAIS do Google Trends Brasil via scraping."""
    trends = []
    try:
        url = 'https://trends.google.com/trending?geo=BR'
        r = requests.get(url, timeout=20, headers=HEADERS)
        if r.status_code != 200:
            logger.warning(f"Google Trends retornou {r.status_code}")
            return trends

        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            # Coluna 1 (índice 1): contém o termo + volume + status
            cell_1 = cells[1].get_text(' ', strip=True) if len(cells) > 1 else ''
            # Coluna 2 (índice 2): contém volume e variação
            cell_2 = cells[2].get_text(' ', strip=True) if len(cells) > 2 else ''
            # Coluna 3 (índice 3): contém tempo
            cell_3 = cells[3].get_text(' ', strip=True) if len(cells) > 3 else ''

            # Extrair termo limpo - pegar tudo antes do padrão de volume
            # Formatos: "fortaleza x palmeiras 1M+ searches..." ou "cruzeiro 500 mil+ pesquisas..."
            # Normalizar non-breaking spaces
            cell_1_norm = cell_1.replace('\xa0', ' ')
            termo_match = re.match(
                r'^([a-zA-ZÀ-ÿ0-9\s]+?)(?=\s*\d+\s*(?:[KkMm]|mi|mil)\+)', cell_1_norm
            )
            if not termo_match:
                continue

            termo = termo_match.group(1).strip()
            if not termo or len(termo) < 2:
                continue

            volume = _parse_trending_volume(cell_1)

            # Variacao vem da cell_2, que tem formato "1M+ arrow_upward 1.000%"
            variacao = 0
            var_match = re.search(r'arrow_upward\s*([\d.]+)%', cell_2)
            if var_match:
                variacao = int(var_match.group(1).replace('.', '').replace(',', ''))
            else:
                variacao = _parse_variacao(cell_2)

            # Tempo da cell_3: "há 13 horas trending_up Ativa"
            tempo = ''
            tempo_match = re.search(r'(\d+\s*(?:horas?|minutos?|dias?)\s*(?:atrás|ago))', cell_3, re.IGNORECASE)
            if tempo_match:
                tempo = tempo_match.group(1)
            else:
                tempo_match2 = re.search(r'(\d+\s*h\s*(?:atrás|ago))', cell_3, re.IGNORECASE)
                if tempo_match2:
                    tempo = tempo_match2.group(1)
                else:
                    # Fallback: pegar "há X h"
                    tempo_match3 = re.search(r'há\s*(\d+\s*h?)', cell_3)
                    if tempo_match3:
                        tempo = tempo_match3.group(0)

            # Filtrar termos muito genéricos ou números puros
            if termo.isdigit() or len(termo) < 3:
                continue

            trends.append({
                'termo': termo,
                'volume_buscas': volume,
                'variacao_pct': variacao,
                'tempo': tempo,
                'fonte': 'Google Trends BR',
                'atualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
            })

            if len(trends) >= 25:
                break

    except Exception as e:
        logger.error(f"Erro ao buscar Google Trends: {e}")

    return trends


def _obter_google_news_destaques() -> List[Dict[str, Any]]:
    """Extrai headlines em destaque do Google News Brasil via RSS."""
    noticias = []
    try:
        url = 'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=pt-BR&gl=BR&ceid=BR:pt-150'
        r = requests.get(url, timeout=15, headers=HEADERS)
        if r.status_code != 200:
            return noticias

        soup = BeautifulSoup(r.text, 'lxml-xml')
        items = soup.find_all('item')[:20]

        for item in items:
            title_tag = item.find('title')
            pub_date_tag = item.find('pubDate')
            source_tag = item.find('source')

            title = title_tag.text if title_tag else ''
            # Remover nome da fonte do título (ex: "Título - Fonte")
            title_clean = re.sub(r'\s*-\s*[A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)*$', '', title).strip()

            if not title_clean or len(title_clean) < 5:
                continue

            pub_date = pub_date_tag.text if pub_date_tag else ''
            source = source_tag.text if source_tag else 'Google News'

            noticias.append({
                'termo': title_clean,
                'fonte_nome': source,
                'publicado': pub_date,
                'fonte': 'Google News BR',
                'atualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
            })

    except Exception as e:
        logger.error(f"Erro ao buscar Google News: {e}")

    return noticias


def _cruzamento_ecommerce(termos_trends: List[Dict]) -> List[Dict[str, Any]]:
    """
    Cruza os termos do Google Trends com a lista de produtos Shopee
    para encontrar oportunidades de e-commerce.
    """
    try:
        from modules.shopee import TERMOS_REAIS_SHOPEE
        termos_shopee = [t.lower() for t in TERMOS_REAIS_SHOPEE]
    except Exception:
        return []

    cruzamentos = []
    for t in termos_trends:
        termo_lower = t['termo'].lower()
        # Verificar se o termo trend tem relação com algum produto Shopee
        for produto in termos_shopee:
            if produto in termo_lower or termo_lower in produto:
                cruzamentos.append({
                    'termo_trend': t['termo'],
                    'produto_relacionado': produto,
                    'volume_buscas': t.get('volume_buscas', 0),
                    'variacao_pct': t.get('variacao_pct', 0),
                    'fonte': 'Cruzamento Trends + Shopee',
                    'atualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
                })

    return cruzamentos


def _cache_valido() -> bool:
    """Verifica se o cache está válido."""
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        timestamp = datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))
        return (datetime.now() - timestamp) < timedelta(hours=CACHE_TTL_HORAS)
    except Exception:
        return False


def _salvar_cache(dados: Dict):
    """Salva os dados no cache."""
    cache = {
        'timestamp': datetime.now().isoformat(),
        'data': datetime.now().strftime('%Y-%m-%d'),
        'dados': dados,
    }
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar cache: {e}")


def _carregar_cache() -> Optional[Dict]:
    """Carrega dados do cache."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        return cache.get('dados')
    except Exception:
        return None


def obter_sugestoes_do_dia(forcar_atualizacao: bool = False) -> Dict[str, Any]:
    """
    Retorna sugestões do dia para postar nas redes sociais.
    Dados reais do Google Trends, Google News e cruzamento com Shopee.
    """
    if not forcar_atualizacao and _cache_valido():
        dados = _carregar_cache()
        if dados:
            return dados

    logger.info("🔥 Coletando sugestões reais para postar hoje...")

    # 1. Google Trends reais
    trends_reais = _obter_google_trends_reais()
    logger.info(f"  Google Trends: {len(trends_reais)} tendências reais")

    # 2. Google News destaques
    news_destaques = _obter_google_news_destaques()
    logger.info(f"  Google News: {len(news_destaques)} destaques")

    # 3. Cruzamento com e-commerce
    cruzamentos = _cruzamento_ecommerce(trends_reais)
    logger.info(f"  Cruzamentos e-commerce: {len(cruzamentos)} oportunidades")

    # Montar payload
    resultado = {
        'data': datetime.now().strftime('%d/%m/%Y'),
        'hora_geracao': datetime.now().strftime('%H:%M'),
        'trends_google': trends_reais,
        'news_destaques': news_destaques,
        'oportunidades_ecommerce': cruzamentos,
        'total_trends': len(trends_reais),
        'total_news': len(news_destaques),
        'total_oportunidades': len(cruzamentos),
    }

    _salvar_cache(resultado)
    return resultado


def render_o_que_postar_hoje():
    """Renderiza a seção 'O que Postar Hoje' no Streamlit."""
    import streamlit as st

    st.markdown("## 🎯 O Que Postar Hoje")

    col_atualizar, col_info = st.columns([1, 3])
    with col_atualizar:
        if st.button("🔄 Atualizar Agora", key="btn_atualizar_postar", use_container_width=True):
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            st.rerun()
    with col_info:
        dados = obter_sugestoes_do_dia()
        st.info(
            f"📅 {dados.get('data', '?')} às {dados.get('hora_geracao', '?')} | "
            f"📊 {dados.get('total_trends', 0)} trends + "
            f"📰 {dados.get('total_news', 0)} notícias + "
            f"🛒 {dados.get('total_oportunidades', 0)} oportunidades e-commerce"
        )

    st.markdown("---")

    # === SEÇÃO 1: TRENDING SEARCHES DO GOOGLE (O que o Brasil está buscando agora) ===
    st.markdown("### 🔥 O Brasil Está Buscando Isso Agora")
    st.caption("Trending searches em tempo real do Google Trends Brasil. Poste sobre esses temas para pegar o algoritmo.")

    trends = dados.get('trends_google', [])
    if trends:
        # Top 5 destaques
        top_trends = sorted(trends, key=lambda x: x.get('volume_buscas', 0), reverse=True)[:5]
        cols = st.columns(min(5, len(top_trends)))
        for i, trend in enumerate(top_trends):
            with cols[i]:
                st.metric(
                    f"#{i+1} {trend['termo'][:25]}",
                    trend.get('volume_buscas', 0),
                    f"+{trend.get('variacao_pct', 0):,}%",
                )

        # Tabela completa
        df_trends = []
        for idx, t in enumerate(trends, 1):
            df_trends.append({
                '#': idx,
                'O que estão buscando': t['termo'],
                'Buscas': f"{t.get('volume_buscas', 0):,}".replace(',', '.'),
                'Variação': f"+{t.get('variacao_pct', 0):,}%".replace(',', '.'),
                'Quando começou': t.get('tempo', ''),
                'Dica de Post': _gerar_dica_post(t['termo']),
            })

        import pandas as pd
        df = pd.DataFrame(df_trends)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Não foi possível obter dados do Google Trends agora. Tentando novamente...")
        # Tentar novamente com flag
        dados = obter_sugestoes_do_dia(forcar_atualizacao=True)
        trends = dados.get('trends_google', [])
        if trends:
            st.rerun()

    st.markdown("---")

    # === SEÇÃO 2: NOTÍCIAS EM DESTAQUE (Para criar conteúdo oportuno) ===
    st.markdown("### 📰 Notícias em Destaque (Conteúdo Oportuno)")
    st.caption("Headlines do Google News Brasil. Crie conteúdo conectando esses temas aos seus produtos.")

    news = dados.get('news_destaques', [])
    if news:
        for n in news[:10]:
            with st.expander(f"📌 {n['termo'][:60]}"):
                st.markdown(f"**Fonte:** {n.get('fonte_nome', 'Google News')}")
                st.markdown(f"**Publicado:** {n.get('publicado', '?')}")
                st.markdown(f"**💡 Como usar no post:** Crie um post conectando esse assunto atual aos seus produtos em alta. Use hashtags relacionadas para pegar o alcance orgânico.")
    else:
        st.warning("⚠️ Sem notícias disponíveis no momento.")

    st.markdown("---")

    # === SEÇÃO 3: OPORTUNIDADES E-COMMERCE (Trends + Produtos Shopee) ===
    st.markdown("### 🛒 Oportunidades de E-commerce (Trends × Shopee)")
    st.caption("Termos que estão trendando E são produtos da Shopee. Esses são os posts com maior chance de viralizar e converter.")

    oportunidades = dados.get('oportunidades_ecommerce', [])
    if oportunidades:
        for opp in oportunidades:
            st.success(
                f"🔥 **{opp['termo_trend']}** → Produto Shopee: **{opp['produto_relacionado']}** "
                f"({opp.get('volume_buscas', 0):,} buscas, +{opp.get('variacao_pct', 0):,}% variação)"
            )
    else:
        # Gerar sugestões baseadas nos trends + produtos Shopee
        st.info(
            "Nenhum cruzamento direto encontrado hoje. "
            "Dica: Use os trending topics da seção acima e conecte com os produtos da Grade de Descoberta."
        )
        # Mostrar os top trends como sugestões gerais
        for t in trends[:5]:
            st.markdown(f"- **{t['termo']}** — {t.get('volume_buscas', 0):,} buscas (+{t.get('variacao_pct', 0):,}%)")

    st.markdown("---")
    st.caption("📊 Dados em tempo real: Google Trends Brasil + Google News | Atualizado a cada 4h")


def _gerar_dica_post(termo: str) -> str:
    """Gera uma dica rápida de como postar sobre o termo."""
    termo_lower = termo.lower()

    # Esportes
    if any(kw in termo_lower for kw in ['copa', 'futebol', 'jogo', 'x ', ' vs ', 'campeonato', 'libertadores']):
        return "Poste 'previsão do jogo' ou 'onde assistir' — engajamento garantido"
    # Política
    if any(kw in termo_lower for kw in ['lula', 'bolsonaro', 'governo', 'senado', 'câmara', 'ministro']):
        return "Conteúdo político viraliza — poste opinião + chamada para debate"
    # Economia
    if any(kw in termo_lower for kw in ['selic', 'salário', 'pis', 'pasep', 'inflação', 'bolsa']):
        return "Finanças pessoais + link para produto — 'como economizar com X'"
    # Entretenimento
    if any(kw in termo_lower for kw in ['novela', 'show', 'filme', 'série', 'drama', 'reality']):
        return "Meme + opinião — conecte ao produto com humor"
    # Tecnologia
    if any(kw in termo_lower for kw in ['iphone', 'samsung', 'notebook', 'tablet', 'tech']):
        return "Review comparativo + link de compra — conteúdo que converte"
    # Beleza/Moda
    if any(kw in termo_lower for kw in ['make', 'unha', 'cabelo', 'look', 'outfit', 'moda']):
        return "Tutorial/transformação + produto usado — alto engajamento"

    return "Poste sobre esse tema quente + conecte com seu nicho"
