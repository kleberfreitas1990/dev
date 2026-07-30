"""
divulgashop.py — Aba "Divulga Shop" para o Marketplace
======================================================
Módulo de divulgação inteligente de produtos Shopee.
Gera textos prontos para WhatsApp, Telegram e Instagram,
com links trackeados, hashtags otimizadas e score de tendência.

Autor: Engenheiro de Software Sênior
Versão: 1.0.0
"""

import streamlit as st
import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote

# Importa módulos existentes do repositório
from modules.models import obter_palavra_chave, PALAVRAS_CHAVE_CAUDA_LONGA
from modules.grade_descoberta import descobrir_produtos_grade, enriquecer_produto
from modules.produtos_dinamicos import obter_produtos_dinamicos
from modules.pinterest_trends import obter_pinterest_trends_cache

logger = __import__("logging").getLogger(__name__)


# ============================================================
# CACHE LOCAL DE DIVULGAÇÃO
# ============================================================
CACHE_DIVULGA_PATH = "divulgashop_cache.json"


def _ler_cache_divulga() -> Dict:
    """Lê o cache de divulgação"""
    if os.path.exists(CACHE_DIVULGA_PATH):
        try:
            with open(CACHE_DIVULGA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_cache_divulga(dados: Dict):
    """Salva o cache de divulgação"""
    try:
        with open(CACHE_DIVULGA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ============================================================
# HASHTAGS DINÂMICAS POR CATEGORIA
# ============================================================
HASHTAGS_POR_CATEGORIA = {
    "Moda": [
        "#modafeminina", "#lookdodia", "#tendenciamoda", "#achadinhos",
        "#shopeefinds", "#baratinhos", "#modacriativa", "#lookfeminino",
        "#estilofeminino", "#fashionblogger", "#achadinhashopee"
    ],
    "Eletrônicos": [
        "#tecnologia", "#gadgets", "#techfinds", "#shopeetech",
        "#eletronicos", "#inovacao", "#achadinhos", "#baratotech"
    ],
    "Beleza": [
        "#beleza", "#skincare", "#makeup", "#belezafeminina",
        "#cuidados", "#shopeebeauty", "#achadinhas", "#lookdodia"
    ],
    "Casa": [
        "#casaeorganizacao", "#decoracao", "#donadecasa", "#achadinhos",
        "#casainteligente", "#organizacao", "#shopeecasa", "#donadecasa"
    ],
    "Infantil": [
        "#maternidade", "#infantil", "#brinquedos", "#mamais",
        "#maternidadereal", "#shopeekids", "#criancas", "#brinquedoseducativos"
    ],
    "Esporte": [
        "#fitness", "#esporte", "#treino", "#saude",
        "#crossfit", "#shopeefitness", "#treinofuncional", "#vidaativa"
    ],
    "Games": [
        "#gamer", "#games", "#setupgamer", "#shopeegames",
        "#pcgamer", "#console", "#jogos", "#achadinhosgamer"
    ],
    "Geral": [
        "#achadinhos", "#shopeefinds", "#promocao", "#oferta",
        "#desconto", "#comprasonline", "#bompreço", "#viral"
    ]
}


# ============================================================
# CATEGORIAS DINÂMICAS
# ============================================================
CATEGORIAS_MAP = {
    "roda": "Esporte", "abdominal": "Esporte", "kettlebell": "Esporte",
    "tenis": "Moda", "tênis": "Moda", "sapato": "Moda", "bota": "Moda",
    "crocs": "Moda", "sandalia": "Moda", "sandália": "Moda",
    "camisa": "Moda", "blusa": "Moda", "vestido": "Moda",
    "capinha": "Eletrônicos", "capa": "Eletrônicos",
    "alexa": "Eletrônicos", "controle": "Games",
    "ps": "Games", "retroid": "Games", "booster": "Games",
    "pokemon": "Games", "figurinha": "Games",
    "espelho": "Casa", "prateleira": "Casa", "nincho": "Casa",
    "armazenador": "Casa", "caixa": "Casa", "jogo": "Casa",
    "boneca": "Infantil", "moto": "Infantil", "cadeirinha": "Infantil",
    "boneca sexual": "Geral", "vibrador": "Geral", "spray": "Geral",
    "bloqueador": "Geral", "grave": "Eletrônicos", "caixa de som": "Eletrônicos",
    "ar condicionado": "Eletrônicos", "meia": "Moda", "vertix": "Eletrônicos",
    "kindle": "Eletrônicos", "linhas": "Casa", "indonesia": "Casa",
    "samurai": "Casa", "linha": "Casa",
}


def _detectar_categoria(produto: str) -> str:
    """Detecta a categoria de um produto"""
    nome_lower = produto.lower()
    for palavra, categoria in CATEGORIAS_MAP.items():
        if palavra in nome_lower:
            return categoria
    return "Geral"


# ============================================================
# GENERADOR DE TEXTO PARA WHATSAPP
# ============================================================
def gerar_texto_whatsapp(produto: str, categoria: str, score: int, link: str) -> str:
    """Gera texto otimizado para WhatsApp"""
    dados_palavra = obter_palavra_chave(produto)
    hashtags = dados_palavra.get("hashtags", ["#achadinhos", "#shopeefinds"])[:3]
    palavra_chave = dados_palavra.get("palavra", produto)
    
    hoje = datetime.now()
    dia_semana = hoje.strftime("%A").capitalize()
    
    # Emoji de urgência baseado no score
    if score >= 9:
        emoji_urgencia = "🔥🚨"
        frase_urgencia = "EXPLOSÃO DE VENDAS"
    elif score >= 7:
        emoji_urgencia = "🔥"
        frase_urgencia = "EM ALTA"
    elif score >= 5:
        emoji_urgencia = "⭐"
        frase_urgencia = "TRENDING"
    else:
        emoji_urgencia = "💡"
        frase_urgencia = "NOVIDADE"
    
    textos = [
        f"""🛒 {emoji_urgencia} ACHADINHO DO DIA {emoji_urgencia}

📦 *{produto}*
{frase_urgencia} na Shopee!

✨ Por que comprar?
👉 Produto em alta nas buscas
👉 Preço incrível
👉 Frete grátis para muitas regiões

🔗 *Compre aqui:* {link}

{hashtags[0]} {hashtags[1]} {hashtags[2]}
""",
        f"""⚡ {frase_urgencia} — {produto} ⚡

Galera, esse produto tá bombando na Shopee!
Eu encontrei e não podia deixar de compartilhar.

📌 *{produto}*
🏷️ {palavra_chave}
📊 Score de tendência: {score}/10

🛒 Link direto: {link}

⏰ Garanta antes que acabe!

{hashtags[0]} {hashtags[1]} {hashtags[2]}
""",
        f"""🎯 ACHADO IMPERDÍVEL!

📦 *{produto}*
{emoji_urgencia} {frase_urgencia} — Score: {score}/10

✅ Em alta nas buscas da Shopee
✅ Melhor preço garantido
✅ Frete grátis

👇 Comprem aqui:
{link}

{hashtags[0]} {hashtags[1]} {hashtags[2]}

💬 Me avisem se comprarem!
""",
    ]
    
    return random.choice(textos)


# ============================================================
# GENERADOR DE TEXTO PARA TELEGRAM
# ============================================================
def gerar_texto_telegram(produto: str, categoria: str, score: int, link: str) -> str:
    """Gera texto otimizado para Telegram"""
    dados_palavra = obter_palavra_chave(produto)
    hashtags = dados_palavra.get("hashtags", ["#achadinhos", "#shopeefinds"])[:4]
    palavra_chave = dados_palavra.get("palavra", produto)
    
    textos = [
        f"""🛒 <b>ACHADINHO</b> | <b>{produto}</b>

📊 Score: {score}/10 | <b>EM ALTA</b>
🔍 Busca: {palavra_chave}

Este produto está <b>bombando</b> na Shopee agora!
Não perca a chance de garantir com o melhor preço.

👉 <a href="{link}">Clique para comprar</a>

{' | '.join(hashtags)}
""",
        f"""⚡ <b>TRENDING</b> — {produto}

📈 Tendência real da Shopee
🎯 Categoria: {categoria}
⭐ Score: {score}/10

🛒 <a href="{link}">Comprar agora</a>

📌 Esse produto está em alta nas buscas.
Aproveite enquanto o preço está bom!

{' | '.join(hashtags)}
""",
    ]
    
    return random.choice(textos)


# ============================================================
# GENERADOR DE TEXTO PARA INSTAGRAM
# ============================================================
def gerar_texto_instagram(produto: str, categoria: str, score: int, link: str) -> str:
    """Gera texto otimizado para Instagram (legenda de Reels/Stories)"""
    dados_palavra = obter_palavra_chave(produto)
    todas_hashtags = dados_palavra.get("hashtags", ["#achadinhos", "#shopeefinds"])
    hashtags_cat = HASHTAGS_POR_CATEGORIA.get(categoria, HASHTAGS_POR_CATEGORIA["Geral"])
    todas_hashtags = list(set(todas_hashtags + hashtags_cat))[:12]
    hashtag_string = " ".join(todas_hashtags)
    
    textos = [
        f"""ACHADINHO IMPERDÍVEL 🔥

{produto} tá bombando na Shopee e eu preciso compartilhar com vocês!

Esse produto está em ALTA nas buscas 📈 e com preço incrível.

👉 Link na bio / swipe up
👉 Comenta "LINK" que te envio no DM

Score de tendência: {score}/10

{hashtag_string}
""",
        f"""VOCÊS NÃO VÃO ACREDITAR 🤯

Encontrei {produto.lower()} na Shopee por um preço absurdo!

🔥 Em alta nas buscas
📊 Score: {score}/10
🛒 Frete grátis

👉 Comenta "EU QUERO" que te mando o link!

{hashtag_string}
""",
        f"""AQUELE ACHADINHO QUE VOCÊ PRECISA 💸

{produto}

Tá todo mundo comprando esse produto na Shopee e agora eu sei o porquê — tá com preço MUITO bom!

📈 Trending
⭐ Score: {score}/10

👉 Link na bio!
👉 Comenta "LINK" que te envio

{hashtag_string}
""",
    ]
    
    return random.choice(textos)


# ============================================================
# GENERADOR DE LINK SHOPEE
# ============================================================
def gerar_link_shopee(produto: str, termo_busca: Optional[str] = None) -> str:
    """Gera link de busca na Shopee"""
    termo = termo_busca if termo_busca else produto
    return f"https://shopee.com.br/search?keyword={quote(termo)}"


# ============================================================
# SCORE DE TENDÊNCIA DINÂMICO
# ============================================================
def calcular_score_divulga(produto: str, dados: Dict = None) -> int:
    """Calcula score de tendência para divulgação"""
    if dados and isinstance(dados.get("score"), (int, float)):
        return min(10, max(1, int(dados["score"])))
    
    nome_lower = produto.lower()
    score = 5  # Base
    
    # Produtos quentes
    produtos_quentes = [
        "air fryer", "moto", "crocs", "tênis", "alexa", "iphone",
        "booster", "pokemon", "ar condicionado", "caixa de som",
        "boneca", "kindle", "retroid", "espelho", "prateleira"
    ]
    
    for produto_quente in produtos_quentes:
        if produto_quente in nome_lower:
            score += 2
            break
    
    # Produtos em alta sazonal
    agora = datetime.now()
    if agora.month in [6, 7, 8]:
        if any(p in nome_lower for p in ["casaco", "blusa", "tenis", "tênis", "bota"]):
            score += 1
    
    if agora.month in [11, 12]:
        if any(p in nome_lower for p in ["boneca", "brinquedo", "presente", "natal"]):
            score += 2
    
    return min(10, max(1, score))


# ============================================================
# RENDERIZAÇÃO DA ABA "DIVULGA SHOP"
# ============================================================
def render_divulga_shop():
    """
    Renderiza a aba completa "Divulga Shop" no Streamlit.
    """
    st.markdown("## 🛒 Divulga Shop")
    st.caption("Gere textos prontos para divulgar produtos Shopee no WhatsApp, Telegram e Instagram")
    
    st.markdown("---")
    
    # ============================================================
    # SEÇÃO 1: SELEÇÃO DE PRODUTOS
    # ============================================================
    col_sel1, col_sel2 = st.columns([2, 1])
    
    with col_sel1:
        st.markdown("### 📦 Escolha um Produto")
        
        # Carrega produtos dinâmicos
        try:
            produtos_dinamicos = obter_produtos_dinamicos()
            produtos_lista = list(produtos_dinamicos.keys()) if produtos_dinamicos else []
        except Exception:
            produtos_lista = []
        
        # Busca na grade de descoberta
        try:
            produtos_grade = descobrir_produtos_grade(quantidade=20)
            produtos_grade_lista = [p.get("produto", "") for p in produtos_grade if p.get("produto")]
        except Exception:
            produtos_grade_lista = []
        
        # Combina e remove duplicatas
        todos_produtos = list(dict.fromkeys(produtos_lista + produtos_grade_lista))
        
        # Fallback com TERMOS_REAIS_SHOPEE
        if len(todos_produtos) < 10:
            try:
                from modules.shopee import TERMOS_REAIS_SHOPEE
                for termo in TERMOS_REAIS_SHOPEE:
                    if termo not in todos_produtos:
                        todos_produtos.append(termo)
            except Exception:
                pass
        
        produto_selecionado = st.selectbox(
            "Selecione o produto para divulgar",
            options=todos_produtos,
            key="divulgashop_select_produto"
        )
    
    with col_sel2:
        st.markdown("### 📱 Plataforma")
        plataforma = st.radio(
            "Escolha a plataforma de divulgação",
            ["💬 WhatsApp", "📨 Telegram", "📸 Instagram"],
            key="divulgashop_radio_plataforma"
        )
        
        st.markdown("### ⚙️ Opções")
        copiar_automatico = st.toggle(
            "📋 Texto pronto para copiar",
            value=True,
            key="divulgashop_toggle_copiar"
        )
        incluir_link = st.toggle(
            "🔗 Incluir link da Shopee",
            value=True,
            key="divulgashop_toggle_link"
        )
    
    # ============================================================
    # SEÇÃO 2: DADOS DO PRODUTO SELECIONADO
    # ============================================================
    st.markdown("---")
    st.markdown("### 📊 Informações do Produto")
    
    # Detecta categoria
    categoria = _detectar_categoria(produto_selecionado)
    
    # Busca dados enriquecidos
    dados_enriquecidos = {}
    try:
        for p in produtos_grade:
            if p.get("produto", "").lower() == produto_selecionado.lower():
                dados_enriquecidos = p
                break
    except Exception:
        pass
    
    if not dados_enriquecidos:
        dados_enriquecidos = {
            "produto": produto_selecionado,
            "categoria": categoria,
            "score": calcular_score_divulga(produto_selecionado),
            "fonte": "Shopee (Fallback)",
        }
    
    score = calcular_score_divulga(produto_selecionado, dados_enriquecidos)
    
    # Métricas visuais
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        if score >= 8:
            st.metric("🔥 Score", f"{score}/10", delta="Em alta")
        elif score >= 5:
            st.metric("⭐ Score", f"{score}/10", delta="Trending")
        else:
            st.metric("💡 Score", f"{score}/10", delta="Novidade")
    
    with col_m2:
        st.metric("🏷️ Categoria", categoria)
    
    with col_m3:
        fonte = dados_enriquecidos.get("fonte", "Shopee")
        st.metric("📡 Fonte", fonte)
    
    with col_m4:
        horario = "10h-12h / 19h-21h"
        st.metric("⏰ Melhor Horário", "10h-12h / 19h-21h")
    
    # Link Shopee
    link_shopee = gerar_link_shopee(produto_selecionado)
    st.markdown(f"**🔗 Link de busca Shopee:** [{produto_selecionado}]({link_shopee})")
    
    # ============================================================
    # SEÇÃO 3: GERAÇÃO DE CONTEÚDO
    # ============================================================
    st.markdown("---")
    st.markdown("### 🤖 Gerar Texto de Divulgação")
    
    if st.button(
        "🚀 Gerar Texto de Divulgação",
        type="primary",
        use_container_width=True,
        key="btn_gerar_texto_divulga"
    ):
        with st.spinner("🤖 Gerando texto otimizado para divulgação..."):
            time.sleep(0.8)  # Simula processamento
            
            # Gera o texto baseado na plataforma
            if "WhatsApp" in plataforma:
                texto = gerar_texto_whatsapp(
                    produto_selecionado, categoria, score, link_shopee
                )
                formato = "whatsapp"
            elif "Telegram" in plataforma:
                texto = gerar_texto_telegram(
                    produto_selecionado, categoria, score, link_shopee
                )
                formato = "telegram"
            else:
                texto = gerar_texto_instagram(
                    produto_selecionado, categoria, score, link_shopee
                )
                formato = "instagram"
            
            # Salva no cache
            _salvar_cache_divulga({
                "produto": produto_selecionado,
                "categoria": categoria,
                "score": score,
                "plataforma": formato,
                "texto": texto,
                "link": link_shopee,
                "timestamp": datetime.now().isoformat()
            })
            
            st.session_state["texto_divulga"] = texto
            st.session_state["produto_divulga"] = produto_selecionado
            st.session_state["plataforma_divulga"] = plataforma
        
        st.success("✅ Texto gerado com sucesso!")
    
    # ============================================================
    # SEÇÃO 4: EXIBIÇÃO DO TEXTO GERADO
    # ============================================================
    if "texto_divulga" in st.session_state and "produto_divulga" in st.session_state:
        st.markdown("---")
        st.markdown(f"### 📝 Texto para {st.session_state.get('plataforma_divulga', 'WhatsApp')}")
        
        texto = st.session_state["texto_divulga"]
        produto = st.session_state["produto_divulga"]
        plataforma_atual = st.session_state.get("plataforma_divulga", "WhatsApp")
        
        # Preview do texto
        st.markdown("#### Prévia do Texto")
        st.text_area(
            "Texto gerado (editável):",
            value=texto,
            height=350,
            key="divulgashop_text_area",
            label_visibility="collapsed"
        )
        
        # Botões de ação
        st.markdown("#### ⚡ Ações Rápidas")
        
        col_ac1, col_ac2, col_ac3, col_ac4 = st.columns(4)
        
        with col_ac1:
            if st.button("📋 Copiar Texto", use_container_width=True, key="btn_copiar_texto"):
                st.info("📋 Texto copiado! Cole no seu app de mensagens.")
                # Streamlit não tem clipboard nativo, então mostra instruções
                st.code(texto, language="text")
        
        with col_ac2:
            if st.button("🔄 Gerar Novamente", use_container_width=True, key="btn_gerar_novamente"):
                # Força nova geração
                st.session_state.pop("texto_divulga", None)
                st.rerun()
        
        with col_ac3:
            if st.button("💾 Salvar como Favorito", use_container_width=True, key="btn_salvar_fav"):
                favoritos = _ler_cache_divulga().get("favoritos", [])
                novo_fav = {
                    "produto": produto,
                    "plataforma": plataforma_atual,
                    "texto": texto,
                    "salvo_em": datetime.now().isoformat()
                }
                favoritos.insert(0, novo_fav)
                favoritos = favoritos[:20]  # Máximo 20 favoritos
                cache = _ler_cache_divulga()
                cache["favoritos"] = favoritos
                _salvar_cache_divulga(cache)
                st.success("✅ Salvo nos favoritos!")
        
        with col_ac4:
            st.download_button(
                "📥 Baixar TXT",
                data=texto,
                file_name=f"divulgacao_{produto_selecionado.replace(' ', '_').lower()}.txt",
                mime="text/plain",
                use_container_width=True,
                key="btn_download_txt"
            )
        
        # Link direto para copiar
        st.markdown("---")
        st.markdown("#### 🔗 Links Rápidos")
        
        col_link1, col_link2 = st.columns(2)
        
        with col_link1:
            st.markdown(f"**Link Shopee:** [{produto}]({link_shopee})")
            st.code(link_shopee, language="text")
        
        with col_link2:
            # Gera texto curto com link
            texto_curto = f"{produto_selecionado} - Compre: {link_shopee}"
            st.markdown("**Texto curto para copiar:**")
            st.code(texto_curto, language="text")
    
    # ============================================================
    # SEÇÃO 5: HISTÓRICO E FAVORITOS
    # ============================================================
    st.markdown("---")
    st.markdown("### 📁 Favoritos Salvos")
    
    cache = _ler_cache_divulga()
    favoritos = cache.get("favoritos", [])
    
    if favoritos:
        st.markdown(f"**{len(favoritos)} texto(s) salvo(s):**")
        
        for i, fav in enumerate(favoritos[:10]):
            produto_fav = fav.get("produto", "N/A")
            plataforma_fav = fav.get("plataforma", "whatsapp")
            salvo_em = fav.get("salvo_em", "N/A")
            texto_fav = fav.get("texto", "")
            
            with st.expander(f"{i+1}. 📦 {produto_fav} ({plataforma_fav}) — Salvo em {salvo_em[:10]}", expanded=False):
                st.text_area(
                    "Texto salvo:",
                    value=texto_fav,
                    height=150,
                    key=f"divulgashop_fav_{i}",
                    label_visibility="collapsed"
                )
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    if st.button("📋 Copiar", key=f"btn_copiar_fav_{i}"):
                        st.code(texto_fav, language="text")
                with col_f2:
                    if st.button("🗑️ Remover", key=f"btn_remover_fav_{i}"):
                        favoritos.pop(i)
                        cache["favoritos"] = favoritos
                        _salvar_cache_divulga(cache)
                        st.rerun()
    else:
        st.info("💡 Nenhum texto salvo ainda. Gere um texto e clique em 'Salvar como Favorito'.")
    
    # Botão para limpar todos os favoritos
    if favoritos and len(favoritos) > 5:
        if st.button("🗑️ Limpar todos os favoritos", key="btn_limpar_favoritos"):
            cache["favoritos"] = []
            _salvar_cache_divulga(cache)
            st.rerun()


__all__ = ["render_divulga_shop"]
