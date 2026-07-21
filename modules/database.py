"""
Módulo de Banco de Dados SQLite — Minerador de Produtos v9.9
=============================================================
Substitui os arquivos JSON por um banco relacional para:
- Caches de tendências (ML, Amazon, Shopee, Google)
- Histórico de tendências (snapshots do Top 10 ao longo do tempo)
- Pedidos da Pedreira (fluxo de compras)
- Logs de buscas
- Histórico de atualizações automáticas

Design:
- Migrações automáticas no primeiro acesso
- Camada de compatibilidade: as funções públicas retornam os mesmos
  dicts que os módulos antigos, então a grade e telas não precisam
  de alteração externa.
- Fallback: se o SQLite falhar, os JSONs originais continuam servindo.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
DIRETORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DIRETORIO_RAIZ, "minerador.db")
DB_VERSION = 3  # Bumpar quando houver schema change

# ============================================================
# CONEXÃO THREAD-SAFE
# ============================================================
_local = threading_local = None


@contextmanager
def _get_connection():
    """Retorna uma conexão SQLite com WAL e foreign keys habilitados."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# SCHEMA — MIGRAÇÕES AUTOMÁTICAS
# ============================================================
_SCHEMA_DDL = """
-- Versão do schema
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cache de tendências do Mercado Livre
CREATE TABLE IF NOT EXISTS ml_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_nome TEXT NOT NULL,
    categoria TEXT,
    categoria_origem TEXT DEFAULT 'Não informada pela página de tendências',
    evento TEXT DEFAULT 'Termo mais procurado no Mercado Livre',
    tendencia TEXT DEFAULT 'Em destaque',
    score INTEGER DEFAULT 0,
    posicao_ranking INTEGER DEFAULT 0,
    atualizado TEXT,
    fonte TEXT DEFAULT 'Mercado Livre Trends',
    origem_coleta TEXT DEFAULT 'pagina_oficial',
    url_fonte TEXT DEFAULT 'https://tendencias.mercadolivre.com.br/',
    ciclo_id TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Metadados do ciclo de coleta ML
CREATE TABLE IF NOT EXISTS ml_ciclos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ciclo_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    total INTEGER DEFAULT 0,
    fonte TEXT DEFAULT 'Mercado Livre Trends',
    url_fonte TEXT DEFAULT 'https://tendencias.mercadolivre.com.br/',
    origem_coleta TEXT DEFAULT 'pagina_oficial',
    status_coleta TEXT DEFAULT 'sucesso',
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cache de tendências da Amazon
CREATE TABLE IF NOT EXISTS amazon_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_nome TEXT NOT NULL,
    categoria TEXT,
    categoria_origem TEXT DEFAULT 'Não informada na lista geral de Best Sellers',
    evento TEXT DEFAULT 'Produto listado em Best Sellers Amazon Brasil',
    tendencia TEXT DEFAULT 'Mais vendido',
    score INTEGER DEFAULT 0,
    posicao_ranking INTEGER DEFAULT 0,
    url_produto TEXT,
    atualizado TEXT,
    fonte TEXT DEFAULT 'Amazon Bestsellers',
    origem_coleta TEXT DEFAULT 'pagina_oficial',
    url_fonte TEXT DEFAULT 'https://www.amazon.com.br/gp/bestsellers/',
    ciclo_id TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Metadados do ciclo de coleta Amazon
CREATE TABLE IF NOT EXISTS amazon_ciclos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ciclo_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    total INTEGER DEFAULT 0,
    fonte TEXT DEFAULT 'Amazon Bestsellers',
    url_fonte TEXT DEFAULT 'https://www.amazon.com.br/gp/bestsellers/',
    origem_coleta TEXT DEFAULT 'pagina_oficial',
    status_coleta TEXT DEFAULT 'sucesso',
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cache de tendências da Shopee
CREATE TABLE IF NOT EXISTS shopee_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termo TEXT NOT NULL,
    vendas TEXT,
    avaliacao TEXT,
    preco TEXT,
    categoria TEXT,
    fonte TEXT DEFAULT 'Shopee Trending',
    origem_coleta TEXT DEFAULT 'cache_shopee_live',
    atualizado TEXT,
    ciclo_id TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cache de tendências do Google Trends
CREATE TABLE IF NOT EXISTS google_trends_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termo TEXT NOT NULL,
    interesse INTEGER DEFAULT 0,
    variacao TEXT,
    categoria TEXT,
    trafego TEXT,
    fonte TEXT DEFAULT 'Google Trends',
    origem_coleta TEXT DEFAULT 'pytrends',
    atualizado TEXT,
    ciclo_id TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Histórico de tendências (snapshots do Top 10)
CREATE TABLE IF NOT EXISTS historico_tendencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ciclo_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    origem TEXT DEFAULT 'sistema',
    dados_json TEXT NOT NULL,
    total_produtos INTEGER DEFAULT 0,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Pedidos da Pedreira
CREATE TABLE IF NOT EXISTS pedreira_pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto TEXT NOT NULL,
    quantidade INTEGER DEFAULT 1,
    solicitante TEXT,
    atendente TEXT,
    empresa TEXT DEFAULT 'N/A',
    status TEXT DEFAULT 'pendente',
    observacoes TEXT,
    data_solicitacao TEXT NOT NULL DEFAULT (datetime('now')),
    data_atualizacao TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Logs de buscas
CREATE TABLE IF NOT EXISTS buscas_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    nivel TEXT DEFAULT 'info',
    termo TEXT,
    sucesso INTEGER DEFAULT 1,
    quantidade INTEGER DEFAULT 0,
    tempo_execucao REAL DEFAULT 0.0,
    detalhes TEXT,
    erro TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Histórico de atualizações automáticas
CREATE TABLE IF NOT EXISTS auto_update_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    data_formatada TEXT,
    tipo TEXT DEFAULT 'automatica',
    sucesso INTEGER DEFAULT 1,
    tempo_segundos REAL DEFAULT 0.0,
    detalhes_json TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cache de produtos agregados (compatibilidade com produtos_cache_v48.json)
CREATE TABLE IF NOT EXISTS produtos_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_nome TEXT UNIQUE NOT NULL,
    dados_json TEXT NOT NULL,
    fonte TEXT,
    atualizado TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Índices para performance
_INDICES_DDL = """
CREATE INDEX IF NOT EXISTS idx_ml_cache_ciclo ON ml_cache(ciclo_id);
CREATE INDEX IF NOT EXISTS idx_amazon_cache_ciclo ON amazon_cache(ciclo_id);
CREATE INDEX IF NOT EXISTS idx_shopee_cache_ciclo ON shopee_cache(ciclo_id);
CREATE INDEX IF NOT EXISTS idx_google_cache_ciclo ON google_trends_cache(ciclo_id);
CREATE INDEX IF NOT EXISTS idx_ml_cache_nome ON ml_cache(produto_nome);
CREATE INDEX IF NOT EXISTS idx_amazon_cache_nome ON amazon_cache(produto_nome);
CREATE INDEX IF NOT EXISTS idx_pedreira_status ON pedreira_pedidos(status);
CREATE INDEX IF NOT EXISTS idx_buscas_termo ON buscas_logs(termo);
CREATE INDEX IF NOT EXISTS idx_buscas_timestamp ON buscas_logs(timestamp);
"""


# ============================================================
# INICIALIZAÇÃO E MIGRAÇÃO
# ============================================================
def inicializar_db() -> bool:
    """Cria o banco e aplica migrações. Retorna True se tudo ok."""
    try:
        with _get_connection() as conn:
            conn.executescript(_SCHEMA_DDL)
            conn.executescript(_INDICES_DDL)

            # Registra a versão atual
            cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            if not row or row["version"] < DB_VERSION:
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (DB_VERSION,),
                )
                logger.info(f"Database v{DB_VERSION} inicializada em {DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Falha ao inicializar banco de dados: {e}")
        return False


def verificar_db() -> bool:
    """Verifica se o banco existe e está íntegro."""
    if not os.path.exists(DB_PATH):
        return inicializar_db()
    try:
        with _get_connection() as conn:
            conn.execute("SELECT 1 FROM schema_version LIMIT 1")
        return True
    except Exception:
        return inicializar_db()


# ============================================================
# MERCADO LIVRE — CACHE
# ============================================================
def salvar_ml_ciclo(produtos: Dict[str, Any]) -> str:
    """Salva um ciclo completo de coleta do ML. Retorna o ciclo_id."""
    ciclo_id = f"ml_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with _get_connection() as conn:
        conn.execute(
            """INSERT INTO ml_ciclos (ciclo_id, timestamp, total, fonte, url_fonte, origem_coleta, status_coleta)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ciclo_id, datetime.now().isoformat(), len(produtos),
             "Mercado Livre Trends", "https://tendencias.mercadolivre.com.br/",
             "pagina_oficial", "sucesso"),
        )
        for nome, dados in produtos.items():
            conn.execute(
                """INSERT INTO ml_cache
                   (produto_nome, categoria, categoria_origem, evento, tendencia, score,
                    posicao_ranking, atualizado, fonte, origem_coleta, url_fonte, ciclo_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    nome,
                    dados.get("categoria", ""),
                    dados.get("categoria_origem", ""),
                    dados.get("evento", ""),
                    dados.get("tendencia", ""),
                    dados.get("score", 0),
                    dados.get("posicao_ranking", 0),
                    dados.get("atualizado", ""),
                    dados.get("fonte", "Mercado Livre Trends"),
                    dados.get("origem_coleta", "pagina_oficial"),
                    dados.get("url_fonte", "https://tendencias.mercadolivre.com.br/"),
                    ciclo_id,
                ),
            )
    return ciclo_id


def obter_ml_ciclo_atual() -> Dict[str, Any]:
    """Retorna o último ciclo ML como dict no formato do JSON original."""
    with _get_connection() as conn:
        # Pega o último ciclo
        cursor = conn.execute(
            "SELECT * FROM ml_ciclos ORDER BY id DESC LIMIT 1"
        )
        ciclo = cursor.fetchone()
        if not ciclo:
            return {}

        # Pega os produtos do último ciclo
        cursor = conn.execute(
            """SELECT produto_nome, categoria, categoria_origem, evento, tendencia,
                      score, posicao_ranking, atualizado, fonte, origem_coleta, url_fonte
               FROM ml_cache
               WHERE ciclo_id = ?
               ORDER BY posicao_ranking""",
            (ciclo["ciclo_id"],),
        )
        produtos = {}
        for row in cursor.fetchall():
            produtos[row["produto_nome"]] = {
                "pins": 0,
                "pins_historico": 0,
                "crescimento": 0,
                "crescimento_real": False,
                "views_tiktok": 0,
                "resultados_ml": 0,
                "buscas_mes": 0,
                "buscas_historico": 0,
                "categoria": row["categoria"],
                "categoria_origem": row["categoria_origem"],
                "evento": row["evento"],
                "variacao": 0,
                "tendencia": row["tendencia"],
                "score": row["score"],
                "fonte": row["fonte"],
                "origem_coleta": row["origem_coleta"],
                "url_fonte": row["url_fonte"],
                "posicao_ranking": row["posicao_ranking"],
                "atualizado": row["atualizado"],
            }

        return {
            "timestamp": ciclo["timestamp"],
            "data": datetime.fromisoformat(ciclo["timestamp"]).date().isoformat() if ciclo["timestamp"] else "",
            "total": ciclo["total"],
            "fonte": ciclo["fonte"],
            "url_fonte": ciclo["url_fonte"],
            "origem_coleta": ciclo["origem_coleta"],
            "status_coleta": ciclo["status_coleta"],
            "produtos": produtos,
        }


def ml_cache_valido() -> bool:
    """Verifica se o último ciclo ML está dentro do TTL de 6h."""
    from datetime import timedelta
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT timestamp FROM ml_ciclos ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if not row:
            return False
        try:
            ts = datetime.fromisoformat(row["timestamp"])
            return (datetime.now() - ts) < timedelta(hours=6)
        except (ValueError, TypeError):
            return False


def limpar_ml_cache_antigos(max_ciclos: int = 10) -> int:
    """Remove ciclos ML antigos, mantendo apenas os N mais recentes."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT ciclo_id FROM ml_ciclos ORDER BY id DESC LIMIT ?, 999999",
            (max_ciclos,),
        )
        ids_para_remover = [row["ciclo_id"] for row in cursor.fetchall()]
        if not ids_para_remover:
            return 0
        placeholders = ",".join("?" * len(ids_para_remover))
        conn.execute(f"DELETE FROM ml_cache WHERE ciclo_id IN ({placeholders})", ids_para_remover)
        conn.execute(f"DELETE FROM ml_ciclos WHERE ciclo_id IN ({placeholders})", ids_para_remover)
    return len(ids_para_remover)


# ============================================================
# AMAZON — CACHE
# ============================================================
def salvar_amazon_ciclo(produtos: Dict[str, Any]) -> str:
    """Salva um ciclo completo de coleta da Amazon. Retorna o ciclo_id."""
    ciclo_id = f"amazon_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with _get_connection() as conn:
        conn.execute(
            """INSERT INTO amazon_ciclos (ciclo_id, timestamp, total, fonte, url_fonte, origem_coleta, status_coleta)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ciclo_id, datetime.now().isoformat(), len(produtos),
             "Amazon Bestsellers", "https://www.amazon.com.br/gp/bestsellers/",
             "pagina_oficial", "sucesso"),
        )
        for nome, dados in produtos.items():
            conn.execute(
                """INSERT INTO amazon_cache
                   (produto_nome, categoria, categoria_origem, evento, tendencia, score,
                    posicao_ranking, url_produto, atualizado, fonte, origem_coleta, url_fonte, ciclo_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    nome,
                    dados.get("categoria", ""),
                    dados.get("categoria_origem", ""),
                    dados.get("evento", ""),
                    dados.get("tendencia", ""),
                    dados.get("score", 0),
                    dados.get("posicao_ranking", 0),
                    dados.get("url_produto", ""),
                    dados.get("atualizado", ""),
                    dados.get("fonte", "Amazon Bestsellers"),
                    dados.get("origem_coleta", "pagina_oficial"),
                    dados.get("url_fonte", "https://www.amazon.com.br/gp/bestsellers/"),
                    ciclo_id,
                ),
            )
    return ciclo_id


def obter_amazon_ciclo_atual() -> Dict[str, Any]:
    """Retorna o último ciclo Amazon como dict no formato do JSON original."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM amazon_ciclos ORDER BY id DESC LIMIT 1"
        )
        ciclo = cursor.fetchone()
        if not ciclo:
            return {}

        cursor = conn.execute(
            """SELECT produto_nome, categoria, categoria_origem, evento, tendencia,
                      score, posicao_ranking, url_produto, atualizado, fonte, origem_coleta, url_fonte
               FROM amazon_cache
               WHERE ciclo_id = ?
               ORDER BY posicao_ranking""",
            (ciclo["ciclo_id"],),
        )
        produtos = {}
        for row in cursor.fetchall():
            produtos[row["produto_nome"]] = {
                "pins": 0,
                "pins_historico": 0,
                "crescimento": 0,
                "crescimento_real": False,
                "views_tiktok": 0,
                "resultados_ml": 0,
                "buscas_mes": 0,
                "buscas_historico": 0,
                "categoria": row["categoria"],
                "categoria_origem": row["categoria_origem"],
                "evento": row["evento"],
                "variacao": 0,
                "tendencia": row["tendencia"],
                "score": row["score"],
                "fonte": row["fonte"],
                "origem_coleta": row["origem_coleta"],
                "url_fonte": row["url_fonte"],
                "url_produto": row["url_produto"],
                "posicao_ranking": row["posicao_ranking"],
                "atualizado": row["atualizado"],
            }

        return {
            "timestamp": ciclo["timestamp"],
            "data": datetime.fromisoformat(ciclo["timestamp"]).date().isoformat() if ciclo["timestamp"] else "",
            "total": ciclo["total"],
            "fonte": ciclo["fonte"],
            "url_fonte": ciclo["url_fonte"],
            "origem_coleta": ciclo["origem_coleta"],
            "status_coleta": ciclo["status_coleta"],
            "produtos": produtos,
        }


def amazon_cache_valido() -> bool:
    """Verifica se o último ciclo Amazon está dentro do TTL de 12h."""
    from datetime import timedelta
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT timestamp FROM amazon_ciclos ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if not row:
            return False
        try:
            ts = datetime.fromisoformat(row["timestamp"])
            return (datetime.now() - ts) < timedelta(hours=12)
        except (ValueError, TypeError):
            return False


def limpar_amazon_cache_antigos(max_ciclos: int = 10) -> int:
    """Remove ciclos Amazon antigos, mantendo apenas os N mais recentes."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT ciclo_id FROM amazon_ciclos ORDER BY id DESC LIMIT ?, 999999",
            (max_ciclos,),
        )
        ids_para_remover = [row["ciclo_id"] for row in cursor.fetchall()]
        if not ids_para_remover:
            return 0
        placeholders = ",".join("?" * len(ids_para_remover))
        conn.execute(f"DELETE FROM amazon_cache WHERE ciclo_id IN ({placeholders})", ids_para_remover)
        conn.execute(f"DELETE FROM amazon_ciclos WHERE ciclo_id IN ({placeholders})", ids_para_remover)
    return len(ids_para_remover)


# ============================================================
# SHOPEE — CACHE
# ============================================================
def salvar_shopee_ciclo(itens: List[Dict[str, Any]]) -> str:
    """Salva um ciclo de coleta da Shopee."""
    ciclo_id = f"shopee_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with _get_connection() as conn:
        for item in itens:
            conn.execute(
                """INSERT INTO shopee_cache
                   (termo, vendas, avaliacao, preco, categoria, fonte, origem_coleta, atualizado, ciclo_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.get("termo", ""),
                    item.get("vendas", ""),
                    item.get("avaliacao", ""),
                    item.get("preco", ""),
                    item.get("categoria", ""),
                    item.get("fonte", "Shopee Trending"),
                    item.get("origem_coleta", "cache_shopee_live"),
                    item.get("atualizado", ""),
                    ciclo_id,
                ),
            )
    return ciclo_id


def obter_shopee_ciclo_atual() -> List[Dict[str, Any]]:
    """Retorna os itens do último ciclo Shopee."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """SELECT sh.ciclo_id, ac.timestamp
               FROM shopee_cache sh
               INNER JOIN (SELECT ciclo_id, MAX(timestamp) as timestamp FROM shopee_cache GROUP BY 1) ac
               ON sh.ciclo_id = ac.ciclo_id
               ORDER BY ac.timestamp DESC
               LIMIT 1"""
        )
        # Simplificado: pegar o último ciclo
        cursor = conn.execute(
            "SELECT ciclo_id FROM shopee_cache ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if not row:
            return []

        cursor = conn.execute(
            """SELECT termo, vendas, avaliacao, preco, categoria, fonte, origem_coleta, atualizado
               FROM shopee_cache WHERE ciclo_id = ?""",
            (row["ciclo_id"],),
        )
        return [dict(r) for r in cursor.fetchall()]


# ============================================================
# GOOGLE TRENDS — CACHE
# ============================================================
def salvar_google_trends_ciclo(itens: List[Dict[str, Any]]) -> str:
    """Salva um ciclo de coleta do Google Trends."""
    ciclo_id = f"google_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with _get_connection() as conn:
        for item in itens:
            conn.execute(
                """INSERT INTO google_trends_cache
                   (termo, interesse, variacao, categoria, trafego, fonte, origem_coleta, atualizado, ciclo_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.get("termo", ""),
                    item.get("interesse", 0),
                    item.get("variacao", ""),
                    item.get("categoria", ""),
                    item.get("trafego", ""),
                    item.get("fonte", "Google Trends"),
                    item.get("origem_coleta", "pytrends"),
                    item.get("atualizado", ""),
                    ciclo_id,
                ),
            )
    return ciclo_id


def obter_google_trends_ciclo_atual() -> List[Dict[str, Any]]:
    """Retorna os itens do último ciclo Google Trends."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT ciclo_id FROM google_trends_cache ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if not row:
            return []

        cursor = conn.execute(
            """SELECT termo, interesse, variacao, categoria, trafego, fonte, origem_coleta, atualizado
               FROM google_trends_cache WHERE ciclo_id = ?""",
            (row["ciclo_id"],),
        )
        return [dict(r) for r in cursor.fetchall()]


# ============================================================
# HISTÓRICO DE TENDÊNCIAS
# ============================================================
def registrar_historico_tendencias(top10: List[Dict], origem: str = "sistema") -> Dict[str, Any]:
    """Registra um snapshot do Top 10 no banco."""
    ciclo_id = f"hist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    dados_json = json.dumps(top10, ensure_ascii=False)
    with _get_connection() as conn:
        conn.execute(
            """INSERT INTO historico_tendencias (ciclo_id, timestamp, origem, dados_json, total_produtos)
               VALUES (?, ?, ?, ?, ?)""",
            (ciclo_id, datetime.now().isoformat(), origem, dados_json, len(top10)),
        )
    return {
        "registrado": True,
        "ciclo_id": ciclo_id,
        "motivo": origem,
    }


def obter_historico_tendencias(limite: int = 30) -> List[Dict[str, Any]]:
    """Retorna o histórico de tendências mais recentes."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """SELECT ciclo_id, timestamp, origem, dados_json, total_produtos
               FROM historico_tendencias
               ORDER BY id DESC LIMIT ?""",
            (limite,),
        )
        registros = []
        for row in cursor.fetchall():
            registros.append({
                "ciclo_id": row["ciclo_id"],
                "timestamp": row["timestamp"],
                "origem": row["origem"],
                "dados": json.loads(row["dados_json"]) if row["dados_json"] else [],
                "total_produtos": row["total_produtos"],
                "data_formatada": datetime.fromisoformat(row["timestamp"]).strftime("%d/%m/%Y %H:%M") if row["timestamp"] else "",
            })
        return registros


def limpar_historico_antigos(max_registros: int = 50) -> int:
    """Remove registros de histórico antigos."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id FROM historico_tendencias ORDER BY id DESC LIMIT ?, 999999",
            (max_registros,),
        )
        ids = [row["id"] for row in cursor.fetchall()]
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        conn.execute(f"DELETE FROM historico_tendencias WHERE id IN ({placeholders})", ids)
    return len(ids)


# ============================================================
# PEDREIRA — PEDIDOS
# ============================================================
def criar_pedido_pedreira(produto: str, quantidade: int = 1, solicitante: str = "",
                          empresa: str = "N/A", observacoes: str = "") -> int:
    """Cria um novo pedido na Pedreira. Retorna o ID."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO pedreira_pedidos (produto, quantidade, solicitante, empresa, observacoes, status)
               VALUES (?, ?, ?, ?, ?, 'pendente')""",
            (produto, quantidade, solicitante, empresa, observacoes),
        )
        return cursor.lastrowid


def obter_pedidos_pedreira(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna pedidos, opcionalmente filtrados por status."""
    with _get_connection() as conn:
        if status:
            cursor = conn.execute(
                "SELECT * FROM pedreira_pedidos WHERE status = ? ORDER BY id",
                (status,),
            )
        else:
            cursor = conn.execute("SELECT * FROM pedreira_pedidos ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


def atualizar_status_pedido(pedido_id: int, novo_status: str,
                             atendente: str = "") -> bool:
    """Atualiza o status de um pedido."""
    with _get_connection() as conn:
        conn.execute(
            """UPDATE pedreira_pedidos
               SET status = ?, data_atualizacao = ?, atendente = ?
               WHERE id = ?""",
            (novo_status, datetime.now().isoformat(), atendente, pedido_id),
        )
    return True


def excluir_pedido_pedreira(pedido_id: int) -> bool:
    """Remove um pedido da Pedreira."""
    with _get_connection() as conn:
        conn.execute("DELETE FROM pedreira_pedidos WHERE id = ?", (pedido_id,))
    return True


# ============================================================
# LOGS DE BUSCAS
# ============================================================
def registrar_log_busca(nivel: str = "info", termo: str = "", sucesso: bool = True,
                        quantidade: int = 0, tempo_execucao: float = 0.0,
                        detalhes: str = "", erro: str = "") -> int:
    """Registra um log de busca no banco."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO buscas_logs (timestamp, nivel, termo, sucesso, quantidade,
               tempo_execucao, detalhes, erro)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(), nivel, termo,
                1 if sucesso else 0, quantidade, tempo_execucao,
                detalhes, erro,
            ),
        )
        return cursor.lastrowid


def obter_logs_busca(limite: int = 50) -> List[Dict[str, Any]]:
    """Retorna os logs de busca mais recentes."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM buscas_logs ORDER BY id DESC LIMIT ?", (limite,)
        )
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "timestamp": row["timestamp"],
                "data_formatada": datetime.fromisoformat(row["timestamp"]).strftime("%d/%m/%Y %H:%M:%S") if row["timestamp"] else "",
                "nivel": row["nivel"],
                "termo": row["termo"],
                "sucesso": bool(row["sucesso"]),
                "quantidade": row["quantidade"],
                "tempo_execucao": row["tempo_execucao"],
                "detalhes": row["detalhes"],
                "erro": row["erro"],
            })
        return logs


# ============================================================
# HISTÓRICO DE ATUALIZAÇÃO AUTOMÁTICA
# ============================================================
def registrar_execucao_auto(tipo: str = "automatica", sucesso: bool = True,
                             detalhes: Optional[Dict] = None,
                             tempo: float = 0.0) -> int:
    """Registra uma execução de atualização automática."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO auto_update_historico (timestamp, data_formatada, tipo, sucesso, tempo_segundos, detalhes_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(),
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                tipo,
                1 if sucesso else 0,
                tempo,
                json.dumps(detalhes, ensure_ascii=False) if detalhes else "{}",
            ),
        )
        return cursor.lastrowid


def obter_historico_auto(limite: int = 50) -> List[Dict[str, Any]]:
    """Retorna o histórico de atualizações automáticas."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM auto_update_historico ORDER BY id DESC LIMIT ?", (limite,)
        )
        registros = []
        for row in cursor.fetchall():
            registros.append({
                "timestamp": row["timestamp"],
                "data_formatada": row["data_formatada"],
                "tipo": row["tipo"],
                "sucesso": bool(row["sucesso"]),
                "tempo_segundos": row["tempo_segundos"],
                "detalhes": json.loads(row["detalhes_json"]) if row["detalhes_json"] else {},
            })
        return registros


# ============================================================
# CACHE AGREGADO DE PRODUTOS (compatibilidade com produtos_cache_v48.json)
# ============================================================
def salvar_cache_produtos_agregado(produtos: Dict[str, Any]) -> bool:
    """Salva o cache agregado de produtos (para admin/tools)."""
    with _get_connection() as conn:
        agora = datetime.now().isoformat()
        for nome, dados in produtos.items():
            conn.execute(
                """INSERT INTO produtos_cache (produto_nome, dados_json, fonte, atualizado, atualizado_em)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(produto_nome) DO UPDATE SET
                     dados_json = excluded.dados_json,
                     fonte = excluded.fonte,
                     atualizado = excluded.atualizado,
                     atualizado_em = excluded.atualizado_em""",
                (
                    nome,
                    json.dumps(dados, ensure_ascii=False),
                    dados.get("fonte", ""),
                    dados.get("atualizado", ""),
                    agora,
                ),
            )
    return True


def obter_cache_produtos_agregado() -> Dict[str, Any]:
    """Retorna o cache agregado no formato compatível com produtos_cache_v48.json."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT produto_nome, dados_json, fonte, atualizado FROM produtos_cache ORDER BY atualizado_em DESC"
        )
        produtos = {}
        for row in cursor.fetchall():
            try:
                produtos[row["produto_nome"]] = json.loads(row["dados_json"])
            except json.JSONDecodeError:
                pass
        data_cache = datetime.now().date().isoformat()
        return {
            "data": data_cache,
            "produtos": produtos,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================
# STATUS GERAL DO BANCO
# ============================================================
def obter_status_banco() -> Dict[str, Any]:
    """Retorna um resumo do estado do banco de dados."""
    status = {
        "db_path": DB_PATH,
        "db_existe": os.path.exists(DB_PATH),
        "db_size_kb": round(os.path.getsize(DB_PATH) / 1024, 1) if os.path.exists(DB_PATH) else 0,
        "versao_schema": DB_VERSION,
    }

    try:
        with _get_connection() as conn:
            for tabela in ["ml_ciclos", "amazon_ciclos", "shopee_cache",
                           "google_trends_cache", "historico_tendencias",
                           "pedreira_pedidos", "buscas_logs", "auto_update_historico"]:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM {tabela}")
                    status[f"{tabela}_count"] = cursor.fetchone()["cnt"]
                except Exception:
                    status[f"{tabela}_count"] = 0
    except Exception as e:
        status["erro"] = str(e)

    return status


# ============================================================
# MIGRAÇÃO DE JSON PARA SQLITE (one-shot)
# ============================================================
def migrar_jsons_para_db() -> bool:
    """
    Importa os dados dos JSONs existentes para o SQLite.
    Executado automaticamente no primeiro acesso ao banco.
    """
    migrado = False

    # 1. ML Cache
    ml_path = os.path.join(DIRETORIO_RAIZ, "ml_trends_cache.json")
    if os.path.exists(ml_path):
        try:
            with open(ml_path, "r", encoding="utf-8") as f:
                ml_data = json.load(f)
            if ml_data.get("produtos"):
                ciclo_id = salvar_ml_ciclo(ml_data["produtos"])
                logger.info(f"ML migrado: {len(ml_data['produtos'])} termos (ciclo: {ciclo_id})")
                migrado = True
        except Exception as e:
            logger.warning(f"Falha ao migrar ML: {e}")

    # 2. Amazon Cache
    amz_path = os.path.join(DIRETORIO_RAIZ, "amazon_trends.json")
    if os.path.exists(amz_path):
        try:
            with open(amz_path, "r", encoding="utf-8") as f:
                amz_data = json.load(f)
            if amz_data.get("produtos"):
                ciclo_id = salvar_amazon_ciclo(amz_data["produtos"])
                logger.info(f"Amazon migrado: {len(amz_data['produtos'])} produtos (ciclo: {ciclo_id})")
                migrado = True
        except Exception as e:
            logger.warning(f"Falha ao migrar Amazon: {e}")

    # 3. Shopee Live Cache
    sp_path = os.path.join(DIRETORIO_RAIZ, "shopee_live_cache.json")
    if os.path.exists(sp_path):
        try:
            with open(sp_path, "r", encoding="utf-8") as f:
                sp_data = json.load(f)
            itens = sp_data.get("dados", [])
            if itens:
                ciclo_id = salvar_shopee_ciclo(itens)
                logger.info(f"Shopee migrado: {len(itens)} itens (ciclo: {ciclo_id})")
                migrado = True
        except Exception as e:
            logger.warning(f"Falha ao migrar Shopee: {e}")

    # 4. Google Trends Cache
    gt_path = os.path.join(DIRETORIO_RAIZ, "google_trends_cache.json")
    if os.path.exists(gt_path):
        try:
            with open(gt_path, "r", encoding="utf-8") as f:
                gt_data = json.load(f)
            itens = gt_data.get("dados", [])
            if itens:
                ciclo_id = salvar_google_trends_ciclo(itens)
                logger.info(f"Google migrado: {len(itens)} itens (ciclo: {ciclo_id})")
                migrado = True
        except Exception as e:
            logger.warning(f"Falha ao migrar Google: {e}")

    # 5. Produtos Cache (se existir)
    cache_path = os.path.join(DIRETORIO_RAIZ, "produtos_cache_v48.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            produtos = cache_data.get("produtos", {})
            if produtos:
                salvar_cache_produtos_agregado(produtos)
                logger.info(f"Cache agregado migrado: {len(produtos)} produtos")
                migrado = True
        except Exception as e:
            logger.warning(f"Falha ao migrar cache agregado: {e}")

    return migrado


# ============================================================
# UTILIDADES
# ============================================================
def resetar_tudo() -> bool:
    """REMOVE TODOS OS DADOS DO BANCO. Uso apenas em testes."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    return inicializar_db()
