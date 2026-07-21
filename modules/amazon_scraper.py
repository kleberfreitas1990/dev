"""Coletor oficial de Best Sellers da Amazon Brasil.

O módulo só publica itens extraídos de ``https://www.amazon.com.br/gp/bestsellers/`` (com fallback parametrizado para evitar bloqueios de bot-detection).
Quando a página não está disponível, preserva exclusivamente um cache anterior que
já tenha sido validado como coleta oficial; listas curadas e métricas aleatórias
não são usadas como substitutos de dados da Amazon.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DIRETORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_CACHE_AMAZON = "amazon_trends.json"
CAMINHO_CACHE_AMAZON = os.path.join(DIRETORIO_RAIZ, ARQUIVO_CACHE_AMAZON)

URL_BESTSELLERS_AMAZON = "https://www.amazon.com.br/gp/bestsellers/"
FONTE_AMAZON = "Amazon Bestsellers"
ORIGEM_COLETA = "pagina_oficial"
VALIDADE_CACHE_HORAS = 12
TIMEOUT_REQUEST = 20
MAX_PRODUTOS = 30
MINIMO_PRODUTOS_VALIDOS = 3

HEADERS_AMAZON = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# Taxonomia exibida pela grade. A página geral de Best Sellers não fornece uma
# categoria individual por card, por isso a classificação é explicitamente
# marcada como interna e não como informação da Amazon.
MAPA_CATEGORIAS_AMAZON = {
    "meia": "Moda",
    "cueca": "Moda",
    "chinelo": "Moda",
    "mochila": "Moda",
    "livro": "Livros",
    "kindle": "Eletrônicos",
    "echo": "Eletrônicos",
    "fire tv": "Eletrônicos",
    "fone": "Eletrônicos",
    "headphone": "Eletrônicos",
    "ssd": "Eletrônicos",
    "smartphone": "Eletrônicos",
    "iphone": "Eletrônicos",
    "notebook": "Eletrônicos",
    "monitor": "Eletrônicos",
    "mouse": "Eletrônicos",
    "teclado": "Eletrônicos",
    "jogo": "Brinquedos e Jogos",
    "lego": "Brinquedos e Jogos",
    "creme": "Beleza e Cuidados Pessoais",
    "shampoo": "Beleza e Cuidados Pessoais",
    "perfume": "Beleza e Cuidados Pessoais",
    "café": "Casa e Cozinha",
    "cafeteira": "Casa e Cozinha",
    "panela": "Casa e Cozinha",
    "fritadeira": "Casa e Cozinha",
    "air fryer": "Casa e Cozinha",
}

# Slugs presentes no parâmetro de referência dos links do ranking Amazon.
# Quando disponíveis, representam a categoria da própria página de Best Sellers
# e têm precedência sobre a inferência por palavras do título.
MAPA_CATEGORIAS_URL_AMAZON = {
    "fashion": "Moda",
    "home": "Casa e Cozinha",
    "kitchen": "Casa e Cozinha",
    "electronics": "Eletrônicos",
    "books": "Livros",
    "toys": "Brinquedos e Jogos",
    "beauty": "Beleza e Cuidados Pessoais",
    "sports": "Esportes e Fitness",
    "automotive": "Automotivo",
    "office": "Papelaria e Escritório",
    "pet-supplies": "Pet Shop",
}


def _normalizar_texto(valor: str) -> str:
    """Normaliza texto para comparações de categoria."""
    sem_acentos = unicodedata.normalize("NFKD", str(valor)).encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"\s+", " ", sem_acentos).strip().lower()


def _inferir_categoria(nome: str) -> str:
    """Aplica a taxonomia interna da grade sem atribuí-la à fonte oficial."""
    nome_normalizado = _normalizar_texto(nome)
    for chave, categoria in MAPA_CATEGORIAS_AMAZON.items():
        if _normalizar_texto(chave) in nome_normalizado:
            return categoria
    return "Outros"


def _categoria_da_url_amazon(url_produto: str) -> str:
    """Extrai a categoria de Best Sellers codificada no link de referência da Amazon."""
    correspondencia = re.search(r"zg_bs_c_([a-z0-9-]+)_d_", url_produto.lower())
    if not correspondencia:
        return ""
    return MAPA_CATEGORIAS_URL_AMAZON.get(correspondencia.group(1), "")


def _carregar_cache_amazon() -> Dict[str, Any]:
    """Lê somente o envelope de cache compatível com a coleta oficial."""
    if not os.path.exists(CAMINHO_CACHE_AMAZON):
        return {}
    try:
        with open(CAMINHO_CACHE_AMAZON, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _cache_e_oficial(cache: Dict[str, Any]) -> bool:
    """Valida a proveniência e o formato de um cache antes de reutilizá-lo."""
    return (
        isinstance(cache.get("produtos"), dict)
        and cache.get("origem_coleta") == ORIGEM_COLETA
        and cache.get("url_fonte") == URL_BESTSELLERS_AMAZON
        and cache.get("status_coleta") == "sucesso"
    )


def _cache_recente(cache: Dict[str, Any]) -> bool:
    """Verifica se um cache oficial ainda está dentro do intervalo configurado (JSON + SQLite fallback)."""
    if _cache_e_oficial(cache):
        try:
            timestamp = datetime.fromisoformat(str(cache["timestamp"]))
            if (datetime.now() - timestamp).total_seconds() < VALIDADE_CACHE_HORAS * 3600:
                return True
        except (KeyError, TypeError, ValueError):
            pass
    # Fallback: verifica no SQLite
    try:
        from modules.database import amazon_cache_valido
        return amazon_cache_valido()
    except Exception:
        pass
    return False


def _normalizar_categorias_cache(produtos: Dict[str, Any]) -> Dict[str, Any]:
    """Atualiza em memória a taxonomia de itens já confirmados pela fonte oficial."""
    normalizados: Dict[str, Any] = {}
    for nome, dados in produtos.items():
        if not isinstance(dados, dict):
            continue
        produto = dict(dados)
        categoria_origem = _categoria_da_url_amazon(str(produto.get("url_produto", "")))
        produto["categoria"] = categoria_origem or _inferir_categoria(str(nome))
        produto["categoria_origem"] = categoria_origem or "Não informada na lista geral de Best Sellers"
        normalizados[str(nome)] = produto
    return normalizados


def _produtos_cache_oficial(cache: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retorna produtos oficiais com categorias normalizadas (JSON + SQLite fallback)."""
    if cache is not None and _cache_e_oficial(cache):
        produtos = cache.get("produtos", {})
        if isinstance(produtos, dict):
            return _normalizar_categorias_cache(produtos)
    # Fallback: tenta o SQLite
    try:
        from modules.database import obter_amazon_ciclo_atual
        db_data = obter_amazon_ciclo_atual()
        if db_data.get("produtos"):
            return _normalizar_categorias_cache(db_data["produtos"])
    except Exception:
        pass
    return {}


def _salvar_cache(produtos: Dict[str, Any]) -> bool:
    """Escreve o resultado oficial em JSON + SQLite (dual-write)."""
    payload = {
        "timestamp": datetime.now().isoformat(),
        "data": datetime.now().date().isoformat(),
        "total": len(produtos),
        "fonte": FONTE_AMAZON,
        "url_fonte": URL_BESTSELLERS_AMAZON,
        "origem_coleta": ORIGEM_COLETA,
        "status_coleta": "sucesso",
        "produtos": produtos,
    }
    # JSON (compatibilidade backward)
    caminho_tmp = f"{CAMINHO_CACHE_AMAZON}.tmp"
    json_ok = False
    try:
        with open(caminho_tmp, "w", encoding="utf-8") as arquivo:
            json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        os.replace(caminho_tmp, CAMINHO_CACHE_AMAZON)
        json_ok = True
    except OSError as erro:
        logger.error("Falha ao salvar JSON Amazon: %s", erro)
        try:
            if os.path.exists(caminho_tmp):
                os.remove(caminho_tmp)
        except OSError:
            pass
    # SQLite
    db_ok = False
    try:
        from modules.database import salvar_amazon_ciclo
        salvar_amazon_ciclo(produtos)
        db_ok = True
    except Exception as db_err:
        logger.warning(f"Falha ao salvar Amazon no SQLite: {db_err}")
    if json_ok or db_ok:
        logger.info("Cache oficial Amazon salvo com %d produtos.", len(produtos))
        return True
    return False


def _texto_limpo(elemento: Any) -> str:
    """Extrai e normaliza o texto visível de um elemento HTML."""
    if elemento is None:
        return ""
    return re.sub(r"\s+", " ", elemento.get_text(" ", strip=True)).strip()


def _extrair_titulo(card: Any) -> str:
    """Extrai o título do card, tolerando variações de classes versionadas pela Amazon."""
    seletor = (
        ".p13n-sc-truncate, "
        "[class*='p13n-sc-css-line-clamp-3'], "
        "[class*='p13n-sc-css-line-clamp-4'], "
        "[class*='line-clamp-3'], "
        "[class*='line-clamp-4']"
    )
    titulo = _texto_limpo(card.select_one(seletor))
    if titulo:
        return titulo

    imagem = card.select_one("img[alt]")
    return str(imagem.get("alt", "")).strip() if imagem else ""


def _extrair_posicao(card: Any, posicao_padrao: int) -> int:
    """Obtém a posição exibida pela página; usa a ordem do card apenas como contingência."""
    texto = _texto_limpo(card.select_one(".zg-bdg-text, [class*='zg-bdg-text'], [class*='rank']"))
    correspondencia = re.search(r"(\d+)", texto)
    return int(correspondencia.group(1)) if correspondencia else posicao_padrao


def _extrair_url_produto(card: Any) -> str:
    """Obtém o link canônico do produto quando a página o disponibiliza."""
    link = card.select_one("a[href*='/dp/'], a[href*='/gp/product/']")
    if link is None:
        return ""
    href = str(link.get("href", "")).strip()
    return urljoin("https://www.amazon.com.br", href) if href else ""


def _cards_bestsellers(soup: BeautifulSoup) -> List[Any]:
    """Localiza cards de produtos sem depender de uma única classe obfuscada."""
    seletores = [
        "#zg-ordered-list > li",
        ".zg-grid-general-faceout",
        ".p13n-sc-uncoverable-faceout",
        "[id^='p13n-asin-index-']",
    ]
    cards: List[Any] = []
    for seletor in seletores:
        for card in soup.select(seletor):
            if card not in cards:
                cards.append(card)
    return cards


# Lista de URLs da Amazon em ordem de preferência. A Amazon Brasil
# alterna entre rate-limitar URLs com e sem parâmetros de referência,
# portanto tentamos ambas antes de desistir.
_URLS_AMAZON_BESTSELLERS = [
    "https://www.amazon.com.br/gp/bestsellers/?ref_=zg_bs_nav_0",
    "https://www.amazon.com.br/gp/bestsellers/",
]


def _obter_resposta_bestsellers() -> Optional[requests.Response]:
    """Tenta obter uma resposta válida da página de Best Sellers, alternando URLs."""
    for url in _URLS_AMAZON_BESTSELLERS:
        try:
            resposta = requests.get(url, headers=HEADERS_AMAZON, timeout=TIMEOUT_REQUEST)
            resposta.raise_for_status()
            if resposta.status_code == 200 and len(resposta.text) >= 10000 and "Something went wrong" not in resposta.text:
                return resposta
            logger.warning("Amazon (%s) retornou página de erro; tentando próxima URL...", url)
        except requests.RequestException as erro:
            logger.warning("Amazon (%s) falhou: %s; tentando próxima URL...", url, erro)
            continue
    return None


def _raspar_pagina_oficial() -> Dict[str, Any]:
    """Consulta a página oficial e devolve somente produtos efetivamente exibidos nela."""
    resposta = _obter_resposta_bestsellers()
    if resposta is None:
        logger.warning("Todas as tentativas de acesso à Amazon Best Sellers falharam.")
        return {}

    soup = BeautifulSoup(resposta.text, "html.parser")
    produtos: Dict[str, Any] = {}
    for indice, card in enumerate(_cards_bestsellers(soup), start=1):
        nome = _extrair_titulo(card)
        if len(nome) < 6 or nome in produtos:
            continue

        posicao = _extrair_posicao(card, indice)
        url_produto = _extrair_url_produto(card)
        categoria_origem = _categoria_da_url_amazon(url_produto)
        categoria = categoria_origem or _inferir_categoria(nome)
        produtos[nome] = {
            "pins": 0,
            "pins_historico": 0,
            "crescimento": 0,
            "crescimento_real": False,
            "views_tiktok": 0,
            "resultados_ml": 0,
            "buscas_mes": 0,
            "buscas_historico": 0,
            "categoria": categoria,
            "categoria_origem": categoria_origem or "Não informada na lista geral de Best Sellers",
            "evento": "Produto listado em Best Sellers Amazon Brasil",
            "variacao": 0,
            "tendencia": "Mais vendido",
            "score": max(1, MAX_PRODUTOS - posicao + 1),
            "fonte": FONTE_AMAZON,
            "origem_coleta": ORIGEM_COLETA,
            "url_fonte": URL_BESTSELLERS_AMAZON,
            "url_produto": url_produto,
            "posicao_ranking": posicao,
            "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        if len(produtos) >= MAX_PRODUTOS:
            break

    if len(produtos) < MINIMO_PRODUTOS_VALIDOS:
        logger.warning(
            "A página oficial Amazon retornou apenas %d produtos válidos; resultado descartado.",
            len(produtos),
        )
        return {}

    logger.info("Página oficial Amazon: %d produtos validados.", len(produtos))
    return produtos


def capturar_bestsellers_amazon(forcar: bool = False) -> Dict[str, Any]:
    """Captura a lista oficial ou devolve exclusivamente um cache oficial validado."""
    cache_anterior = _carregar_cache_amazon()
    if not forcar and _cache_recente(cache_anterior):
        produtos_cache = _produtos_cache_oficial(cache_anterior)
        logger.info("Cache oficial Amazon válido: %d produtos.", len(produtos_cache))
        return produtos_cache

    produtos = _raspar_pagina_oficial()
    if produtos:
        _salvar_cache(produtos)
        return produtos

    produtos_cache = _produtos_cache_oficial(cache_anterior)
    if produtos_cache:
        logger.warning("Amazon indisponível; preservando %d produtos do último cache oficial validado.", len(produtos_cache))
        return produtos_cache

    logger.error("Nenhum Best Seller oficial da Amazon foi confirmado; a fonte será omitida da grade.")
    return {}


def obter_amazon_trends_cache() -> Dict[str, Any]:
    """Obtém o cache oficial Amazon e o atualiza quando necessário."""
    return capturar_bestsellers_amazon(forcar=False)


def obter_status_cache_amazon() -> Dict[str, Any]:
    """Expõe o estado do cache oficial para o painel de atualização."""
    cache = _carregar_cache_amazon()
    if not _cache_e_oficial(cache):
        return {
            "valido": False,
            "total": 0,
            "data_formatada": "Nenhuma coleta oficial validada",
            "fonte": "N/A",
        }

    try:
        timestamp = datetime.fromisoformat(str(cache["timestamp"]))
        data_formatada = timestamp.strftime("%d/%m/%Y %H:%M")
    except (KeyError, TypeError, ValueError):
        data_formatada = "Data inválida"

    return {
        "valido": _cache_recente(cache),
        "total": int(cache.get("total", len(cache.get("produtos", {})))),
        "data_formatada": data_formatada,
        "fonte": cache.get("fonte", FONTE_AMAZON),
    }
