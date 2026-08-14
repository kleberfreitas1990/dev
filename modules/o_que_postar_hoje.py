"""
O Que Postar Hoje — Oportunidades de Marketplace.

A tela é deliberadamente limitada a dados de compra e busca com proveniência
identificada. Notícias, Google Trends, Pinterest, TikTok e métricas simuladas
não são exibidos como oportunidade comercial.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from modules.adult_content_filter import filtrar_lista_termos

logger = logging.getLogger(__name__)

DIRETORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(DIRETORIO_RAIZ, "o_que_postar_hoje_cache.json")
CACHE_TTL_HORAS = 2
MAX_IDADE_FONTE_HORAS = 48

FONTES_MARKETPLACE = (
    {
        "chave": "shopee",
        "arquivo": "shopee_daily_cache.json",
        "nome": "Shopee — Buscas em Alta",
        "origem_esperada": None,
        "url": "https://help.shopee.com.br/portal/10/article/163263-Como-encontrar-produtos-em-alta",
    },
    {
        "chave": "mercado_livre",
        "arquivo": "ml_trends_cache.json",
        "nome": "Mercado Livre — Tendências",
        "origem_esperada": "pagina_oficial",
        "url": "https://tendencias.mercadolivre.com.br/",
    },
    {
        "chave": "amazon",
        "arquivo": "amazon_trends.json",
        "nome": "Amazon Brasil — Mais Vendidos",
        "origem_esperada": "pagina_oficial",
        "url": "https://www.amazon.com.br/gp/bestsellers/",
    },
)

CATEGORIAS_COMERCIAIS = {
    "Moda": ("tênis", "tenis", "bolsa", "crocs", "biquíni", "biquini", "roupa", "sapato", "casaco"),
    "Beleza": ("pente", "perfume", "maquiagem", "cabelo", "skincare", "unha"),
    "Casa e Jardim": ("tapete", "mangueira", "garrafa", "botijão", "botijao", "cozinha", "sala", "jardim"),
    "Tecnologia e Games": ("nintendo", "switch", "ps5", "kindle", "celular", "xiaomi", "gabinete", "impressora", "drone"),
    "Automotivo": ("pneu", "multimídia", "multimidia", "fiat", "carro"),
    "Ferramentas": ("serra", "pedal", "ferramenta"),
    "Infantil": ("bebê", "bebe", "brinquedo", "photocard"),
}


def _ler_json(caminho: str) -> Dict[str, Any]:
    """Lê um cache estruturado sem fabricar dados quando a origem falha."""
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
        return conteudo if isinstance(conteudo, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError) as erro:
        logger.warning("Não foi possível ler cache de marketplace %s: %s", caminho, erro)
        return {}


def _parse_data(valor: Any) -> Optional[datetime]:
    """Converte os formatos de data dos caches para uma data comparável."""
    if not valor:
        return None
    texto = str(valor).strip()
    for formato in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def _data_payload(payload: Dict[str, Any]) -> Optional[datetime]:
    return _parse_data(payload.get("timestamp") or payload.get("data_coleta") or payload.get("data"))


def _formatar_data(data: Optional[datetime]) -> str:
    return data.strftime("%d/%m/%Y %H:%M") if data else "Data não informada"


def _fonte_atual(payload: Dict[str, Any]) -> bool:
    data = _data_payload(payload)
    return bool(data and (datetime.now() - data) <= timedelta(hours=MAX_IDADE_FONTE_HORAS))


def _classificar_produto(nome: str, categoria_origem: str = "") -> str:
    if categoria_origem and categoria_origem not in {"Não informada pela página de tendências", "Outros"}:
        return categoria_origem
    nome_normalizado = nome.lower()
    for categoria, palavras in CATEGORIAS_COMERCIAIS.items():
        if any(palavra in nome_normalizado for palavra in palavras):
            return categoria
    return "Outros"


def _dica_de_conteudo(nome: str, categoria: str) -> str:
    """Sugere um formato sem alegar sinais inexistentes de redes sociais."""
    if categoria == "Tecnologia e Games":
        return f"Mostre uso real, compatibilidade e comparação de {nome}."
    if categoria == "Casa e Jardim":
        return f"Demonstre a utilidade de {nome} em um problema do dia a dia."
    if categoria == "Moda":
        return f"Mostre variações, tamanho e combinação de {nome}."
    return f"Faça demonstração objetiva de {nome}, com benefício e chamada para a oferta."


def _status_fonte(configuracao: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    data = _data_payload(payload)
    if not payload:
        situacao = "Indisponível"
        criterio = "Sem cache de origem"
    elif configuracao["origem_esperada"] and payload.get("origem_coleta") != configuracao["origem_esperada"]:
        situacao = "Não verificada"
        criterio = "Origem oficial não confirmada"
    elif not _fonte_atual(payload):
        situacao = "Desatualizada"
        criterio = f"Cache acima de {MAX_IDADE_FONTE_HORAS}h"
    elif payload.get("status_coleta") not in (None, "sucesso"):
        situacao = "Indisponível"
        criterio = "Última coleta não foi bem-sucedida"
    else:
        situacao = "Atualizada"
        criterio = "Origem e data verificadas"

    itens = payload.get("termos") if configuracao["chave"] == "shopee" else payload.get("produtos", {})
    total = len(itens) if isinstance(itens, (list, dict)) else 0
    return {
        "fonte": configuracao["nome"],
        "situacao": situacao,
        "atualizado": _formatar_data(data),
        "itens_disponiveis": total,
        "criterio": criterio,
        "url": configuracao["url"],
    }


def _itens_shopee(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    termos = payload.get("termos", [])
    if not isinstance(termos, list):
        return []
    termos_filtrados = filtrar_lista_termos(termos)
    atualizado = _formatar_data(_data_payload(payload))
    resultado = []
    for posicao, termo in enumerate(termos_filtrados, start=1):
        nome = str(termo).strip()
        if not nome:
            continue
        categoria = _classificar_produto(nome)
        resultado.append({
            "produto": nome,
            "fonte": "Shopee — Buscas em Alta",
            "indicador": "Termo de busca em alta",
            "posicao": posicao,
            "categoria": categoria,
            "atualizado": atualizado,
            "origem": payload.get("fonte", "Rotina diária Shopee"),
            "dica_post": _dica_de_conteudo(nome, categoria),
        })
    return resultado


def _itens_ranking(payload: Dict[str, Any], nome_fonte: str) -> List[Dict[str, Any]]:
    produtos = payload.get("produtos", {})
    if not isinstance(produtos, dict):
        return []
    atualizado = _formatar_data(_data_payload(payload))
    resultado = []
    for nome, dados in produtos.items():
        if not isinstance(dados, dict):
            continue
        produto = str(nome).strip()
        if not produto:
            continue
        categoria = _classificar_produto(produto, str(dados.get("categoria", "")))
        posicao = dados.get("posicao_ranking")
        indicador = f"Posição #{posicao} no ranking" if posicao else str(dados.get("evento", "Destaque de marketplace"))
        resultado.append({
            "produto": produto,
            "fonte": nome_fonte,
            "indicador": indicador,
            "posicao": posicao if isinstance(posicao, int) else 9999,
            "categoria": categoria,
            "atualizado": atualizado,
            "origem": dados.get("origem_coleta", payload.get("origem_coleta", "Página oficial")),
            "dica_post": _dica_de_conteudo(produto, categoria),
        })
    return sorted(resultado, key=lambda item: item["posicao"])


def _cache_valido() -> bool:
    payload = _ler_json(CACHE_FILE)
    data = _parse_data(payload.get("timestamp"))
    return bool(data and (datetime.now() - data) < timedelta(hours=CACHE_TTL_HORAS))


def _salvar_cache(dados: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as arquivo:
            json.dump({"timestamp": datetime.now().isoformat(), "dados": dados}, arquivo, ensure_ascii=False, indent=2)
    except OSError as erro:
        logger.error("Não foi possível salvar cache da tela comercial: %s", erro)


def _carregar_cache() -> Optional[Dict[str, Any]]:
    return _ler_json(CACHE_FILE).get("dados")


def obter_sugestoes_do_dia(forcar_atualizacao: bool = False) -> Dict[str, Any]:
    """Retorna oportunidades comerciais apenas de fontes de marketplace atuais."""
    if not forcar_atualizacao and _cache_valido():
        dados_em_cache = _carregar_cache()
        if dados_em_cache:
            return dados_em_cache

    status_fontes: List[Dict[str, Any]] = []
    itens_marketplace: List[Dict[str, Any]] = []

    for configuracao in FONTES_MARKETPLACE:
        caminho = os.path.join(DIRETORIO_RAIZ, configuracao["arquivo"])
        payload = _ler_json(caminho)
        status = _status_fonte(configuracao, payload)
        status_fontes.append(status)
        if status["situacao"] != "Atualizada":
            logger.info("Fonte %s excluída da tela: %s", configuracao["nome"], status["criterio"])
            continue
        if configuracao["chave"] == "shopee":
            itens_marketplace.extend(_itens_shopee(payload))
        else:
            itens_marketplace.extend(_itens_ranking(payload, configuracao["nome"]))

    resultado = {
        "data": datetime.now().strftime("%d/%m/%Y"),
        "hora_geracao": datetime.now().strftime("%H:%M"),
        "itens_marketplace": itens_marketplace,
        "status_fontes": status_fontes,
        "total_oportunidades": len(itens_marketplace),
        "fontes_atualizadas": sum(1 for status in status_fontes if status["situacao"] == "Atualizada"),
    }
    _salvar_cache(resultado)
    return resultado


def render_o_que_postar_hoje() -> None:
    """Renderiza a tela exclusiva de oportunidades de marketplace."""
    import pandas as pd
    import streamlit as st

    st.markdown("## 🛒 O Que Vender e Postar Hoje")
    st.caption("Oportunidades de marketplace com origem e data verificáveis, atualizadas somente por fontes comerciais.")

    col_atualizar, col_info = st.columns([1, 3])
    with col_atualizar:
        if st.button("🔄 Atualizar fontes", key="btn_atualizar_postar", use_container_width=True):
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            st.rerun()
    with col_info:
        dados = obter_sugestoes_do_dia()
        st.info(
            f"📅 {dados.get('data', '?')} às {dados.get('hora_geracao', '?')} | "
            f"🛒 {dados.get('total_oportunidades', 0)} oportunidades verificadas | "
            f"✅ {dados.get('fontes_atualizadas', 0)} fonte(s) atualizada(s)"
        )

    st.markdown("---")
    st.markdown("### 🔥 Oportunidades de Marketplace")
    st.caption("Cada linha indica a fonte, o tipo de sinal comercial e a data da coleta. Nenhum volume, crescimento ou engajamento é inventado.")

    itens = dados.get("itens_marketplace", [])
    if itens:
        destaques = itens[:5]
        colunas = st.columns(min(5, len(destaques)))
        for indice, item in enumerate(destaques):
            with colunas[indice]:
                st.metric(f"#{indice + 1} {item['produto'][:20]}", item["indicador"], item["fonte"].split(" — ")[0])

        tabela = []
        for indice, item in enumerate(itens, start=1):
            tabela.append({
                "#": indice,
                "Produto / busca": item["produto"],
                "Marketplace": item["fonte"],
                "Sinal confirmado": item["indicador"],
                "Categoria": item["categoria"],
                "Atualizado em": item["atualizado"],
                "Ideia de conteúdo": item["dica_post"],
            })
        st.dataframe(pd.DataFrame(tabela), use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhuma fonte de marketplace atual e verificável está disponível neste momento. A tela não usa substitutos genéricos.")

    st.markdown("---")
    st.markdown("### 🔎 Status das fontes comerciais")
    st.caption("Fontes desatualizadas ou sem origem oficial confirmada são exibidas aqui, mas não entram nas oportunidades.")
    status_fontes = dados.get("status_fontes", [])
    if status_fontes:
        tabela_status = [{
            "Fonte": status["fonte"],
            "Situação": status["situacao"],
            "Última coleta": status["atualizado"],
            "Itens no cache": status["itens_disponiveis"],
            "Critério": status["criterio"],
        } for status in status_fontes]
        st.dataframe(pd.DataFrame(tabela_status), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### ✍️ Como transformar o sinal em post")
    st.caption("Use o produto e a fonte mostrados acima. Faça demonstração, comparação ou lista de benefícios e mantenha a comunicação vinculada ao sinal comercial disponível.")
