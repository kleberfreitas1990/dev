"""Coletor oficial de tendências de pesquisa do Mercado Livre Brasil.

A coleta aceita somente os links publicados na seção ``Termos mais procurados``
da página oficial. Não há expansão por autocomplete, nem fallback estático: se a
fonte não estiver disponível, o módulo preserva apenas um cache já validado da
mesma página oficial.
"""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DIRETORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_CACHE_ML = "ml_trends_cache.json"
CAMINHO_CACHE_ML = os.path.join(DIRETORIO_RAIZ, ARQUIVO_CACHE_ML)

URL_TENDENCIAS_ML = "https://tendencias.mercadolivre.com.br/"
FONTE_ML = "Mercado Livre Trends"
ORIGEM_COLETA = "pagina_oficial"
VALIDADE_CACHE_HORAS = 6
TIMEOUT_REQUEST = 15
MAX_TERMOS = 40

HEADERS_PADRAO = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Taxonomia da grade. A categoria é derivada do termo; a página de tendências
# do Mercado Livre não publica uma categoria por item na lista de buscas.
MAPA_CATEGORIAS_ML = {
    "apple watch": "Eletrônicos",
    "smartwatch": "Eletrônicos",
    "iphone": "Eletrônicos",
    "ipad": "Eletrônicos",
    "celular": "Eletrônicos",
    "samsung": "Eletrônicos",
    "xiaomi": "Eletrônicos",
    "motorola": "Eletrônicos",
    "notebook": "Eletrônicos",
    "computador": "Eletrônicos",
    "tablet": "Eletrônicos",
    "monitor": "Eletrônicos",
    "fone": "Eletrônicos",
    "jbl": "Eletrônicos",
    "xdj": "Eletrônicos",
    "ar condicionado": "Eletrodomésticos",
    "microondas": "Eletrodomésticos",
    "fogao": "Eletrodomésticos",
    "freezer": "Eletrodomésticos",
    "geladeira": "Eletrodomésticos",
    "ventilador": "Eletrodomésticos",
    "cafeteira": "Casa e Cozinha",
    "guarda roupa": "Casa e Móveis",
    "painel para tv": "Casa e Móveis",
    "penteadeira": "Casa e Móveis",
    "bicicleta": "Esportes e Fitness",
    "tenis": "Moda",
    "ps4": "Games",
    "ps5": "Games",
    "xbox": "Games",
    "nintendo": "Games",
    "carro": "Veículos",
}


def _normalizar_texto(valor: str) -> str:
    """Normaliza texto para comparação, preservando o título original no dado salvo."""
    sem_acentos = unicodedata.normalize("NFKD", str(valor)).encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"\s+", " ", sem_acentos).strip().lower()


def _inferir_categoria(termo: str) -> str:
    """Classifica o termo na taxonomia da grade sem alegar categoria de origem."""
    termo_normalizado = _normalizar_texto(termo)
    for chave, categoria in MAPA_CATEGORIAS_ML.items():
        if _normalizar_texto(chave) in termo_normalizado:
            return categoria
    return "Outros"


def _ler_cache() -> Dict[str, Any]:
    """Lê o cache sem interromper a aplicação em caso de erro de arquivo."""
    if not os.path.exists(CAMINHO_CACHE_ML):
        return {}
    try:
        with open(CAMINHO_CACHE_ML, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _cache_e_oficial(cache: Dict[str, Any]) -> bool:
    """Garante que apenas resultados da URL oficial possam ser reutilizados."""
    return (
        isinstance(cache.get("produtos"), dict)
        and cache.get("origem_coleta") == ORIGEM_COLETA
        and cache.get("url_fonte") == URL_TENDENCIAS_ML
        and cache.get("status_coleta") == "sucesso"
    )


def _cache_valido() -> bool:
    """Verifica a validade temporal e a proveniência do cache."""
    cache = _ler_cache()
    if not _cache_e_oficial(cache):
        return False

    try:
        timestamp = datetime.fromisoformat(str(cache["timestamp"]))
    except (KeyError, TypeError, ValueError):
        return False

    return datetime.now() - timestamp < timedelta(hours=VALIDADE_CACHE_HORAS)


def _produtos_cache_oficial() -> Dict[str, Any]:
    """Retorna somente produtos de um cache que passou na validação de origem."""
    cache = _ler_cache()
    if _cache_e_oficial(cache):
        produtos = cache.get("produtos", {})
        return produtos if isinstance(produtos, dict) else {}
    return {}


def _salvar_cache(produtos: Dict[str, Any]) -> bool:
    """Persiste um resultado oficial de maneira atômica."""
    payload = {
        "timestamp": datetime.now().isoformat(),
        "data": datetime.now().date().isoformat(),
        "total": len(produtos),
        "fonte": FONTE_ML,
        "url_fonte": URL_TENDENCIAS_ML,
        "origem_coleta": ORIGEM_COLETA,
        "status_coleta": "sucesso",
        "produtos": produtos,
    }
    caminho_tmp = f"{CAMINHO_CACHE_ML}.tmp"
    try:
        with open(caminho_tmp, "w", encoding="utf-8") as arquivo:
            json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        os.replace(caminho_tmp, CAMINHO_CACHE_ML)
        logger.info("Cache oficial do Mercado Livre salvo com %d termos.", len(produtos))
        return True
    except OSError as erro:
        logger.error("Falha ao salvar cache oficial do Mercado Livre: %s", erro)
        try:
            if os.path.exists(caminho_tmp):
                os.remove(caminho_tmp)
        except OSError:
            pass
        return False


def _eh_link_de_tendencia(href: str) -> bool:
    """Aceita apenas um link de resultado de busca da lista oficial de tendências."""
    if not href:
        return False

    url = urlparse(href)
    dominio = url.netloc.lower()
    fragmento = url.fragment.lower()
    if dominio != "lista.mercadolivre.com.br":
        return False
    if "menu=categories" in fragmento:
        return False
    return bool(url.path and url.path != "/")


def _raspar_tendencias_pagina() -> List[str]:
    """Extrai somente os links da seção oficial ``Termos mais procurados``."""
    try:
        resposta = requests.get(URL_TENDENCIAS_ML, headers=HEADERS_PADRAO, timeout=TIMEOUT_REQUEST)
        resposta.raise_for_status()
    except requests.RequestException as erro:
        logger.warning("Falha ao acessar tendências oficiais do Mercado Livre: %s", erro)
        return []

    soup = BeautifulSoup(resposta.text, "html.parser")
    secao = soup.select_one("nav[aria-label='Termos mais procurados']")
    if secao is not None:
        links = secao.select("a.nav-footer-seo__link[href], a[href]")
    else:
        # A classe é própria da lista de tendências e evita os menus de categorias.
        links = soup.select("a.nav-footer-seo__link[href]")

    termos: List[str] = []
    for link in links:
        href = str(link.get("href", "")).strip()
        termo = link.get_text(" ", strip=True) or str(link.get("aria-label", "")).strip()
        termo = re.sub(r"\s+", " ", termo).strip()
        if not _eh_link_de_tendencia(href) or len(termo) < 3:
            continue
        if termo not in termos:
            termos.append(termo)
        if len(termos) >= MAX_TERMOS:
            break

    logger.info("Página oficial do Mercado Livre: %d termos validados.", len(termos))
    return termos


def _construir_produto(termo: str, posicao: int) -> Dict[str, Any]:
    """Monta o schema da grade sem inventar métricas não publicadas pela fonte."""
    return {
        "pins": 0,
        "pins_historico": 0,
        "crescimento": 0,
        "crescimento_real": False,
        "views_tiktok": 0,
        "resultados_ml": 0,
        "buscas_mes": 0,
        "buscas_historico": 0,
        "categoria": _inferir_categoria(termo),
        "categoria_origem": "Não informada pela página de tendências",
        "evento": "Termo mais procurado no Mercado Livre",
        "variacao": 0,
        "tendencia": "Em destaque",
        "score": max(1, MAX_TERMOS - posicao),
        "fonte": FONTE_ML,
        "origem_coleta": ORIGEM_COLETA,
        "url_fonte": URL_TENDENCIAS_ML,
        "posicao_ranking": posicao + 1,
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def capturar_tendencias_ml(forcar: bool = False) -> Dict[str, Any]:
    """Captura as tendências da URL oficial ou retorna um cache oficial validado."""
    if not forcar and _cache_valido():
        produtos_cache = _produtos_cache_oficial()
        if produtos_cache:
            logger.info("Cache oficial do Mercado Livre válido: %d termos.", len(produtos_cache))
            return produtos_cache

    termos = _raspar_tendencias_pagina()
    if not termos:
        produtos_cache = _produtos_cache_oficial()
        if produtos_cache:
            logger.warning("Página oficial indisponível; preservando %d termos do último cache validado.", len(produtos_cache))
            return produtos_cache
        logger.error("Nenhum termo oficial do Mercado Livre foi confirmado; a fonte será omitida da grade.")
        return {}

    produtos = {termo: _construir_produto(termo, posicao) for posicao, termo in enumerate(termos)}
    _salvar_cache(produtos)
    return produtos


def obter_tendencias_ml_cache() -> Dict[str, Any]:
    """Obtém tendências do cache oficial, atualizando quando necessário."""
    return capturar_tendencias_ml(forcar=False)


def forcar_atualizacao_ml() -> Dict[str, Any]:
    """Força uma nova leitura da página oficial de tendências."""
    return capturar_tendencias_ml(forcar=True)


def obter_status_cache_ml() -> Dict[str, Any]:
    """Retorna o estado do cache sem mascarar dados de origem não validada."""
    cache = _ler_cache()
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
        "valido": _cache_valido(),
        "total": int(cache.get("total", len(cache.get("produtos", {})))),
        "data_formatada": data_formatada,
        "fonte": cache.get("fonte", FONTE_ML),
    }


def obter_categorias_ml() -> List[str]:
    """Retorna categorias presentes nos termos oficiais atualmente disponíveis."""
    categorias = sorted(
        {
            dados.get("categoria", "Outros")
            for dados in obter_tendencias_ml_cache().values()
            if isinstance(dados, dict)
        }
    )
    return categorias if categorias else ["Outros"]
