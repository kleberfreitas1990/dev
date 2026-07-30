"""
divulgashop.py — Aba "Divulga Shop" para o Marketplace
======================================================
Fluxo: URL do produto Shopee → Extração automática de dados → Texto pronto para postar

Extrai: nome, preço, descrição, foto, link
Gera: texto otimizado para WhatsApp, Telegram e Instagram

Autor: Engenheiro de Software Sênior
Versão: 2.0.0
"""

import streamlit as st
import json
import os
import random
import re
import time
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote, urlparse, parse_qs

import requests

from modules.models import obter_palavra_chave

logger = logging.getLogger(__name__)


# ============================================================
# CREDENCIAIS SHOPEE API
# ============================================================
SHOPEE_APP_ID = "18372330665"
SHOPEE_SECRET = "YKHI6WJBBXZW2JNCX3IRPMEYJHZKUW6N"
SHOPEE_BASE_URL = "https://partner.shopeemobile.com"


# ============================================================
# CACHE LOCAL DE DIVULGAÇÃO
# ============================================================
CACHE_DIVULGA_PATH = "divulgashop_cache.json"
CACHE_EXTRACAO_PATH = "divulgashop_extracao_cache.json"


def _ler_json(path: str) -> Dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_json(path: str, data: Dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ============================================================
# EXTRAÇÃO DE DADOS DO PRODUTO SHOPEE
# ============================================================
def _gerar_sign(base_string: str) -> str:
    """Gera assinatura HMAC-SHA256 para a API Shopee."""
    return hmac.new(
        SHOPEE_SECRET.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def _extrair_id_produto(url: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extrai shop_id e item_id da URL do produto Shopee.
    Aceita formatos:
    - https://shopee.com.br/product/{shop_id}/{item_id}
    - https://shopee.com.br/product/{shop_id}/{item_id}?...
    - https://shopee.com.br/Produto-i.{shop_id}.{item_id}
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Formato: /product/{shop_id}/{item_id}
    match = re.search(r'/product/(\d+)/(\d+)', path)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Formato: -i.{shop_id}.{item_id}
    match = re.search(r'-(?:i\.|product\.)(\d+)\.(\d+)', path)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Formato: ?shop_id=&item_id=
    params = parse_qs(parsed.query)
    shop_id = int(params.get("shop_id", [None])[0]) if params.get("shop_id") else None
    item_id = int(params.get("item_id", [None])[0]) if params.get("item_id") else None
    if shop_id and item_id:
        return shop_id, item_id

    return None, None


def _extrair_id_simples(url: str) -> Optional[int]:
    """Extrai apenas o item_id de URLs curtas ou simplificadas."""
    path = urlparse(url).path.rstrip("/")

    # Último segmento numérico
    match = re.search(r'(\d{7,12})', path.split("/")[-1])
    if match:
        return int(match.group(1))

    return None


def buscar_dados_produto_por_id(item_id: int, shop_id: Optional[int] = None) -> Dict:
    """
    Busca dados do produto via API Shopee.
    Retorna: {nome, preco, descricao, foto, link, loja, avaliacoes, vendidos}
    """
    timestamp = str(int(time.time()))
    path = "/api/v2/shop/get_product_info"
    params = {"item_id": item_id, "shop_id": shop_id or 0}
    param_string = "".join(f"{k}={v}" for k, v in sorted(params.items()))
    base_string = f"{SHOPEE_APP_ID}{path}{timestamp}{param_string}"
    sign = _gerar_sign(base_string)

    full_params = {
        "partner_id": SHOPEE_APP_ID,
        "timestamp": timestamp,
        "sign": sign,
        **params,
    }

    url = f"{SHOPEE_BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.get(url, params=full_params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            logger.warning(f"API Shopee status {resp.status_code}")
    except Exception as e:
        logger.error(f"Erro API Shopee: {e}")

    return {}


def extrair_dados_produto(url: str) -> Dict:
    """
    Extrai dados completos do produto Shopee pela URL.
    Retorna dict com: nome, preco, descricao, foto, link, loja, avaliacoes, vendidos
    """
    # Cache de extração (5 min TTL)
    if os.path.exists(CACHE_EXTRACAO_PATH):
        cache = _ler_json(CACHE_EXTRACAO_PATH)
        if cache.get(url) and cache.get("timestamp"):
            try:
                cache_time = datetime.fromisoformat(cache["timestamp"])
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return cache[url]
            except Exception:
                pass

    shop_id, item_id = _extrair_id_produto(url)

    if not item_id:
        item_id = _extrair_id_simples(url)

    resultado = {
        "nome": "",
        "preco": "",
        "descricao": "",
        "foto": "",
        "link": url,
        "loja": "",
        "avaliacoes": 0,
        "vendidos": 0,
        "shop_id": shop_id,
        "item_id": item_id,
    }

    if not item_id:
        logger.warning(f"Não foi possível extrair item_id da URL: {url}")
        return resultado

    # Tentar via API
    if shop_id:
        dados = buscar_dados_produto_por_id(item_id, shop_id)
        if dados and dados.get("response"):
            resp = dados["response"]
            resultado["nome"] = resp.get("name", "")
            resultado["loja"] = resp.get("shop_name", "")
            resultado["avaliacoes"] = resp.get("rating_star", 0)
            resultado["vendidos"] = resp.get("sold", 0)

            # Preço
            price_data = resp.get("price") or resp.get("min_price")
            if price_data:
                if isinstance(price_data, (int, float)):
                    resultado["preco"] = f"R$ {price_data / 100000:.2f}"
                elif isinstance(price_data, str):
                    resultado["preco"] = price_data

            # Descrição
            resultado["descricao"] = resp.get("description", "")

            # Foto
            images = resp.get("images", [])
            if images:
                first_img = images[0] if isinstance(images[0], str) else images[0].get("url", "")
                resultado["foto"] = first_img

            # Salvar no cache
            cache = _ler_json(CACHE_EXTRACAO_PATH)
            cache[url] = resultado
            cache["timestamp"] = datetime.now().isoformat()
            _salvar_json(CACHE_EXTRACAO_PATH, cache)

            return resultado

    # Fallback: scraping via requests (sem browser)
    resultado_fallback = _extrair_fallback(url, item_id)
    if resultado_fallback.get("nome"):
        # Mesclar fallback com resultado parcial
        for key, val in resultado_fallback.items():
            if val and not resultado.get(key):
                resultado[key] = val

    # Salvar no cache
    cache = _ler_json(CACHE_EXTRACAO_PATH)
    cache[url] = resultado
    cache["timestamp"] = datetime.now().isoformat()
    _salvar_json(CACHE_EXTRACAO_PATH, cache)

    return resultado


def _extrair_fallback(url: str, item_id: int) -> Dict:
    """
    Fallback: tenta extrair dados do produto via scraping HTTP direto.
    Usa headers de navegador para contornar bloqueios simples.
    """
    resultado = {"nome": "", "preco": "", "descricao": "", "foto": ""}

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

        if resp.status_code != 200:
            return resultado

        html = resp.text

        # Tentar extrair JSON embutido (__NEXT_DATA__ ou similar)
        import re as _re
        json_match = _re.search(r'<script[^>]*>window\.__INIT_STATE__\s*=\s*({.*?})\s*</script>', html, _re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                page = data.get("Page", data)
                if isinstance(page, dict):
                    produto = page.get("product", page.get("item", {}))
                    if isinstance(produto, dict):
                        resultado["nome"] = produto.get("name", produto.get("title", ""))
                        resultado["descricao"] = produto.get("description", produto.get("desc", ""))
            except Exception:
                pass

        # Fallback: regex para metadados OG
        og_title = _re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        if og_title:
            resultado["nome"] = og_title.group(1)

        og_image = _re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        if og_image:
            resultado["foto"] = og_image.group(1)

        og_desc = _re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html)
        if og_desc:
            resultado["descricao"] = og_desc.group(1)

        # Extrair preço
        preco_match = _re.search(r'(?:R\$\s*|R\$)\s*(\d+[.,]\d{2})', html)
        if preco_match:
            resultado["preco"] = f"R$ {preco_match.group(1)}"

        # Extrair nome do produto de title
        title_match = _re.search(r'<title>([^<]+)</title>', html)
        if title_match and not resultado["nome"]:
            nome_bruto = title_match.group(1).strip()
            # Limpar sufixo " | Shopee Brasil"
            nome_bruto = _re.sub(r'\s*\|\s*Shopee\s*Brasil$', '', nome_bruto)
            if len(nome_bruto) > 5:
                resultado["nome"] = nome_bruto

    except Exception as e:
        logger.error(f"Fallback scraping falhou: {e}")

    return resultado


# ============================================================
# DETECÇÃO DE CATEGORIA
# ============================================================
CATEGORIAS_MAP = {
    "roda": "Esporte", "abdominal": "Esporte", "kettlebell": "Esporte",
    "tenis": "Moda", "tênis": "Moda", "sapato": "Moda", "bota": "Moda",
    "crocs": "Moda", "sandalia": "Moda", "sandália": "Moda",
    "camisa": "Moda", "blusa": "Moda", "vestido": "Moda",
    "capinha": "Eletrônicos", "capa": "Eletrônicos", "iphone": "Eletrônicos",
    "kindle": "Eletrônicos",
    "alexa": "Eletrônicos", "controle": "Games",
    "ps": "Games", "retroid": "Games", "booster": "Games",
    "pokemon": "Games", "figurinha": "Games",
    "espelho": "Casa", "prateleira": "Casa", "nincho": "Casa",
    "armazenador": "Casa", "caixa": "Casa", "jogo": "Casa",
    "boneca": "Infantil", "moto": "Infantil", "cadeirinha": "Infantil",
    "boneca sexual": "Geral", "vibrador": "Geral", "spray": "Geral",
    "bloqueador": "Geral", "grave": "Eletrônicos", "caixa de som": "Eletrônicos",
    "ar condicionado": "Eletrônicos", "meia": "Moda", "vertix": "Eletrônicos",
    "linhas": "Casa", "indonesia": "Casa", "samurai": "Casa", "linha": "Casa",
    "relógio": "Acessórios", "relogio": "Acessórios",
}


def _detectar_categoria(produto: str) -> str:
    nome_lower = produto.lower()
    for palavra, categoria in CATEGORIAS_MAP.items():
        if palavra in nome_lower:
            return categoria
    return "Geral"


# ============================================================
# SCORE DE TENDÊNCIA
# ============================================================
def calcular_score_divulga(produto: str, dados: Dict = None) -> int:
    if dados and isinstance(dados.get("score"), (int, float)):
        return min(10, max(1, int(dados["score"])))

    nome_lower = produto.lower()
    score = 5

    produtos_quentes = [
        "air fryer", "moto", "crocs", "tênis", "alexa", "iphone",
        "booster", "pokemon", "ar condicionado", "caixa de som",
        "boneca", "kindle", "retroid", "espelho", "prateleira"
    ]

    for p in produtos_quentes:
        if p in nome_lower:
            score += 2
            break

    agora = datetime.now()
    if agora.month in [6, 7, 8]:
        if any(p in nome_lower for p in ["casaco", "blusa", "tenis", "tênis", "bota"]):
            score += 1

    if agora.month in [11, 12]:
        if any(p in nome_lower for p in ["boneca", "brinquedo", "presente", "natal"]):
            score += 2

    return min(10, max(1, score))


# ============================================================
# GERADORES DE TEXTO POR PLATAFORMA
# ============================================================
def gerar_texto_whatsapp(produto: Dict) -> str:
    """Gera texto otimizado para WhatsApp"""
    nome = produto.get("nome", "Produto")
    preco = produto.get("preco", "Consulte o preço")
    descricao = produto.get("descricao", "")
    foto = produto.get("foto", "")
    link = produto.get("link", "")
    loja = produto.get("loja", "")

    # Pegar primeira linha da descrição
    desc_curta = ""
    if descricao:
        linhas = [l.strip() for l in descricao.split("\n") if l.strip()]
        desc_curta = linhas[0] if linhas else ""

    # Emoji baseado no preço
    if "R$" in preco:
        try:
            valor = float(preco.replace("R$", "").strip().replace(",", "."))
            emoji_preco = "💰" if valor < 50 else "💎" if valor < 200 else "👑"
        except:
            emoji_preco = "💰"
    else:
        emoji_preco = "💰"

    textos = [
        f"""🛒 🔥 ACHADINHO IMPERDÍVEL! 🔥

📦 *{nome}*
{emoji_preco} *Preço:* {preco}
🏪 Loja: {loja}

{desc_curta}

👉 *Compre aqui:*
{link}

🔥 Garanta antes que acabe!
""",
        f"""⚡ ALERTA DE OFERTA! ⚡

📦 *{nome}*
{emoji_preco} *{preco}*

{desc_curta}

🔗 Link: {link}

⏰ Corre que o preço pode subir!
""",
        f"""🎯 ACHADO NA SHOPEE!

📦 *{nome}*
🏪 {loja}
{emoji_preco} {preco}

{desc_curta}

🛒 Compre: {link}

💬 Me avisa se comprou!
""",
    ]

    return random.choice(textos)


def gerar_texto_telegram(produto: Dict) -> str:
    """Gera texto otimizado para Telegram"""
    nome = produto.get("nome", "Produto")
    preco = produto.get("preco", "Consulte o preço")
    descricao = produto.get("descricao", "")
    foto = produto.get("foto", "")
    link = produto.get("link", "")
    loja = produto.get("loja", "")

    desc_curta = ""
    if descricao:
        linhas = [l.strip() for l in descricao.split("\n") if l.strip()]
        desc_curta = linhas[0] if linhas else ""

    textos = [
        f"""🛒 <b>ACHADINHO</b> | <b>{nome}</b>

💰 <b>Preço:</b> {preco}
🏪 Loja: {loja}
📝 {desc_curta}

👉 <a href="{link}">Clique para comprar</a>
""",
        f"""⚡ <b>OFERTA</b> — {nome}

💰 {preco}
🏪 {loja}

📝 {desc_curta}

🛒 <a href="{link}">Comprar agora</a>
""",
    ]

    return random.choice(textos)


def gerar_texto_instagram(produto: Dict) -> str:
    """Gera texto otimizado para Instagram"""
    nome = produto.get("nome", "Produto")
    preco = produto.get("preco", "Consulte o preço")
    descricao = produto.get("descricao", "")
    foto = produto.get("foto", "")
    link = produto.get("link", "")
    loja = produto.get("loja", "")

    desc_curta = ""
    if descricao:
        linhas = [l.strip() for l in descricao.split("\n") if l.strip()]
        desc_curta = linhas[0] if linhas else ""

    dados_palavra = obter_palavra_chave(nome)
    hashtags = dados_palavra.get("hashtags", ["#achadinhos", "#shopeefinds"])[:6]

    textos = [
        f"""ACHADINHO IMPERDÍVEL 🔥

📦 {nome}
💰 {preco}
🏪 {loja}

{desc_curta}

👉 Link na bio!
👉 Comenta "LINK" que te envio no DM

{" ".join(hashtags)}
""",
        f"""VOCÊS NÃO VÃO ACREDITAR 🤯

📦 {nome}
💰 {preco}

{desc_curta}

👉 Comenta "EU QUERO" que te mando o link!

{" ".join(hashtags)}
""",
    ]

    return random.choice(textos)


# ============================================================
# RENDERIZAÇÃO DA ABA "DIVULGA SHOP"
# ============================================================
def render_divulga_shop():
    """
    Renderiza a aba completa "Divulga Shop" no Streamlit.
    Fluxo: URL → Extração automática → Texto pronto para postar
    """
    st.markdown("## 🛒 Divulga Shop")
    st.caption("Cole a URL do produto Shopee e gere textos prontos para WhatsApp, Telegram e Instagram")

    st.markdown("---")

    # ============================================================
    # SEÇÃO 1: URL DO PRODUTO
    # ============================================================
    st.markdown("### 🔗 URL do Produto")

    url_produto = st.text_input(
        "Cole o link do produto Shopee:",
        placeholder="https://shopee.com.br/product/12345/67890",
        key="divulgashop_url_input",
        help="Cole a URL completa do produto na Shopee. Ex: https://shopee.com.br/product/{shop_id}/{item_id}"
    )

    # Botão para extrair dados
    col_btn1, col_btn2 = st.columns([3, 1])

    with col_btn1:
        if st.button(
            "🔍 Extrair Dados do Produto",
            type="primary",
            use_container_width=True,
            key="btn_extrair_dados",
            disabled=not url_produto.strip()
        ):
            if not url_produto.strip():
                st.error("❌ Por favor, cole a URL do produto!")
            else:
                with st.spinner("🔍 Extraindo dados do produto..."):
                    dados_produto = extrair_dados_produto(url_produto.strip())

                if dados_produto.get("nome"):
                    st.session_state["dados_produto"] = dados_produto
                    st.success(f"✅ Dados extraídos: {dados_produto['nome']}")
                else:
                    st.warning("⚠️ Não foi possível extrair todos os dados. Preencha manualmente abaixo.")
                    st.session_state["dados_produto"] = {
                        "nome": "",
                        "preco": "",
                        "descricao": "",
                        "foto": "",
                        "link": url_produto.strip(),
                        "loja": "",
                    }

    with col_btn2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Cole a URL e clique para extrair")

    # ============================================================
    # SEÇÃO 2: DADOS EXTRAÍDOS (EDITÁVEIS)
    # ============================================================
    if "dados_produto" in st.session_state:
        dados = st.session_state["dados_produto"]

        st.markdown("---")
        st.markdown("### 📦 Dados do Produto")
        st.caption("Edite os campos abaixo se necessário antes de gerar o texto")

        # Foto do produto
        if dados.get("foto"):
            col_foto, col_info = st.columns([1, 3])
            with col_foto:
                try:
                    st.image(dados["foto"], caption="Foto do produto", use_container_width=True)
                except Exception:
                    st.info("🖼️ Foto não disponível")
        else:
            col_foto, col_info = st.columns([1, 3])

        # Campos editáveis
        nome = st.text_input("Nome do Produto", value=dados.get("nome", ""), key="divulgashop_nome", placeholder="Nome do produto")
        preco = st.text_input("Preço", value=dados.get("preco", ""), key="divulgashop_preco", placeholder="R$ 99,90")
        loja = st.text_input("Loja", value=dados.get("loja", ""), key="divulgashop_loja", placeholder="Nome da loja")
        link = st.text_input("Link do Produto", value=dados.get("link", url_produto), key="divulgashop_link", placeholder="https://shopee.com.br/...")

        # Descrição como text_area
        descricao = st.text_area(
            "Descrição",
            value=dados.get("descricao", ""),
            key="divulgashop_descricao",
            height=80,
            placeholder="Descrição do produto..."
        )

        # Montar dict final
        produto_final = {
            "nome": nome,
            "preco": preco,
            "descricao": descricao,
            "foto": dados.get("foto", ""),
            "link": link,
            "loja": loja,
        }

        # Salvar no session state
        st.session_state["produto_final"] = produto_final

        # ============================================================
        # SEÇÃO 3: PLATAFORMA E GERAÇÃO
        # ============================================================
        st.markdown("---")
        st.markdown("### 📱 Gerar Texto de Divulgação")

        col_p1, col_p2 = st.columns([1, 1])

        with col_p1:
            plataforma = st.radio(
                "Plataforma de divulgação:",
                ["💬 WhatsApp", "📨 Telegram", "📸 Instagram"],
                key="divulgashop_plataforma",
                horizontal=True
            )

        with col_p2:
            if st.button(
                "🚀 Gerar Texto de Divulgação",
                type="primary",
                use_container_width=True,
                key="btn_gerar_texto"
            ):
                if not produto_final.get("nome"):
                    st.error("❌ Preencha pelo menos o nome do produto!")
                else:
                    with st.spinner("🤖 Gerando texto otimizado..."):
                        time.sleep(0.5)

                        if "WhatsApp" in plataforma:
                            texto = gerar_texto_whatsapp(produto_final)
                        elif "Telegram" in plataforma:
                            texto = gerar_texto_telegram(produto_final)
                        else:
                            texto = gerar_texto_instagram(produto_final)

                    st.session_state["texto_gerado"] = texto
                    st.session_state["plataforma_atual"] = plataforma
                    st.success("✅ Texto gerado!")

        # ============================================================
        # SEÇÃO 4: TEXTO GERADO
        # ============================================================
        if "texto_gerado" in st.session_state and "plataforma_atual" in st.session_state:
            st.markdown("---")
            st.markdown(f"### 📝 Texto para {st.session_state['plataforma_atual']}")

            texto = st.session_state["texto_gerado"]

            # Preview
            st.text_area(
                "Texto gerado:",
                value=texto,
                height=300,
                key="divulgashop_preview",
                label_visibility="collapsed"
            )

            # Ações
            col_a1, col_a2, col_a3, col_a4 = st.columns(4)

            with col_a1:
                if st.button("📋 Copiar (veja acima)", use_container_width=True, key="btn_copiar"):
                    st.info("📋 Selecione o texto acima e copie (Ctrl+C)")

            with col_a2:
                if st.button("🔄 Gerar Novamente", use_container_width=True, key="btn_gerar_denovo"):
                    st.session_state.pop("texto_gerado", None)
                    st.rerun()

            with col_a3:
                if st.button("💾 Salvar Favorito", use_container_width=True, key="btn_salvar"):
                    cache = _ler_json(CACHE_DIVULGA_PATH)
                    favoritos = cache.get("favoritos", [])
                    favoritos.insert(0, {
                        "produto": produto_final.get("nome", ""),
                        "plataforma": st.session_state["plataforma_atual"],
                        "texto": texto,
                        "link": produto_final.get("link", ""),
                        "salvo_em": datetime.now().isoformat()
                    })
                    favoritos = favoritos[:20]
                    cache["favoritos"] = favoritos
                    _salvar_json(CACHE_DIVULGA_PATH, cache)
                    st.success("✅ Salvo nos favoritos!")

            with col_a4:
                nome_arquivo = produto_final.get("nome", "produto").replace(" ", "_").lower()[:30]
                st.download_button(
                    "📥 Baixar TXT",
                    data=texto,
                    file_name=f"divulgacao_{nome_arquivo}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="btn_download"
                )

            # Links rápidos
            st.markdown("---")
            st.markdown("#### 🔗 Links Rápidos")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.markdown(f"**Link do produto:** [{produto_final.get('nome', 'Produto')}]({produto_final.get('link', '#')})")
            with col_l2:
                texto_curto = f"{produto_final.get('nome', '')} - {produto_final.get('preco', '')} - {produto_final.get('link', '')}"
                st.code(texto_curto, language="text")

        # ============================================================
        # SEÇÃO 5: FAVORITOS
        # ============================================================
        st.markdown("---")
        st.markdown("### 📁 Favoritos Salvos")

        cache = _ler_json(CACHE_DIVULGA_PATH)
        favoritos = cache.get("favoritos", [])

        if favoritos:
            st.markdown(f"**{len(favoritos)} texto(s) salvo(s):**")

            for i, fav in enumerate(favoritos[:10]):
                with st.expander(
                    f"{i+1}. 📦 {fav.get('produto', 'N/A')} ({fav.get('plataforma', '')}) — {fav.get('salvo_em', '')[:10]}",
                    expanded=False
                ):
                    st.text_area(
                        "Texto salvo:",
                        value=fav.get("texto", ""),
                        height=120,
                        key=f"divulgashop_fav_txt_{i}",
                        label_visibility="collapsed"
                    )
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        if st.button("📋 Ver Texto", key=f"btn_ver_fav_{i}"):
                            st.code(fav.get("texto", ""), language="text")
                    with col_f2:
                        if st.button("🗑️ Remover", key=f"btn_rm_fav_{i}"):
                            favoritos.pop(i)
                            cache["favoritos"] = favoritos
                            _salvar_json(CACHE_DIVULGA_PATH, cache)
                            st.rerun()
        else:
            st.info("💡 Gere um texto e clique em 'Salvar Favorito' para reutilizar depois.")


__all__ = ["render_divulga_shop", "extrair_dados_produto"]
