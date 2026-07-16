"""
Histórico de Tendências — Minerador de Produtos v9.5.

Persiste snapshots do Top 10 em SQLite e identifica produtos que permanecem
no ranking por múltiplos ciclos consecutivos. O módulo usa apenas a biblioteca
padrão e pode ser testado sem dependência do Streamlit.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import unicodedata
from contextlib import closing
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

DIRETORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_BANCO_HISTORICO = os.path.join(DIRETORIO_RAIZ, "historico_tendencias.db")


def _conectar(caminho_banco: Optional[str] = None) -> sqlite3.Connection:
    conexao = sqlite3.connect(caminho_banco or CAMINHO_BANCO_HISTORICO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.execute("PRAGMA journal_mode = WAL")
    return conexao


def inicializar_banco(caminho_banco: Optional[str] = None) -> None:
    """Cria as tabelas e índices necessários, caso ainda não existam."""
    with closing(_conectar(caminho_banco)) as conexao:
        conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS ciclos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capturado_em TEXT NOT NULL,
                origem TEXT NOT NULL,
                assinatura TEXT NOT NULL UNIQUE,
                total_itens INTEGER NOT NULL CHECK (total_itens >= 0)
            );

            CREATE TABLE IF NOT EXISTS itens_ciclo (
                ciclo_id INTEGER NOT NULL,
                posicao INTEGER NOT NULL,
                produto_chave TEXT NOT NULL,
                produto TEXT NOT NULL,
                fonte TEXT,
                categoria TEXT,
                score REAL,
                crescimento REAL,
                tendencia TEXT,
                atualizado TEXT,
                PRIMARY KEY (ciclo_id, posicao),
                UNIQUE (ciclo_id, produto_chave),
                FOREIGN KEY (ciclo_id) REFERENCES ciclos(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_itens_produto
                ON itens_ciclo(produto_chave, ciclo_id);
            CREATE INDEX IF NOT EXISTS idx_ciclos_data
                ON ciclos(capturado_em DESC, id DESC);
            """
        )
        conexao.commit()


def normalizar_produto(nome: Any) -> str:
    """Gera uma chave estável, sem acentos e insensível a caixa."""
    texto = unicodedata.normalize("NFKD", str(nome or ""))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()
    return re.sub(r"\s+", " ", texto)


def _numero(valor: Any) -> float:
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor or "").strip().lower().replace("+", "").replace("%", "")
    multiplicador = 1_000.0 if texto.endswith("k") else 1.0
    texto = texto.rstrip("k").replace(".", "").replace(",", ".")
    try:
        return float(texto) * multiplicador
    except (TypeError, ValueError):
        return 0.0


def _preparar_itens(top10: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    itens: List[Dict[str, Any]] = []
    chaves_vistas = set()

    for item in list(top10)[:10]:
        produto = str(item.get("Produto") or item.get("produto") or "").strip()
        produto_chave = normalizar_produto(produto)
        if not produto_chave or produto_chave in chaves_vistas:
            continue
        chaves_vistas.add(produto_chave)
        itens.append(
            {
                "posicao": len(itens) + 1,
                "produto_chave": produto_chave,
                "produto": produto,
                "fonte": str(item.get("Fonte") or item.get("fonte") or ""),
                "categoria": str(item.get("Categoria") or item.get("categoria") or "Geral"),
                "score": _numero(item.get("Score", item.get("score", 0))),
                "crescimento": _numero(item.get("Crescimento", item.get("crescimento", 0))),
                "tendencia": str(item.get("Tendência") or item.get("tendencia") or ""),
                "atualizado": str(item.get("Atualizado") or item.get("atualizado") or ""),
            }
        )
    return itens


def _assinatura_snapshot(itens: List[Dict[str, Any]]) -> str:
    """Assina dados relevantes para impedir duplicação em reruns do Streamlit."""
    conteudo = [
        {
            "posicao": item["posicao"],
            "produto": item["produto_chave"],
            "fonte": item["fonte"],
            "score": item["score"],
            "crescimento": item["crescimento"],
            "atualizado": item["atualizado"],
        }
        for item in itens
    ]
    serializado = json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def registrar_ciclo(
    top10: Iterable[Dict[str, Any]],
    origem: str = "automatico",
    capturado_em: Optional[datetime] = None,
    caminho_banco: Optional[str] = None,
) -> Dict[str, Any]:
    """Registra um snapshot do Top 10; snapshots idênticos são ignorados."""
    itens = _preparar_itens(top10)
    if not itens:
        return {"registrado": False, "motivo": "ranking_vazio", "ciclo_id": None, "total_itens": 0}

    inicializar_banco(caminho_banco)
    assinatura = _assinatura_snapshot(itens)
    data_captura = (capturado_em or datetime.now()).isoformat(timespec="seconds")

    with closing(_conectar(caminho_banco)) as conexao:
        existente = conexao.execute(
            "SELECT id FROM ciclos WHERE assinatura = ?", (assinatura,)
        ).fetchone()
        if existente:
            return {
                "registrado": False,
                "motivo": "snapshot_duplicado",
                "ciclo_id": existente["id"],
                "total_itens": len(itens),
            }

        cursor = conexao.execute(
            "INSERT INTO ciclos (capturado_em, origem, assinatura, total_itens) VALUES (?, ?, ?, ?)",
            (data_captura, origem, assinatura, len(itens)),
        )
        ciclo_id = int(cursor.lastrowid)
        conexao.executemany(
            """
            INSERT INTO itens_ciclo (
                ciclo_id, posicao, produto_chave, produto, fonte, categoria,
                score, crescimento, tendencia, atualizado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    ciclo_id,
                    item["posicao"],
                    item["produto_chave"],
                    item["produto"],
                    item["fonte"],
                    item["categoria"],
                    item["score"],
                    item["crescimento"],
                    item["tendencia"],
                    item["atualizado"],
                )
                for item in itens
            ],
        )
        conexao.commit()

    return {
        "registrado": True,
        "motivo": "novo_snapshot",
        "ciclo_id": ciclo_id,
        "total_itens": len(itens),
    }


def listar_ciclos(limite: int = 100, caminho_banco: Optional[str] = None) -> List[Dict[str, Any]]:
    inicializar_banco(caminho_banco)
    with closing(_conectar(caminho_banco)) as conexao:
        linhas = conexao.execute(
            """
            SELECT id, capturado_em, origem, total_itens
            FROM ciclos
            ORDER BY capturado_em DESC, id DESC
            LIMIT ?
            """,
            (max(1, int(limite)),),
        ).fetchall()
    return [dict(linha) for linha in linhas]


def obter_produtos_persistentes(
    minimo_ciclos: int = 3,
    caminho_banco: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retorna produtos do ciclo mais recente e sua sequência consecutiva atual."""
    ciclos = listar_ciclos(limite=500, caminho_banco=caminho_banco)
    if not ciclos:
        return []

    ids_ciclos = [ciclo["id"] for ciclo in ciclos]
    placeholders = ",".join("?" for _ in ids_ciclos)
    with closing(_conectar(caminho_banco)) as conexao:
        linhas = conexao.execute(
            f"""
            SELECT ciclo_id, posicao, produto_chave, produto, fonte, categoria,
                   score, crescimento, tendencia, atualizado
            FROM itens_ciclo
            WHERE ciclo_id IN ({placeholders})
            """,
            ids_ciclos,
        ).fetchall()

    por_ciclo: Dict[int, Dict[str, Dict[str, Any]]] = {ciclo_id: {} for ciclo_id in ids_ciclos}
    aparicoes: Dict[str, int] = {}
    for linha in linhas:
        item = dict(linha)
        por_ciclo[item["ciclo_id"]][item["produto_chave"]] = item
        aparicoes[item["produto_chave"]] = aparicoes.get(item["produto_chave"], 0) + 1

    ciclo_atual = ids_ciclos[0]
    resultados: List[Dict[str, Any]] = []
    for chave, item_atual in por_ciclo[ciclo_atual].items():
        sequencia = 0
        for ciclo_id in ids_ciclos:
            if chave not in por_ciclo[ciclo_id]:
                break
            sequencia += 1

        if sequencia < max(1, int(minimo_ciclos)):
            continue

        resultados.append(
            {
                "Produto": item_atual["produto"],
                "Fonte": item_atual["fonte"],
                "Categoria": item_atual["categoria"],
                "Posição Atual": item_atual["posicao"],
                "Score Atual": item_atual["score"],
                "Crescimento Atual %": item_atual["crescimento"],
                "Ciclos Consecutivos": sequencia,
                "Aparições Totais": aparicoes.get(chave, 0),
            }
        )

    return sorted(
        resultados,
        key=lambda item: (
            item["Ciclos Consecutivos"],
            item["Score Atual"],
            -item["Posição Atual"],
        ),
        reverse=True,
    )


def obter_evolucao_produto(
    produto: str,
    caminho_banco: Optional[str] = None,
) -> List[Dict[str, Any]]:
    inicializar_banco(caminho_banco)
    chave = normalizar_produto(produto)
    with closing(_conectar(caminho_banco)) as conexao:
        linhas = conexao.execute(
            """
            SELECT c.id AS ciclo_id, c.capturado_em, c.origem,
                   i.posicao, i.produto, i.fonte, i.categoria,
                   i.score, i.crescimento, i.tendencia, i.atualizado
            FROM itens_ciclo i
            JOIN ciclos c ON c.id = i.ciclo_id
            WHERE i.produto_chave = ?
            ORDER BY c.capturado_em ASC, c.id ASC
            """,
            (chave,),
        ).fetchall()
    return [dict(linha) for linha in linhas]


def obter_resumo(caminho_banco: Optional[str] = None) -> Dict[str, Any]:
    inicializar_banco(caminho_banco)
    with closing(_conectar(caminho_banco)) as conexao:
        resumo = conexao.execute(
            """
            SELECT COUNT(*) AS total_ciclos,
                   COALESCE(SUM(total_itens), 0) AS total_snapshots,
                   MAX(capturado_em) AS ultimo_ciclo
            FROM ciclos
            """
        ).fetchone()
        produtos_unicos = conexao.execute(
            "SELECT COUNT(DISTINCT produto_chave) AS total FROM itens_ciclo"
        ).fetchone()["total"]

    return {
        "total_ciclos": int(resumo["total_ciclos"]),
        "total_snapshots": int(resumo["total_snapshots"]),
        "produtos_unicos": int(produtos_unicos),
        "ultimo_ciclo": resumo["ultimo_ciclo"],
    }


def render_historico_tendencias() -> None:
    """Renderiza o painel Streamlit do histórico e da permanência no ranking."""
    import pandas as pd
    import streamlit as st

    st.markdown("## 📈 Histórico de Tendências")
    st.caption(
        "Snapshots reais do Top 10 registrados após cada atualização. "
        "Produtos persistentes permanecem no ranking por ciclos consecutivos."
    )

    resumo = obter_resumo()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ciclos registrados", resumo["total_ciclos"])
    col2.metric("Snapshots de produtos", resumo["total_snapshots"])
    col3.metric("Produtos únicos", resumo["produtos_unicos"])
    col4.metric("Último ciclo", (resumo["ultimo_ciclo"] or "Ainda não registrado").replace("T", " "))

    col_filtro, col_acao = st.columns([3, 1])
    with col_filtro:
        minimo_ciclos = st.slider(
            "Permanência mínima no Top 10",
            min_value=2,
            max_value=10,
            value=3,
            help="Quantidade de ciclos consecutivos, incluindo o ciclo atual.",
            key="historico_minimo_ciclos",
        )
    with col_acao:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Registrar snapshot atual", width="stretch", key="historico_registrar_atual"):
            from modules.models import gerar_top10_produtos

            resultado = registrar_ciclo(gerar_top10_produtos(False), origem="manual")
            if resultado["registrado"]:
                st.success(f"Ciclo #{resultado['ciclo_id']} registrado com sucesso.")
                st.rerun()
            elif resultado["motivo"] == "snapshot_duplicado":
                st.info("O ranking atual já está registrado; nenhum ciclo duplicado foi criado.")
            else:
                st.warning("Não foi possível registrar um ranking vazio.")

    if resumo["total_ciclos"] == 0:
        st.info(
            "O histórico começará na próxima atualização automática. "
            "Use o botão acima para registrar o ranking atual agora."
        )
        return

    persistentes = obter_produtos_persistentes(minimo_ciclos=minimo_ciclos)
    st.markdown(f"### Produtos persistentes — {minimo_ciclos}+ ciclos")
    if not persistentes:
        st.info("Ainda não há produtos com essa permanência no ciclo atual.")
        ciclos = pd.DataFrame(listar_ciclos(limite=20))
        st.markdown("### Ciclos recentes")
        st.dataframe(ciclos, width="stretch", hide_index=True)
        return

    df_persistentes = pd.DataFrame(persistentes)
    st.dataframe(
        df_persistentes,
        width="stretch",
        hide_index=True,
        column_config={
            "Posição Atual": st.column_config.NumberColumn("Posição", format="#%d"),
            "Score Atual": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=10, format="%.1f/10"
            ),
            "Crescimento Atual %": st.column_config.NumberColumn("Crescimento", format="+%.1f%%"),
            "Ciclos Consecutivos": st.column_config.NumberColumn("Ciclos seguidos", format="%d"),
            "Aparições Totais": st.column_config.NumberColumn("Aparições", format="%d"),
        },
    )

    produto_selecionado = st.selectbox(
        "Ver evolução de um produto persistente",
        [item["Produto"] for item in persistentes],
        key="historico_produto_evolucao",
    )
    evolucao = obter_evolucao_produto(produto_selecionado)
    if evolucao:
        df_evolucao = pd.DataFrame(evolucao)
        df_evolucao["capturado_em"] = pd.to_datetime(df_evolucao["capturado_em"], errors="coerce")
        st.markdown(f"#### Evolução — {produto_selecionado}")
        st.line_chart(
            df_evolucao.set_index("capturado_em")[["score"]],
            y_label="Score",
            x_label="Ciclo",
        )
        st.dataframe(
            df_evolucao[["capturado_em", "posicao", "score", "crescimento", "fonte", "tendencia"]],
            width="stretch",
            hide_index=True,
        )


__all__ = [
    "CAMINHO_BANCO_HISTORICO",
    "inicializar_banco",
    "normalizar_produto",
    "registrar_ciclo",
    "listar_ciclos",
    "obter_produtos_persistentes",
    "obter_evolucao_produto",
    "obter_resumo",
    "render_historico_tendencias",
]
