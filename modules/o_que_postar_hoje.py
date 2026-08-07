#!/usr/bin/env python3
"""
O Que Postar Hoje — Dados Reais Inteligentes (v2)
==================================================
Módulo que coleta dados REAIS de tendências do dia e os filtra/categoriza
inteligentemente para direcionar o conteúdo do usuário.

Princípios:
- NUNCA mostrar tragédias, crimes, política polêmica, acidentes ou conteúdo negativo
- PRIORIZAR tendências de moda, beleza, lifestyle, compras e entretenimento leve
- CLASSIFICAR cada trend por potencial comercial (Moda, Beleza, Casa, Games, etc.)
- GERAR sugestões de post específicas com hashtags e formato

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

# ============================================================
# FILTRO ANTI-NEGATIVO — Palavras-chave que NUNCA devem aparecer
# ============================================================
TERMOS_NEGATIVOS = [
    # Tragédias e desastres
    'ciclone', 'furacão', 'enchente', 'inundação', 'terremoto', 'tsunami',
    'incêndio', 'desabamento', ' deslizamento', 'bomba', 'tragédia',
    # Crimes e violência
    'estupro', 'assassinato', 'homicídio', 'latrocínio', 'roubo', 'assalto',
    'crime', 'prisão', 'preso', 'polícia', 'delegado', 'tribunal', 'júri',
    'julgamento', 'sentença', 'condenado', 'vítima', 'cadáver', 'corpo',
    # Política polêmica
    'lula', 'bolsonaro', 'câmara', 'senado', 'stj', 'stf', 'ministro',
    'impeachment', 'denúncia', 'corrupção', 'petralha', 'bolsonarista',
    # Acidentes e emergências
    'acidente', 'morte', 'mortos', 'feridos', 'atropelamento', 'capotamento',
    # Guerra e conflitos
    'guerra', 'ataque', 'bomba', 'míssil', 'invasão', 'conflito',
    # Saúde negativa
    'surto', 'epidemia', 'pandemia', 'doença terminal', 'câncer',
    # Clima severo
    'alerta', 'vendaval', 'temporal', 'severo', 'emergência',
    # Outros negativos
    'triste', 'lamentável', 'revolta', 'indignação', 'pânico', 'alerta máximo',
]

# ============================================================
# CATEGORIZAÇÃO COMERCIAL — Palavras-chave por nicho
# ============================================================
CATEGORIAS_COMERCIAIS = {
    '👗 Moda': {
        'palavras': ['tênis', 'moda', 'look', 'outfit', 'vestido', 'sapato', 'bolsa',
                     'relógio', 'óculos', 'acessório', 'camisa', 'calça', 'jaqueta',
                     'roupa', 'estilo', 'outono', 'inverno', 'verão', 'tendência'],
        'dica': 'Poste look do dia + produto da Shopee. Use hashtags #LookDoDia #ModaFeminina',
        'formato': 'Reels/Vídeo curto mostrando o look completo',
    },
    '💄 Beleza': {
        'palavras': ['make', 'maquiagem', 'unha', 'cabelo', 'progressiva', 'hidratação',
                     'skincare', 'perfume', 'canela', 'pele', 'rosa', 'botox', 'lábios',
                     'milrose', 'escova', 'pente', 'tratamento'],
        'dica': 'Antes/Depois + produto usado. Alto engajamento com tutorial.',
        'formato': 'Reels com transição antes/depois',
    },
    '🏠 Casa & Decoração': {
        'palavras': ['casa', 'decoração', 'papel de parede', 'sala', 'quarto', 'cozinha',
                     'vaso', 'quadro', 'almofada', 'luminária', 'organização', 'sapateira',
                     'travessa', 'cumeeira', 'janela', 'aluminio'],
        'dica': 'Transformação do ambiente + link para produto. Conteúdo que salva.',
        'formato': 'Carrossel ou Reels mostrando antes/depois do ambiente',
    },
    '🎮 Games & Tech': {
        'palavras': ['nintendo', 'ps5', 'switch', '3ds', 'notebook', 'tablet', 'desktop',
                     'game', 'videogame', 'controle', 'fobos', 'steam', 'playstation'],
        'dica': 'Review/Comparativo + link de compra. Conteúdo que converte direto.',
        'formato': 'Vídeo review ou carrossel de unboxing',
    },
    '🏋️ Esportes & Fitness': {
        'palavras': ['bicicleta', 'ergométrica', 'academia', 'treino', 'fitness',
                     'corrida', 'crossfit', 'saúde', 'bem-estar', 'moto', 'scooter',
                     'carabina', 'escapamento', 'cruze', 'automotivo'],
        'dica': 'Dica de treino/equipamento + produto da Shopee. Engaja muito com homens.',
        'formato': 'Reels com demonstração do equipamento',
    },
    '🧸 Brinquedos & Infantil': {
        'palavras': ['lego', 'brinquedo', 'fantasia', 'paquita', 'copa', 'figurinhas',
                     'infantil', 'criança', 'boneca', 'carrinho'],
        'dica': 'Unboxing + reação das crianças. Conteúdo viral por natureza.',
        'formato': 'Reels de unboxing com reação genuína',
    },
    '🍫 Alimentação & Casa': {
        'palavras': ['cacau', 'chocolate', 'chopp', 'fatiador', 'bolo', 'cenoura',
                     'microondas', 'micro-ondas', 'geladeira', 'freezer', 'ar condicionado',
                     'cortador', 'grama', 'liquidificador', 'panela'],
        'dica': 'Receita rápida usando o produto + link. Conteúdo compartilhável.',
        'formato': 'Reels de receita ou demonstração do eletrodoméstico',
    },
    '🎁 Presentes & Datas Especiais': {
        'palavras': ['dia dos pais', 'presente', 'kit', 'caixa', 'vale', 'especial',
                     'aniversário', 'data', 'comemorativa', 'namorados', 'natal'],
        'dica': 'Sugestão de presente com preço. Poste 2-3 semanas antes da data.',
        'formato': 'Carrossel com 3-5 opções de presente por faixa de preço',
    },
}

CATEGORIA_PADRAO = {
    'palavras': [],
    'dica': 'Conteúdo geral — conecte ao seu nicho com humor ou curiosidade.',
    'formato': 'Reels curto ou carrossel informativo',
}


def _classificar_trend(termo: str) -> Dict[str, str]:
    """Classifica uma trend por categoria comercial."""
    termo_lower = termo.lower()

    for categoria, dados in CATEGORIAS_COMERCIAIS.items():
        for palavra in dados['palavras']:
            if palavra in termo_lower:
                return {
                    'categoria': categoria,
                    'dica': dados['dica'],
                    'formato': dados['formato'],
                }

    return {
        'categoria': '🔥 Viral Geral',
        'dica': 'Conteúdo viral — poste rápido antes que esfrie. Use CTA para engajamento.',
        'formato': 'Reels de 15-30s ou post estático com pergunta',
    }


def _filtrar_negativo(termo: str) -> bool:
    """Retorna True se o termo contém conteúdo negativo (deve ser EXCLUÍDO)."""
    termo_lower = termo.lower()
    for palavra in TERMOS_NEGATIVOS:
        if palavra in termo_lower:
            return True
    return False


def _parse_trending_volume(text: str) -> int:
    """Extrai o número de buscas. Suporta inglês (1M+, 500K+) e português (1 mi+, 500 mil+).
    O Google usa \xa0 (non-breaking space) entre número e unidade."""
    text_norm = text.replace('\xa0', ' ')
    match_en = re.search(r'\b(\d+\.?\d*)\s*([KkMm])\+', text_norm)
    if match_en:
        num = float(match_en.group(1))
        suffix = match_en.group(2).upper()
        if suffix == 'M':
            return int(num * 1_000_000)
        elif suffix == 'K':
            return int(num * 1_000)
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


def _obter_google_trends_reais() -> List[Dict[str, Any]]:
    """Extrai trending searches REAIS do Google Trends Brasil via scraping.
    Aplica filtro anti-negativo e categorização comercial."""
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

            cell_1 = cells[1].get_text(' ', strip=True) if len(cells) > 1 else ''
            cell_2 = cells[2].get_text(' ', strip=True) if len(cells) > 2 else ''
            cell_3 = cells[3].get_text(' ', strip=True) if len(cells) > 3 else ''

            # Extrair termo limpo
            cell_1_norm = cell_1.replace('\xa0', ' ')
            termo_match = re.match(
                r'^([a-zA-ZÀ-ÿ0-9\s]+?)(?=\s*\d+\s*(?:[KkMm]|mi|mil)\+)', cell_1_norm
            )
            if not termo_match:
                continue

            termo = termo_match.group(1).strip()
            if not termo or len(termo) < 2:
                continue

            # FILTRO ANTI-NEGATIVO: pular tragédias, crimes, política polêmica
            if _filtrar_negativo(termo):
                logger.info(f"  🚫 Filtrado (negativo): {termo}")
                continue

            volume = _parse_trending_volume(cell_1)

            variacao = 0
            var_match = re.search(r'arrow_upward\s*([\d.]+)%', cell_2)
            if var_match:
                variacao = int(var_match.group(1).replace('.', '').replace(',', ''))
            else:
                variacao = _parse_variacao(cell_2)

            tempo = ''
            tempo_match = re.search(r'(\d+\s*(?:horas?|minutos?|dias?)\s*(?:atrás|ago))', cell_3, re.IGNORECASE)
            if tempo_match:
                tempo = tempo_match.group(1)
            else:
                tempo_match2 = re.search(r'(\d+\s*h\s*(?:atrás|ago))', cell_3, re.IGNORECASE)
                if tempo_match2:
                    tempo = tempo_match2.group(1)
                else:
                    tempo_match3 = re.search(r'há\s*(\d+\s*h?)', cell_3)
                    if tempo_match3:
                        tempo = tempo_match3.group(0)

            if termo.isdigit() or len(termo) < 3:
                continue

            # Categorizar por nicho comercial
            classificacao = _classificar_trend(termo)

            trends.append({
                'termo': termo,
                'volume_buscas': volume,
                'variacao_pct': variacao,
                'tempo': tempo,
                'categoria': classificacao['categoria'],
                'dica_post': classificacao['dica'],
                'formato_sugerido': classificacao['formato'],
                'fonte': 'Google Trends BR',
                'atualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
            })

            if len(trends) >= 25:
                break

    except Exception as e:
        logger.error(f"Erro ao buscar Google Trends: {e}")

    return trends


def _obter_google_news_destaques() -> List[Dict[str, Any]]:
    """Extrai headlines em destaque do Google News Brasil via RSS.
    Filtra conteúdo negativo e prioriza temas comerciais/lifestyle."""
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
            title_clean = re.sub(r'\s*-\s*[A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)*$', '', title).strip()

            if not title_clean or len(title_clean) < 5:
                continue

            # FILTRO ANTI-NEGATIVO
            if _filtrar_negativo(title_clean):
                continue

            # Priorizar notícias com potencial comercial/lifestyle
            classificacao = _classificar_trend(title_clean)

            pub_date = pub_date_tag.text if pub_date_tag else ''
            source = source_tag.text if source_tag else 'Google News'

            noticias.append({
                'termo': title_clean,
                'fonte_nome': source,
                'publicado': pub_date,
                'categoria': classificacao['categoria'],
                'dica_post': classificacao['dica'],
                'formato_sugerido': classificacao['formato'],
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
        for produto in termos_shopee:
            if produto in termo_lower or termo_lower in produto:
                cruzamentos.append({
                    'termo_trend': t['termo'],
                    'produto_relacionado': produto,
                    'volume_buscas': t.get('volume_buscas', 0),
                    'variacao_pct': t.get('variacao_pct', 0),
                    'categoria': t.get('categoria', 'Geral'),
                    'dica_post': t.get('dica_post', 'Poste sobre esse produto trendando'),
                    'formato_sugerido': t.get('formato_sugerido', 'Reels de review'),
                    'fonte': 'Cruzamento Trends + Shopee',
                    'atualizado': datetime.now().strftime('%d/%m/%Y %H:%M'),
                })

    return cruzamentos


def _cache_valido() -> bool:
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
    Filtra conteúdo negativo e categoriza por potencial comercial.
    """
    if not forcar_atualizacao and _cache_valido():
        dados = _carregar_cache()
        if dados:
            return dados

    logger.info("🔥 Coletando sugestões inteligentes para postar hoje...")

    # 1. Google Trends reais (com filtro anti-negativo)
    trends_reais = _obter_google_trends_reais()
    logger.info(f"  Google Trends: {len(trends_reais)} tendências comerciais")

    # 2. Google News destaques (com filtro anti-negativo)
    news_destaques = _obter_google_news_destaques()
    logger.info(f"  Google News: {len(news_destaques)} destaques positivos")

    # 3. Cruzamento com e-commerce
    cruzamentos = _cruzamento_ecommerce(trends_reais)
    logger.info(f"  Cruzamentos e-commerce: {len(cruzamentos)} oportunidades")

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
    st.caption("Tendências reais filtradas — sem tragédias, só conteúdo que vende e engaja")

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
            f"📊 {dados.get('total_trends', 0)} trends comerciais + "
            f"📰 {dados.get('total_news', 0)} notícias positivas + "
            f"🛒 {dados.get('total_oportunidades', 0)} oportunidades e-commerce"
        )

    st.markdown("---")

    # === SEÇÃO 1: TRENDING SEARCHES FILTRADAS E CATEGORIZADAS ===
    st.markdown("### 🔥 Tendências Comerciais do Dia")
    st.caption("Google Trends Brasil — filtrado para mostrar apenas tendências com potencial comercial. Categoria, dica de post e formato sugerido incluídos.")

    trends = dados.get('trends_google', [])
    if trends:
        # Top 5 destaques
        top_trends = sorted(trends, key=lambda x: x.get('volume_buscas', 0), reverse=True)[:5]
        cols = st.columns(min(5, len(top_trends)))
        for i, trend in enumerate(top_trends):
            with cols[i]:
                st.metric(
                    f"#{i+1} {trend['termo'][:20]}",
                    trend.get('volume_buscas', 0),
                    f"+{trend.get('variacao_pct', 0):,}%",
                )

        # Tabela completa com categoria e dica
        df_trends = []
        for idx, t in enumerate(trends, 1):
            df_trends.append({
                '#': idx,
                'O que estão buscando': t['termo'],
                'Categoria': t.get('categoria', 'Geral'),
                'Buscas': f"{t.get('volume_buscas', 0):,}".replace(',', '.'),
                'Variação': f"+{t.get('variacao_pct', 0):,}%".replace(',', '.'),
                'Quando começou': t.get('tempo', ''),
                '💡 Dica de Post': t.get('dica_post', ''),
                '📱 Formato': t.get('formato_sugerido', ''),
            })

        import pandas as pd
        df = pd.DataFrame(df_trends)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Nenhuma tendência comercial encontrada agora. Tentando novamente...")
        dados = obter_sugestoes_do_dia(forcar_atualizacao=True)
        trends = dados.get('trends_google', [])
        if trends:
            st.rerun()

    st.markdown("---")

    # === SEÇÃO 2: NOTÍCIAS POSITIVAS OPORTUNAS ===
    st.markdown("### 📰 Notícias com Potencial Comercial")
    st.caption("Headlines filtradas — apenas temas com potencial de conexão com produtos e lifestyle.")

    news = dados.get('news_destaques', [])
    if news:
        for n in news[:10]:
            with st.expander(f"{n.get('categoria', '📌')} {n['termo'][:60]}"):
                st.markdown(f"**Fonte:** {n.get('fonte_nome', 'Google News')}")
                st.markdown(f"**Publicado:** {n.get('publicado', '?')}")
                st.markdown(f"**💡 Como usar:** {n.get('dica_post', 'Conecte ao seu nicho')}")
                st.markdown(f"**📱 Formato sugerido:** {n.get('formato_sugerido', 'Reels ou carrossel')}")
    else:
        st.info("📰 Nenhuma notícia comercial encontrada hoje. Foque nas tendências acima.")

    st.markdown("---")

    # === SEÇÃO 3: OPORTUNIDADES E-COMMERCE ===
    st.markdown("### 🛒 Oportunidades de E-commerce (Trends × Shopee)")
    st.caption("Termos que estão trendando E são produtos da Shopee. Maior chance de viralizar e converter.")

    oportunidades = dados.get('oportunidades_ecommerce', [])
    if oportunidades:
        for opp in oportunidades:
            st.success(
                f"🔥 **{opp['termo_trend']}** → Produto Shopee: **{opp['produto_relacionado']}** "
                f"({opp.get('volume_buscas', 0):,} buscas, +{opp.get('variacao_pct', 0):,}% variação)\n"
                f"💡 {opp.get('dica_post', '')}"
            )
    else:
        st.info(
            "Nenhum cruzamento direto hoje. "
            "Dica: Use as tendências da tabela acima e conecte com os produtos da Grade de Descoberta."
        )
        for t in trends[:5]:
            st.markdown(f"- **{t['termo']}** — {t.get('volume_buscas', 0):,} buscas (+{t.get('variacao_pct', 0):,}%) — {t.get('categoria', '')}")

    st.markdown("---")
    st.caption("📊 Dados reais: Google Trends BR + Google News | Filtrado: sem tragédias, crimes ou política polêmica")
