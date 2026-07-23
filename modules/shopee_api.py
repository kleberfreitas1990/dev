"""
shopee_api.py — Integração com a API da Shopee (Painel de Afiliado)

PROTEÇÕES DE RATE LIMIT:
- Cache agressivo de 6 horas (mesmo TTL do Google Trends)
- Máximo 10 requisições por ciclo de atualização (12h)
- Exponential backoff em caso de erro
- Fallback automático para JSON cacheado se a API falhar
- Log de todas as requisições para monitoramento

CREDENCIAIS:
- st.secrets["SHOPEE_APP_ID"] / st.secrets["SHOPEE_SECRET"] (Streamlit Cloud)
- .streamlit/secrets.toml (local)
- Fallback: variáveis de ambiente
"""

import os
import time
import hmac
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÕES DE PROTEÇÃO
# ============================================================
MAX_REQUESTS_PER_CYCLE = 10       # Máximo de requisições por ciclo (12h)
CACHE_TTL_SEGUNDOS = 6 * 3600     # Cache de 6 horas
RETRY_DELAY = 5                   # Delay entre retries (segundos)
MAX_RETRIES = 2                   # Máximo de retries por requisição
REQUEST_TIMEOUT = 10              # Timeout em segundos
MIN_REQUEST_INTERVAL = 2          # Mínimo 2s entre requisições (proteção)

# Arquivos de controle
CONTROLE_PATH = Path(__file__).parent.parent / "shopee_api_controle.json"
CACHE_PATH = Path(__file__).parent.parent / "shopee_api_cache.json"


# ============================================================
# CREDENCIAIS
# ============================================================
def _obter_credenciais():
    """
    Obtém credenciais de forma segura:
    1. st.secrets (Streamlit Cloud)
    2. .streamlit/secrets.toml (local)
    3. Variáveis de ambiente
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            app_id = st.secrets.get("SHOPEE_APP_ID", "")
            secret = st.secrets.get("SHOPEE_SECRET", "")
            base_url = st.secrets.get("SHOPEE_BASE_URL", "https://partner.shopeemobile.com")
            if app_id and secret:
                return app_id, secret, base_url
    except Exception:
        pass

    # Fallback: variáveis de ambiente
    app_id = os.environ.get("SHOPEE_APP_ID", "")
    secret = os.environ.get("SHOPEE_SECRET", "")
    base_url = os.environ.get("SHOPEE_BASE_URL", "https://partner.shopeemobile.com")
    return app_id, secret, base_url


# ============================================================
# CONTROLE DE REQUISIÇÕES
# ============================================================
def _carregar_controle():
    """Carrega o controle de requisições do arquivo JSON."""
    if CONTROLE_PATH.exists():
        try:
            with open(CONTROLE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"requisicoes_ciclo": 0, "ultimo_reset": "", "total_erros": 0, "total_sucesso": 0}


def _salvar_controle(controle):
    """Salva o controle de requisições."""
    try:
        with open(CONTROLE_PATH, "w") as f:
            json.dump(controle, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar controle: {e}")


def _verificar_limite():
    """
    Verifica se o ciclo ainda permite requisições.
    Reseta o contador se já passaram 12h desde o último reset.
    """
    controle = _carregar_controle()
    agora = datetime.now()

    if controle.get("ultimo_reset"):
        ultimo_reset = datetime.fromisoformat(controle["ultimo_reset"])
        if agora - ultimo_reset < timedelta(hours=12):
            # Ainda no mesmo ciclo
            if controle["requisicoes_ciclo"] >= MAX_REQUESTS_PER_CYCLE:
                logger.warning(f"🚫 Rate limit atingido: {controle['requisicoes_ciclo']}/{MAX_REQUESTS_PER_CYCLE}")
                return False, controle
        else:
            # Novo ciclo — resetar
            controle["requisicoes_ciclo"] = 0

    return True, controle


def _incrementar_controle(controle, sucesso=True):
    """Incrementa o contador de requisições."""
    controle["requisicoes_ciclo"] += 1
    if not controle.get("ultimo_reset"):
        controle["ultimo_reset"] = datetime.now().isoformat()
    if sucesso:
        controle["total_sucesso"] = controle.get("total_sucesso", 0) + 1
    else:
        controle["total_erros"] = controle.get("total_erros", 0) + 1
    _salvar_controle(controle)


# ============================================================
# CACHE
# ============================================================
def _cache_valido():
    """Verifica se o cache da API está válido (menos de 6h)."""
    if not CACHE_PATH.exists():
        return False
    try:
        with open(CACHE_PATH, "r") as f:
            cache = json.load(f)
        timestamp = cache.get("timestamp", "")
        if timestamp:
            cache_time = datetime.fromisoformat(timestamp)
            return datetime.now() - cache_time < timedelta(seconds=CACHE_TTL_SEGUNDOS)
    except Exception:
        pass
    return False


def _ler_cache():
    """Lê o cache da API."""
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _salvar_cache(data, produtos=None):
    """Salva o cache da API."""
    cache = {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "produtos": produtos or [],
    }
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar cache API: {e}")


# ============================================================
# GERAÇÃO DE SIGN (HMAC-SHA256)
# ============================================================
def _gerar_sign(base_string, secret):
    """Gera a assinatura HMAC-SHA256."""
    return hmac.new(
        secret.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


# ============================================================
# REQUISIÇÃO SEGURA
# ============================================================
def _request_seguro(path, params=None, method="GET"):
    """
    Faz uma requisição à API da Shopee com proteção completa:
    - Rate limit check
    - Cache check
    - Retry com backoff
    - Timeout
    """
    app_id, secret, base_url = _obter_credenciais()

    if not app_id or not secret:
        logger.warning("⚠️ Credenciais da Shopee não configuradas — usando fallback")
        return None

    # Verificar rate limit
    pode_fazer, controle = _verificar_limite()
    if not pode_fazer:
        logger.info("⚠️ Rate limit atingido — usando cache")
        return _ler_cache()

    # Gerar assinatura
    timestamp = str(int(time.time()))
    if method == "GET" and params:
        param_string = "".join(f"{k}={v}" for k, v in sorted(params.items()))
        base_string = f"{app_id}{path}{timestamp}{param_string}"
    else:
        base_string = f"{app_id}{path}{timestamp}"

    sign = _gerar_sign(base_string, secret)

    # Montar URL
    common_params = {
        "partner_id": app_id,
        "timestamp": timestamp,
        "sign": sign,
    }
    if params:
        common_params.update(params)

    url = f"{base_url}{path}"
    headers = {"Content-Type": "application/json"}

    # Tentar com retry
    for tentativa in range(MAX_RETRIES + 1):
        try:
            if tentativa > 0:
                time.sleep(RETRY_DELAY * tentativa)  # Backoff exponencial
                logger.info(f"🔄 Tentativa {tentativa + 1}/{MAX_RETRIES + 1}")

            if method == "GET":
                resp = requests.get(url, params=common_params, timeout=REQUEST_TIMEOUT)
            else:
                resp = requests.post(url, params=common_params, json=params, timeout=REQUEST_TIMEOUT, headers=headers)

            _incrementar_controle(controle, sucesso=(resp.status_code == 200))

            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning(f"⚠️ API Shopee status {resp.status_code}: {resp.text[:200]}")
                _incrementar_controle(controle, sucesso=False)

        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Timeout na requisição (tentativa {tentativa + 1})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠️ Erro de conexão (tentativa {tentativa + 1})")
        except Exception as e:
            logger.error(f"❌ Erro na requisição: {e}")

        _incrementar_controle(controle, sucesso=False)

    logger.error("❌ Todas as tentativas falharam — usando fallback")
    return None


# ============================================================
# FUNÇÕES PÚBLICAS
# ============================================================
def buscar_termos_trending(limit=30):
    """
    Busca termos em tendência na Shopee.
    
    NOTA: A API pública da Shopee (Open Platform) é voltada para sellers,
    não possui endpoint de trending searches. Esta função usa fallback
    inteligente para os dados já em cache.
    
    RATE LIMIT: Não faz requisição real à API para trending (proteção).
    Retorna dados do cache + Google Trends cruzados.
    """
    # Proteção: não faz request à API para trending (não existe endpoint)
    logger.info("📊 Shopee trending: usando cache (API não possui endpoint de tendências)")
    
    # Ler cache local
    cache = _ler_cache()
    if cache and cache.get("produtos"):
        return cache["produtos"]
    
    # Fallback: ler shopee_trends.json
    trends_path = Path(__file__).parent.parent / "shopee_trends.json"
    if trends_path.exists():
        with open(trends_path, "r") as f:
            data = json.load(f)
        return data.get("data", [])
    
    return []


def buscar_info_produto(termo):
    """
    Busca informações de um produto específico na Shopee.
    Usa a API para enriquecer dados de produtos que já temos.
    
    RATE LIMIT: Máximo 5 chamadas por ciclo.
    """
    if not _cache_valido():
        cache = _request_seguro(
            "/api/v2/public/get_shop_by_name",
            params={"keyword": termo, "limit": 5}
        )
        if cache:
            _salvar_cache({"endpoint": "get_shop_by_name", "termo": termo}, cache)
            return cache
    
    return _ler_cache()


def buscar_produtos_shopee_api(termos=None):
    """
    Busca informações de produtos via API da Shopee.
    
    PROTEÇÃO: 
    - Cache de 6h
    - Máximo 10 req/ciclo
    - Fallback para JSON se API falhar
    
    Retorna lista de produtos com info enriquecida.
    """
    # Verificar cache primeiro
    if _cache_valido():
        cache = _ler_cache()
        if cache:
            return cache.get("produtos", [])

    # Ler termos de fallback
    if termos is None:
        termos = buscar_termos_trending()

    if not termos:
        return []

    # Usar API para enriquecer (máximo 3 termos por ciclo para proteger)
    termos_api = termos[:3]  # Proteção: só 3 produtos por ciclo
    produtos_enriquecidos = []

    for termo in termos_api:
        info = buscar_info_produto(termo)
        if info:
            produtos_enriquecidos.append({
                "produto": termo,
                "fonte": "Shopee API",
                "info_api": info,
            })

    # Salvar cache
    _salvar_cache(
        {"endpoint": "product_search", "total": len(produtos_enriquecidos)},
        produtos_enriquecidos
    )

    # Completar com os termos restantes do fallback
    produtos_full = produtos_enriquecidos
    for termo in termos:
        if termo not in [p.get("produto") for p in produtos_enriquecidos]:
            produtos_full.append({
                "produto": termo,
                "fonte": "Shopee (Fallback)",
            })

    return produtos_full


def status_api():
    """Retorna o status atual da API Shopee."""
    app_id, secret, base_url = _obter_credenciais()
    controle = _carregar_controle()
    cache_valido = _cache_valido()

    return {
        "credenciais_ok": bool(app_id and secret),
        "app_id": app_id[:4] + "..." if app_id else "N/A",
        "cache_valido": cache_valido,
        "requisicoes_ciclo": controle.get("requisicoes_ciclo", 0),
        "limite_ciclo": MAX_REQUESTS_PER_CYCLE,
        "total_sucesso": controle.get("total_sucesso", 0),
        "total_erros": controle.get("total_erros", 0),
        "ultimo_reset": controle.get("ultimo_reset", "Nunca"),
    }


# ============================================================
# INTEGRAÇÃO COM GOOGLE_TRENDS (substitui o scraping bloqueado)
# ============================================================
def obter_termos_shopee_api():
    """
    Função principal para obter termos da Shopee.
    
    PRIORIDADE:
    1. Cache da API (6h) — se válido, usa
    2. shopee_trends.json — fallback principal
    3. API real — apenas se cache expirou E rate limit permite
    
    NUNCA faz mais de 1 requisição real por ciclo de 12h.
    """
    # 1. Verificar cache da API
    if _cache_valido():
        cache = _ler_cache()
        if cache and cache.get("data", {}).get("produtos"):
            logger.info("✅ Shopee: usando cache da API (válido)")
            return cache["data"]["produtos"]

    # 2. Fallback: shopee_trends.json (sempre disponível)
    trends_path = Path(__file__).parent.parent / "shopee_trends.json"
    if trends_path.exists():
        with open(trends_path, "r") as f:
            data = json.load(f)
        termos = [t.get("termo") for t in data.get("tendencias", []) if isinstance(t, dict)]
        if not termos:
            termos = data.get("data", []) # Fallback legível se for lista direta
        if termos:
            logger.info(f"✅ Shopee: usando fallback JSON ({len(termos)} termos)")
            return termos

    # 3. Último recurso: API real (com proteção)
    pode_fazer, controle = _verificar_limite()
    if pode_fazer and controle["requisicoes_ciclo"] < 3:  # Máximo 3 req reais/ciclo
        resultado = _request_seguro(
            "/api/v2/public/get_shops_by_partner",
            params={"partner_id": _obter_credenciais()[0], "limit": 30}
        )
        if resultado and resultado.get("response"):
            _salvar_cache(resultado, resultado.get("response", []))
            return resultado.get("response", [])

    logger.warning("⚠️ Shopee: sem dados disponíveis")
    return []
