"""
Sistema de Logs e Monitoramento de Buscas
Registra todas as tentativas de busca e seus resultados
"""

import json
import os
import logging
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

# ============================================================
# ARQUIVO DE LOGS
# ============================================================
ARQUIVO_LOGS = "buscas_logs.json"

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================
logger = logging.getLogger(__name__)

# ============================================================
# FUNÇÕES DE LOG
# ============================================================
def registrar_busca(
    nivel: str,
    termo: str,
    sucesso: bool,
    quantidade: int = 0,
    detalhes: str = "",
    tempo_execucao: float = 0,
    erro: str = ""
) -> Dict:
    """
    Registra uma tentativa de busca no arquivo de logs
    """
    
    registro = {
        "timestamp": datetime.now().isoformat(),
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nivel": nivel,
        "termo": termo,
        "sucesso": sucesso,
        "quantidade": quantidade,
        "detalhes": detalhes,
        "tempo_execucao": round(tempo_execucao, 2),
        "erro": erro if erro else None
    }
    
    # Carrega logs existentes
    logs = carregar_logs()
    
    # Adiciona novo registro
    logs.append(registro)
    
    # Mantém apenas os últimos 1000 registros
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    # Salva
    salvar_logs(logs)
    
    return registro

def carregar_logs() -> List[Dict]:
    """Carrega todos os logs do arquivo"""
    if os.path.exists(ARQUIVO_LOGS):
        try:
            with open(ARQUIVO_LOGS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_logs(logs: List[Dict]) -> bool:
    """Salva logs no arquivo"""
    try:
        with open(ARQUIVO_LOGS, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar logs: {e}")
        return False

def limpar_logs() -> bool:
    """Limpa todos os logs"""
    try:
        if os.path.exists(ARQUIVO_LOGS):
            os.remove(ARQUIVO_LOGS)
        return True
    except:
        return False

def obter_estatisticas_logs() -> Dict:
    """
    Retorna estatísticas dos logs
    """
    logs = carregar_logs()
    
    if not logs:
        return {
            "total_tentativas": 0,
            "sucessos": 0,
            "falhas": 0,
            "taxa_sucesso": "0%",
            "por_nivel": {},
            "ultimas_buscas": []
        }
    
    # Estatísticas gerais
    total = len(logs)
    sucessos = sum(1 for l in logs if l.get("sucesso", False))
    falhas = total - sucessos
    taxa_sucesso = f"{(sucessos/total*100):.1f}%" if total > 0 else "0%"
    
    # Por nível
    por_nivel = {}
    niveis = ["raspagem", "api", "selenium", "cache"]
    for nivel in niveis:
        logs_nivel = [l for l in logs if l.get("nivel") == nivel]
        if logs_nivel:
            total_nivel = len(logs_nivel)
            sucesso_nivel = sum(1 for l in logs_nivel if l.get("sucesso", False))
            por_nivel[nivel] = {
                "total": total_nivel,
                "sucessos": sucesso_nivel,
                "falhas": total_nivel - sucesso_nivel,
                "taxa": f"{(sucesso_nivel/total_nivel*100):.1f}%" if total_nivel > 0 else "0%"
            }
    
    # Últimas 10 buscas
    ultimas = []
    for log in logs[-10:]:
        ultimas.append({
            "data": log.get("data", ""),
            "nivel": log.get("nivel", ""),
            "termo": log.get("termo", ""),
            "sucesso": "✅" if log.get("sucesso") else "❌",
            "quantidade": log.get("quantidade", 0)
        })
    
    return {
        "total_tentativas": total,
        "sucessos": sucessos,
        "falhas": falhas,
        "taxa_sucesso": taxa_sucesso,
        "por_nivel": por_nivel,
        "ultimas_buscas": ultimas
    }

def render_painel_logs():
    """
    Renderiza o painel de logs e monitoramento
    """
    st.markdown("## 📊 Monitor de Buscas")
    st.caption("Veja todas as tentativas de busca e seus resultados")
    
    # ============================================================
    # ESTATÍSTICAS RÁPIDAS
    # ============================================================
    stats = obter_estatisticas_logs()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total de Buscas", stats["total_tentativas"])
    with col2:
        st.metric("✅ Sucessos", stats["sucessos"])
    with col3:
        st.metric("❌ Falhas", stats["falhas"])
    with col4:
        st.metric("📈 Taxa de Sucesso", stats["taxa_sucesso"])
    
    st.markdown("---")
    
    # ============================================================
    # ESTATÍSTICAS POR NÍVEL
    # ============================================================
    if stats["por_nivel"]:
        st.markdown("### 📡 Por Nível de Busca")
        
        col1, col2, col3, col4 = st.columns(4)
        niveis_icons = {
            "raspagem": "📡",
            "api": "🌐", 
            "selenium": "🔄",
            "cache": "💾"
        }
        
        nivel_lista = list(stats["por_nivel"].items())
        for i, (nivel, dados) in enumerate(nivel_lista):
            if i < 4:
                with [col1, col2, col3, col4][i]:
                    icon = niveis_icons.get(nivel, "❓")
                    with st.container(border=True):
                        st.markdown(f"**{icon} {nivel.capitalize()}**")
                        st.caption(f"Total: {dados['total']}")
                        st.caption(f"✅ Sucessos: {dados['sucessos']}")
                        st.caption(f"📈 Taxa: {dados['taxa']}")
    
    st.markdown("---")
    
    # ============================================================
    # ÚLTIMAS BUSCAS
    # ============================================================
    st.markdown("### 🔄 Últimas Buscas Realizadas")
    
    if stats["ultimas_buscas"]:
        # Tabela com as últimas buscas
        df_ultimas = pd.DataFrame(stats["ultimas_buscas"][::-1])
        
        # Renomeia colunas
        df_ultimas.columns = ["Data", "Nível", "Termo", "Status", "Resultados"]
        
        # Estiliza
        st.dataframe(
            df_ultimas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Data": st.column_config.TextColumn("Data", width="small"),
                "Nível": st.column_config.TextColumn("Nível", width="small"),
                "Termo": st.column_config.TextColumn("Termo", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Resultados": st.column_config.TextColumn("Resultados", width="small"),
            }
        )
    else:
        st.info("📭 Nenhuma busca realizada ainda.")
    
    st.markdown("---")
    
    # ============================================================
    # LOGS COMPLETOS (EXPANDÍVEL)
    # ============================================================
    with st.expander("📋 Ver Logs Completos"):
        logs = carregar_logs()
        
        if logs:
            # Cria DataFrame com todos os logs
            df_logs = pd.DataFrame(logs)
            
            # Seleciona e renomeia colunas
            colunas = ["data", "nivel", "termo", "sucesso", "quantidade", "tempo_execucao", "erro"]
            df_logs = df_logs[colunas] if all(c in df_logs.columns for c in colunas) else df_logs
            
            # Formata
            df_logs["sucesso"] = df_logs["sucesso"].apply(lambda x: "✅" if x else "❌")
            df_logs["tempo_execucao"] = df_logs["tempo_execucao"].apply(lambda x: f"{x}s" if x else "-")
            
            st.dataframe(
                df_logs,
                use_container_width=True,
                hide_index=True
            )
            
            # Botão para limpar logs
            if st.button("🧹 Limpar Logs", use_container_width=True):
                if limpar_logs():
                    st.success("✅ Logs limpos com sucesso!")
                    st.rerun()
        else:
            st.info("📭 Nenhum log disponível")

__all__ = [
    'registrar_busca',
    'carregar_logs',
    'salvar_logs',
    'limpar_logs',
    'obter_estatisticas_logs',
    'render_painel_logs'
]
