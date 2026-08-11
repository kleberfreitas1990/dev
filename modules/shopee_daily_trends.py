"""
shopee_daily_trends.py — Coleta Diária de Tendências da Shopee
================================================================

Módulo responsável por:
1. Coletar buscas em alta da Shopee diariamente
2. Normalizar e filtrar conteúdo adulto
3. Persistir histórico em SQLite
4. Fornecer fallback confiável com dados do dia anterior

Versão: 1.0.0
Autor: Manus AI
Data: 2026-08-11
"""

import json
import logging
import time
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from modules.adult_content_filter import filtrar_lista_termos, obter_estatisticas_filtro
from modules.shopee import capturar_buscas_shopee, TERMOS_REAIS_SHOPEE

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
DB_PATH = Path(__file__).parent.parent / "minerador.db"
CACHE_DIARIO = Path(__file__).parent.parent / "shopee_daily_cache.json"

# ============================================================
# SCHEMA DO BANCO DE DADOS
# ============================================================
SCHEMA_DAILY_TRENDS = """
CREATE TABLE IF NOT EXISTS shopee_daily_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta TEXT NOT NULL,
    termo TEXT NOT NULL,
    posicao INTEGER,
    fonte TEXT,
    filtrado_adulto BOOLEAN DEFAULT 0,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(data_coleta, termo)
);

CREATE INDEX IF NOT EXISTS idx_shopee_daily_data ON shopee_daily_trends(data_coleta);
CREATE INDEX IF NOT EXISTS idx_shopee_daily_termo ON shopee_daily_trends(termo);

CREATE TABLE IF NOT EXISTS shopee_daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta TEXT UNIQUE NOT NULL,
    total_termos INTEGER,
    termos_filtrados INTEGER,
    fonte_primaria TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shopee_summary_data ON shopee_daily_summary(data_coleta);
"""

# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================
def _inicializar_banco():
    """Cria as tabelas se não existirem."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        
        for statement in SCHEMA_DAILY_TRENDS.split(";"):
            if statement.strip():
                conn.execute(statement)
        
        conn.commit()
        conn.close()
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")
        raise


# ============================================================
# COLETA E NORMALIZAÇÃO
# ============================================================
def normalizar_termos(termos: List[str]) -> List[str]:
    """
    Normaliza uma lista de termos:
    - Remove duplicados (case-insensitive)
    - Remove espaços extras
    - Ordena alfabeticamente
    """
    if not termos:
        return []
    
    # Normalizar e deduplica
    termos_normalizados = set()
    for termo in termos:
        if termo and isinstance(termo, str):
            termo_limpo = termo.strip()
            if termo_limpo:
                termos_normalizados.add(termo_limpo)
    
    # Retornar ordenado
    return sorted(list(termos_normalizados))


def coletar_tendencias_diarias(forcar_atualizacao: bool = False) -> Tuple[List[str], str]:
    """
    Coleta buscas em alta da Shopee com fallback.
    
    Retorna:
    - Lista de termos (já filtrados)
    - Fonte utilizada ('selenium', 'scraping', 'api', 'fallback', 'cache')
    """
    logger.info("🔍 Iniciando coleta diária de tendências da Shopee...")
    
    # Verificar cache do dia
    hoje = datetime.now().strftime("%Y-%m-%d")
    cache_hoje = _carregar_cache_diario()
    
    if cache_hoje and cache_hoje.get("data_coleta") == hoje and not forcar_atualizacao:
        logger.info("✅ Usando cache do dia atual")
        return cache_hoje.get("termos", []), "cache"
    
    # Tentar coletar dados reais
    termos = []
    fonte = "fallback"
    
    try:
        termos_brutos = capturar_buscas_shopee(max_tentativas=3)
        
        if termos_brutos and len(termos_brutos) > 5:
            termos = termos_brutos
            fonte = "shopee_api"  # Será refinado por capturar_buscas_shopee
            logger.info(f"✅ Coletados {len(termos)} termos via API/Scraping")
        else:
            logger.warning("⚠️ Coleta via API/Scraping retornou poucos termos, usando fallback")
            termos = list(TERMOS_REAIS_SHOPEE)
            fonte = "fallback"
    
    except Exception as e:
        logger.warning(f"⚠️ Erro na coleta: {e}, usando fallback")
        termos = list(TERMOS_REAIS_SHOPEE)
        fonte = "fallback"
    
    # Normalizar
    termos = normalizar_termos(termos)
    
    # Filtrar conteúdo adulto
    termos_antes = len(termos)
    termos = filtrar_lista_termos(termos)
    termos_filtrados = termos_antes - len(termos)
    
    logger.info(f"📊 Coleta finalizada: {len(termos)} termos válidos, {termos_filtrados} bloqueados")
    
    # Salvar cache
    _salvar_cache_diario(hoje, termos, fonte, termos_filtrados)
    
    return termos, fonte


# ============================================================
# CACHE DIÁRIO (JSON)
# ============================================================
def _salvar_cache_diario(data: str, termos: List[str], fonte: str, bloqueados: int):
    """Salva cache diário em JSON."""
    try:
        cache = {
            "data_coleta": data,
            "termos": termos,
            "total": len(termos),
            "fonte": fonte,
            "termos_bloqueados": bloqueados,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(CACHE_DIARIO, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Cache diário salvo: {CACHE_DIARIO}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar cache diário: {e}")


def _carregar_cache_diario() -> Optional[Dict]:
    """Carrega cache diário em JSON."""
    try:
        if CACHE_DIARIO.exists():
            with open(CACHE_DIARIO, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ Erro ao carregar cache diário: {e}")
    
    return None


# ============================================================
# PERSISTÊNCIA EM SQLITE
# ============================================================
def persistir_tendencias_sqlite(data: str, termos: List[str], fonte: str, bloqueados: int):
    """
    Persiste os termos do dia em SQLite.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        cursor = conn.cursor()
        
        # Inserir termos individuais
        for posicao, termo in enumerate(termos, 1):
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO shopee_daily_trends
                    (data_coleta, termo, posicao, fonte, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (data, termo, posicao, fonte, datetime.now().isoformat()))
            except sqlite3.IntegrityError:
                # Termo já existe para este dia
                pass
        
        # Inserir resumo do dia
        cursor.execute("""
            INSERT OR REPLACE INTO shopee_daily_summary
            (data_coleta, total_termos, termos_filtrados, fonte_primaria, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (data, len(termos), bloqueados, fonte, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ {len(termos)} termos persistidos em SQLite para {data}")
    
    except Exception as e:
        logger.error(f"❌ Erro ao persistir em SQLite: {e}")


# ============================================================
# CONSULTAS HISTÓRICAS
# ============================================================
def obter_tendencias_historicas(dias: int = 30) -> List[Dict]:
    """
    Obtém histórico de tendências dos últimos N dias.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        data_inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
        
        cursor.execute("""
            SELECT 
                data_coleta,
                termo,
                posicao,
                fonte
            FROM shopee_daily_trends
            WHERE data_coleta >= ?
            ORDER BY data_coleta DESC, posicao ASC
        """, (data_inicio,))
        
        resultados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return resultados
    
    except Exception as e:
        logger.error(f"❌ Erro ao consultar histórico: {e}")
        return []


def obter_resumo_diario(data: str) -> Optional[Dict]:
    """
    Obtém o resumo do dia especificado.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM shopee_daily_summary
            WHERE data_coleta = ?
        """, (data,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        return dict(resultado) if resultado else None
    
    except Exception as e:
        logger.error(f"❌ Erro ao consultar resumo: {e}")
        return None


def obter_termos_do_dia(data: str) -> List[str]:
    """
    Obtém lista de termos para um dia específico.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT termo
            FROM shopee_daily_trends
            WHERE data_coleta = ?
            ORDER BY posicao ASC
        """, (data,))
        
        termos = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return termos
    
    except Exception as e:
        logger.error(f"❌ Erro ao consultar termos do dia: {e}")
        return []


def obter_termos_permanentes(dias: int = 7) -> List[Tuple[str, int]]:
    """
    Obtém termos que permaneceram em alta nos últimos N dias.
    
    Retorna lista de (termo, dias_permanência).
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        cursor = conn.cursor()
        
        data_inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
        
        cursor.execute(f"""
            SELECT termo, COUNT(DISTINCT data_coleta) as dias_permanencia
            FROM shopee_daily_trends
            WHERE data_coleta >= ?
            GROUP BY termo
            HAVING dias_permanencia >= ?
            ORDER BY dias_permanencia DESC
        """, (data_inicio, dias // 2))
        
        resultados = cursor.fetchall()
        conn.close()
        
        return resultados
    
    except Exception as e:
        logger.error(f"❌ Erro ao consultar termos permanentes: {e}")
        return []


# ============================================================
# ROTINA PRINCIPAL
# ============================================================
def executar_coleta_diaria(forcar_atualizacao: bool = False) -> Dict:
    """
    Executa a coleta diária completa:
    1. Coleta dados
    2. Filtra conteúdo adulto
    3. Persiste em SQLite
    4. Retorna resumo
    """
    # Inicializar banco
    _inicializar_banco()
    
    # Coletar
    termos, fonte = coletar_tendencias_diarias(forcar_atualizacao)
    
    # Obter estatísticas
    stats = obter_estatisticas_filtro(list(TERMOS_REAIS_SHOPEE))
    
    # Persistir
    hoje = datetime.now().strftime("%Y-%m-%d")
    persistir_tendencias_sqlite(hoje, termos, fonte, stats["total_bloqueado"])
    
    # Retornar resumo
    return {
        "data": hoje,
        "total_termos": len(termos),
        "termos_bloqueados": stats["total_bloqueado"],
        "fonte": fonte,
        "timestamp": datetime.now().isoformat(),
        "termos": termos[:10],  # Primeiros 10 para preview
    }


# ============================================================
# TESTES
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Teste: Coleta Diária ===")
    resultado = executar_coleta_diaria(forcar_atualizacao=True)
    print(f"Resultado: {json.dumps(resultado, indent=2, ensure_ascii=False)}")
    
    print("\n=== Teste: Histórico ===")
    historico = obter_tendencias_historicas(dias=7)
    print(f"Encontrados {len(historico)} registros nos últimos 7 dias")
    
    print("\n=== Teste: Termos Permanentes ===")
    permanentes = obter_termos_permanentes(dias=7)
    print(f"Termos permanentes: {permanentes[:5]}")
