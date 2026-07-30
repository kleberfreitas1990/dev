"""
divulgashop.py — Aba "Divulga Shop" para o Marketplace
======================================================
Fluxo simplificado:
1. Cole o link do produto Shopee
2. Gera mensagem formatada (foto + nome + preço + link)
3. Compartilhe direto no WhatsApp/Telegram/Instagram

Estilo: igual ao bot Divulgador Inteligente do Telegram

Autor: Engenheiro de Software Sênior
Versão: 3.0.0
"""

import streamlit as st
import json
import os
import re
import time
import hmac
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ============================================================
# CREDENCIAIS SHOPEE API
# ============================================================
SHOPEE_APP_ID = "18372330665"
SHOPEE_SECRET = "YKHI6WJBBXZW2JNCX3IRPMEYJHZKUW6N"
SHOPEE_BASE_URL = "https://partner.shopeemobile.com"

# Cache local
CACHE_PATH = "divulgashop_cache.json"


# ============================================================
# UTILS
# ============================================================
def _ler_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_json(path: str, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _gerar_sign(base_string: str) -> str:
    """Gera assinatura HMAC-SHA256 para API Shopee."""
    return hmac.new(
        SHOPEE_SECRET.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


# ============================================================
# EXTRAIR IDs DA URL
# ============================================================
def _extrair_ids(url: str):
    """Extrai shop_id e item_id da URL do produto."""
    path = urlparse(url).path.rstrip("/")

    # /product/{shop_id}/{item_id}
    match = re.search(r'/product/(\d+)/(\d+)', path)
    if match:
        return int(match.group(1)), int(match.group(2))

    # -i.{shop_id}.{item_id}
    match = re.search(r'-(?:i\.|product\.)(\d+)\.(\d+)', path)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Query params
    params = parse_qs(urlparse(url).query)
    shop_id = int(params.get("shop_id", [None])[0]) if params.get("shop_id") else None
    item_id = int(params.get("item_id", [None])[0]) if params.get("item_id") else None
    if shop_id and item_id:
        return shop_id, item_id

    return None, None


# ============================================================
# BUSCAR DADOS DO PRODUTO VIA API
# ============================================================
def _buscar_produto_api(shop_id: int, item_id: int) -> dict:
    """Busca dados do produto via API Shopee Open Platform."""
    timestamp = str(int(time.time()))
    path = "/api/v2/shop/get_product_info"
    params = {"item_id": item_id, "shop_id": shop_id}
    param_string = "".join(f"{k}={v}" for k, v in sorted(params.items()))
    base_string = f"{SHOPEE_APP_ID}{path}{timestamp}{param_string}"
    sign = _gerar_sign(base_string)

    full_params = {
        "partner_id": SHOPEE_APP_ID,
        "timestamp": timestamp,
        "sign": sign,
        **params,
    }

    try:
        resp = requests.get(
            f"{SHOPEE_BASE_URL}{path}",
            params=full_params,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data and data.get("response"):
                return data["response"]
    except Exception as e:
        logger.error(f"Erro API Shopee: {e}")

    return {}


# ============================================================
# EXTRAIR DADOS VIA SCRAPING (FALLBACK)
# ============================================================
def _extrair_via_scraping(url: str) -> dict:
    """Extrai dados do produto via scraping HTTP."""
    resultado = {}

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

        if resp.status_code != 200:
            return resultado

        html = resp.text

        # Meta tags OG
        og_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        if og_title:
            resultado["nome"] = og_title.group(1)

        og_image = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        if og_image:
            resultado["foto"] = og_image.group(1)

        og_desc = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html)
        if og_desc:
            resultado["descricao"] = og_desc.group(1)

        # Preço
        preco_match = re.search(r'(?:R\$\s*)(\d+[.,]\d{2})', html)
        if preco_match:
            resultado["preco"] = f"R$ {preco_match.group(1)}"

        # Nome do title
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match and not resultado.get("nome"):
            nome = title_match.group(1).strip()
            nome = re.sub(r'\s*\|\s*Shopee\s*Brasil$', '', nome)
            if len(nome) > 5:
                resultado["nome"] = nome

    except Exception as e:
        logger.error(f"Scraping falhou: {e}")

    return resultado


# ============================================================
# FUNÇÃO PRINCIPAL: EXTRAIR DADOS DO PRODUTO
# ============================================================
def extrair_dados_produto(url: str) -> dict:
    """
    Extrai dados do produto Shopee pela URL.
    Retorna: {nome, preco, descricao, foto, link}
    """
    # Cache 2 min
    cache = _ler_json(CACHE_PATH)
    if cache.get(url) and cache.get("timestamp"):
        try:
            cache_time = datetime.fromisoformat(cache["timestamp"])
            if datetime.now() - cache_time < timedelta(minutes=2):
                return cache[url]
        except Exception:
            pass

    shop_id, item_id = _extrair_ids(url)

    produto = {
        "nome": "",
        "preco": "",
        "descricao": "",
        "foto": "",
        "link": url,
    }

    # Tentar API primeiro
    if shop_id and item_id:
        api_data = _buscar_produto_api(shop_id, item_id)
        if api_data:
            produto["nome"] = api_data.get("name", "")
            produto["loja"] = api_data.get("shop_name", "")

            price = api_data.get("price")
            if price:
                try:
                    valor = float(price) / 100000
                    produto["preco"] = f"R$ {valor:.2f}"
                except:
                    produto["preco"] = str(price)

            min_price = api_data.get("min_price")
            if min_price and not produto["preco"]:
                try:
                    valor = float(min_price) / 100000
                    produto["preco"] = f"R$ {valor:.2f}"
                except:
                    pass

            produto["descricao"] = api_data.get("description", "")
            images = api_data.get("images", [])
            if images:
                produto["foto"] = images[0] if isinstance(images[0], str) else images[0].get("url", "")

            # Cache
            cache[url] = produto
            cache["timestamp"] = datetime.now().isoformat()
            _salvar_json(CACHE_PATH, cache)

            return produto

    # Fallback scraping
    scraping = _extrair_via_scraping(url)
    for key, val in scraping.items():
        if val and not produto.get(key):
            produto[key] = val

    # Cache
    cache[url] = produto
    cache["timestamp"] = datetime.now().isoformat()
    _salvar_json(CACHE_PATH, cache)

    return produto


# ============================================================
# GERAR MENSAGEM DE DIVULGAÇÃO
# ============================================================
def gerar_mensagem(produto: dict) -> str:
    """
    Gera mensagem formatada no estilo do Divulgador Inteligente:
    🛍️ Nome do Produto
    💸por R$ 99,90 🚨🚨
    👉Link p/ comprar: https://...
    _*Promoção sujeita a alteração a qualquer momento*_
    """
    nome = produto.get("nome", "Produto Shopee")
    preco = produto.get("preco", "")
    link = produto.get("link", "")
    foto = produto.get("foto", "")

    # Limpar nome (truncar se muito longo)
    if len(nome) > 80:
        nome = nome[:77] + "..."

    msg = f"""🛍️ {nome}

💸por {preco} 🚨🚨

👉Link p/ comprar: {link}

_*Promoção sujeita a alteração a qualquer momento*_"""

    return msg


# ============================================================
# FAVORITOS
# ============================================================
def salvar_favorito(produto: dict, mensagem: str, plataforma: str):
    cache = _ler_json(CACHE_PATH)
    favoritos = cache.get("favoritos", [])
    favoritos.insert(0, {
        "nome": produto.get("nome", ""),
        "preco": produto.get("preco", ""),
        "foto": produto.get("foto", ""),
        "link": produto.get("link", ""),
        "mensagem": mensagem,
        "plataforma": plataforma,
        "salvo_em": datetime.now().isoformat()
    })
    cache["favoritos"] = favoritos[:20]
    _salvar_json(CACHE_PATH, cache)


# ============================================================
# RENDERIZAÇÃO DA ABA
# ============================================================
def render_divulga_shop():
    """
    Renderiza a aba Divulga Shop.
    Fluxo: Cole o link → Gera mensagem pronta → Compartilhe.
    """
    st.markdown("## 🛒 Divulga Shop")
    st.caption("Cole o link do produto Shopee e gere a mensagem pronta para compartilhar")
    st.markdown("---")

    # ── CAMPO DE URL ──
    url = st.text_input(
        "🔗 Cole o link do produto Shopee:",
        placeholder="https://shopee.com.br/product/... ou https://s.shopee.com.br/...",
        key="ds_url",
        help="Cole o link do produto. Ex: https://shopee.com.br/product/12345/67890"
    )

    # ── BOTÃO GERAR ──
    if st.button("🚀 Gerar Mensagem de Divulgação", type="primary", use_container_width=True, key="ds_gerar", disabled=not url.strip()):
        if not url.strip():
            st.error("Cole o link do produto primeiro!")
        else:
            with st.spinner("🔍 Extraindo dados do produto..."):
                produto = extrair_dados_produto(url.strip())

            st.session_state["ds_produto"] = produto
            st.session_state["ds_mensagem"] = gerar_mensagem(produto)
            st.success(f"✅ Produto encontrado: {produto.get('nome', 'Produto')}")

    # ── EXIBIR RESULTADO ──
    if "ds_produto" in st.session_state and "ds_mensagem" in st.session_state:
        produto = st.session_state["ds_produto"]
        mensagem = st.session_state["ds_mensagem"]

        st.markdown("---")

        # Foto + info
        col_img, col_info = st.columns([2, 4])

        with col_img:
            if produto.get("foto"):
                st.image(produto["foto"], use_container_width=True)
            else:
                st.info("📷 Sem imagem")

        with col_info:
            st.markdown(f"### {produto.get('nome', 'Produto')}")
            if produto.get("preco"):
                st.markdown(f"### 💰 {produto['preco']}")
            if produto.get("loja"):
                st.markdown(f"**Loja:** {produto['loja']}")
            if produto.get("link"):
                st.markdown(f"**Link:** [{produto.get('nome', 'Ver produto')[:40]}...]({produto['link']})")

        # ── MENSAGEM GERADA ──
        st.markdown("---")
        st.markdown("### 📝 Mensagem Pronta para Compartilhar")

        st.text_area(
            "Mensagem:",
            value=mensagem,
            height=200,
            key="ds_preview",
            label_visibility="collapsed"
        )

        # ── AÇÕES ──
        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            st.markdown("#### 💬 WhatsApp")
            if st.button("📤 Compartilhar no WhatsApp", use_container_width=True, key="ds_whats"):
                # Abrir WhatsApp Web com a mensagem pré-preenchida
                texto_codificado = mensagem.replace(" ", "%20").replace("\n", "%0A")
                link_wa = f"https://web.whatsapp.com/send?text={texto_codificado}"
                st.markdown(f"[📤 Abrir WhatsApp Web]({link_wa})")
                st.success("Clique no link acima para compartilhar no WhatsApp!")

        with col_a2:
            st.markdown("#### 📨 Telegram")
            if st.button("📤 Compartilhar no Telegram", use_container_width=True, key="ds_tele"):
                texto_codificado = mensagem.replace(" ", "%20").replace("\n", "%0A")
                link_tg = f"https://t.me/share/url?url={produto.get('link', '')}&text={texto_codificado}"
                st.markdown(f"[📤 Abrir Telegram]({link_tg})")
                st.success("Clique no link acima para compartilhar no Telegram!")

        with col_a3:
            st.markdown("#### 📸 Instagram")
            if st.button("📤 Preparar para Instagram", use_container_width=True, key="ds_insta"):
                st.info("📋 Copie a mensagem acima e cole no Instagram Stories ou DM")

        # ── COPIAR + DOWNLOAD + FAVORITO ──
        st.markdown("---")
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            st.download_button(
                "📥 Baixar Mensagem (.txt)",
                data=mensagem,
                file_name=f"divulgacao_{produto.get('nome', 'produto')[:30].replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="ds_download"
            )

        with col_b2:
            if st.button("🔄 Gerar Novamente", use_container_width=True, key="ds_novo"):
                st.session_state.pop("ds_produto", None)
                st.session_state.pop("ds_mensagem", None)
                st.rerun()

        with col_b3:
            if st.button("💾 Salvar Favorito", use_container_width=True, key="ds_fav"):
                salvar_favorito(produto, mensagem, "Divulga Shop")
                st.success("✅ Salvo nos favoritos!")

    # ── FAVORITOS ──
    st.markdown("---")
    st.markdown("### 📁 Favoritos Salvos")

    cache = _ler_json(CACHE_PATH)
    favoritos = cache.get("favoritos", [])

    if favoritos:
        st.markdown(f"**{len(favoritos)} salvo(s):**")
        for i, fav in enumerate(favoritos[:8]):
            with st.expander(
                f"📦 {fav.get('nome', 'N/A')} — {fav.get('preco', '')} ({fav.get('salvo_em', '')[:10]})",
                expanded=False
            ):
                if fav.get("foto"):
                    st.image(fav["foto"], width=150)
                st.text_area(
                    "Mensagem:",
                    value=fav.get("mensagem", ""),
                    height=100,
                    key=f"ds_fav_msg_{i}",
                    label_visibility="collapsed"
                )
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    if st.button("📋 Copiar", key=f"ds_copiar_{i}"):
                        st.code(fav.get("mensagem", ""), language="text")
                with col_f2:
                    if st.button("🗑️ Remover", key=f"ds_rm_{i}"):
                        favoritos.pop(i)
                        cache["favoritos"] = favoritos
                        _salvar_json(CACHE_PATH, cache)
                        st.rerun()
    else:
        st.info("💡 Gere uma mensagem e salve como favorito para reutilizar.")


__all__ = ["render_divulga_shop", "extrair_dados_produto", "gerar_mensagem"]
