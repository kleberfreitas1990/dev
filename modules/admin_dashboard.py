"""
Painel Administrativo - Resumo das Buscas
Mostra se cada nível rodou ou deu erro
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

from modules.logger import carregar_logs, obter_estatisticas_logs, limpar_logs
from modules.shopee import obter_stats_cache_shopee
from modules.serper import obter_stats_cache_serper, obter_stats_serper
from modules.produtos_dinamicos import carregar_cache_produtos


def verificar_status_buscas() -> Dict:
    """
    Verifica o status de cada nível de busca
    Retorna um dicionário com o status de cada um
    """
    
    status = {
        "raspagem": {"status": "⏳", "mensagem": "Aguardando", "ultima": "Nunca", "total": 0},
        "api": {"status": "⏳", "mensagem": "Aguardando", "ultima": "Nunca", "total": 0},
        "cache": {"status": "⏳", "mensagem": "Aguardando", "ultima": "Nunca", "total": 0},
        "produtos": {"status": "⏳", "mensagem": "Aguardando", "ultima": "Nunca", "total": 0}
    }
    
    # ============================================================
    # 1. VERIFICA RASPAGEM (Shopee)
    # ============================================================
    try:
        stats_shopee = obter_stats_cache_shopee()
        if stats_shopee.get("existe"):
            total = stats_shopee.get("total_termos", 0)
            data = stats_shopee.get("data", "Nunca")
            
            hoje = datetime.now().date().isoformat()
            is_hoje = data == hoje
            
            if total > 0 and is_hoje:
                status["raspagem"] = {
                    "status": "✅",
                    "mensagem": f"{total} termos encontrados",
                    "ultima": data,
                    "total": total
                }
            elif total > 0:
                status["raspagem"] = {
                    "status": "🟡",
                    "mensagem": f"{total} termos (cache antigo)",
                    "ultima": data,
                    "total": total
                }
            else:
                status["raspagem"] = {
                    "status": "❌",
                    "mensagem": "Nenhum termo encontrado",
                    "ultima": data,
                    "total": 0
                }
        else:
            status["raspagem"] = {
                "status": "❌",
                "mensagem": "Cache não encontrado",
                "ultima": "Nunca",
                "total": 0
            }
    except Exception as e:
        status["raspagem"] = {
            "status": "❌",
            "mensagem": f"Erro: {str(e)[:30]}",
            "ultima": "Erro",
            "total": 0
        }
    
    # ============================================================
    # 2. VERIFICA API (Serper)
    # ============================================================
    try:
        stats_serper = obter_stats_cache_serper()
        if stats_serper.get("existe"):
            total = stats_serper.get("total_produtos", 0)
            
            if total > 0:
                status["api"] = {
                    "status": "✅",
                    "mensagem": f"{total} produtos encontrados",
                    "ultima": "Hoje" if total > 0 else "Nunca",
                    "total": total
                }
            else:
                status["api"] = {
                    "status": "🟡",
                    "mensagem": "Cache vazio",
                    "ultima": "Nunca",
                    "total": 0
                }
        else:
            serper_key = st.secrets.get("SERPER_API_KEY", "")
            if not serper_key:
                status["api"] = {
                    "status": "⚠️",
                    "mensagem": "Chave não configurada",
                    "ultima": "-",
                    "total": 0
                }
            else:
                status["api"] = {
                    "status": "🟡",
                    "mensagem": "Aguardando primeira busca",
                    "ultima": "Nunca",
                    "total": 0
                }
    except Exception as e:
        status["api"] = {
            "status": "❌",
            "mensagem": f"Erro: {str(e)[:30]}",
            "ultima": "Erro",
            "total": 0
        }
    
    # ============================================================
    # 3. VERIFICA CACHE DE PRODUTOS
    # ============================================================
    try:
        cache_produtos = carregar_cache_produtos()
        if cache_produtos:
            total = len(cache_produtos.get("produtos", {}))
            data = cache_produtos.get("data", "Nunca")
            
            if total > 0:
                status["cache"] = {
                    "status": "✅",
                    "mensagem": f"{total} produtos em cache",
                    "ultima": data,
                    "total": total
                }
            else:
                status["cache"] = {
                    "status": "🟡",
                    "mensagem": "Cache vazio",
                    "ultima": data,
                    "total": 0
                }
        else:
            status["cache"] = {
                "status": "🟡",
                "mensagem": "Nenhum cache",
                "ultima": "Nunca",
                "total": 0
            }
    except Exception as e:
        status["cache"] = {
            "status": "❌",
            "mensagem": f"Erro: {str(e)[:30]}",
            "ultima": "Erro",
            "total": 0
        }
    
    # ============================================================
    # 4. VERIFICA PRODUTOS ATIVOS
    # ============================================================
    try:
        from modules.models import gerar_top10_produtos
        produtos = gerar_top10_produtos(forcar_atualizacao=False)
        
        if produtos and len(produtos) > 0:
            status["produtos"] = {
                "status": "✅",
                "mensagem": f"{len(produtos)} produtos ativos",
                "ultima": "Disponível",
                "total": len(produtos)
            }
        else:
            status["produtos"] = {
                "status": "❌",
                "mensagem": "Nenhum produto disponível",
                "ultima": "-",
                "total": 0
            }
    except Exception as e:
        status["produtos"] = {
            "status": "❌",
            "mensagem": f"Erro: {str(e)[:30]}",
            "ultima": "Erro",
            "total": 0
        }
    
    return status


def render_admin_resumo():
    """
    Renderiza o resumo administrativo simples
    """
    
    st.markdown("## 📊 Resumo Administrativo")
    st.caption("Status atual das buscas e sistemas")
    
    status = verificar_status_buscas()
    
    # ============================================================
    # STATUS GERAL - RESUMÃO
    # ============================================================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 📡 Raspagem")
        status_raspagem = status["raspagem"]["status"]
        mensagem = status["raspagem"]["mensagem"]
        
        if status_raspagem == "✅":
            st.success(f"{status_raspagem} {mensagem}")
        elif status_raspagem == "🟡":
            st.warning(f"{status_raspagem} {mensagem}")
        elif status_raspagem == "⚠️":
            st.info(f"{status_raspagem} {mensagem}")
        else:
            st.error(f"{status_raspagem} {mensagem}")
    
    with col2:
        st.markdown("### 🌐 API Serper")
        status_api = status["api"]["status"]
        mensagem = status["api"]["mensagem"]
        
        if status_api == "✅":
            st.success(f"{status_api} {mensagem}")
        elif status_api == "🟡":
            st.warning(f"{status_api} {mensagem}")
        elif status_api == "⚠️":
            st.info(f"{status_api} {mensagem}")
        else:
            st.error(f"{status_api} {mensagem}")
    
    with col3:
        st.markdown("### 💾 Cache")
        status_cache = status["cache"]["status"]
        mensagem = status["cache"]["mensagem"]
        
        if status_cache == "✅":
            st.success(f"{status_cache} {mensagem}")
        elif status_cache == "🟡":
            st.warning(f"{status_cache} {mensagem}")
        else:
            st.error(f"{status_cache} {mensagem}")
    
    with col4:
        st.markdown("### 📦 Produtos")
        status_produtos = status["produtos"]["status"]
        mensagem = status["produtos"]["mensagem"]
        
        if status_produtos == "✅":
            st.success(f"{status_produtos} {mensagem}")
        else:
            st.error(f"{status_produtos} {mensagem}")
    
    st.markdown("---")
    
    # ============================================================
    # DETALHES EM TABELA RESUMIDA
    # ============================================================
    st.markdown("### 📋 Detalhes por Sistema")
    
    dados_resumo = []
    
    for nome, info in status.items():
        nome_exibido = {
            "raspagem": "📡 Raspagem (Shopee)",
            "api": "🌐 API (Serper)",
            "cache": "💾 Cache",
            "produtos": "📦 Produtos Gerados"
        }.get(nome, nome)
        
        dados_resumo.append({
            "Sistema": nome_exibido,
            "Status": info["status"],
            "Mensagem": info["mensagem"],
            "Última Atualização": info["ultima"],
            "Total": info["total"]
        })
    
    df_resumo = pd.DataFrame(dados_resumo)
    
    st.dataframe(
        df_resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sistema": st.column_config.TextColumn("Sistema", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Mensagem": st.column_config.TextColumn("Mensagem", width="medium"),
            "Última Atualização": st.column_config.TextColumn("Última Atualização", width="small"),
            "Total": st.column_config.NumberColumn("Total", width="small"),
        }
    )
    
    st.markdown("---")
    
    # ============================================================
    # STATUS DA API SERPER - LIMITE DIÁRIO
    # ============================================================
    st.markdown("### 📊 Status da API Serper")
    st.caption("Monitoramento do limite diário de requisições")
    
    from modules.serper import obter_stats_serper
    stats_serper = obter_stats_serper()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Limite Diário", stats_serper["limite_diario"])
    with col2:
        st.metric("✅ Usadas Hoje", stats_serper["usadas_hoje"])
    with col3:
        restantes = stats_serper["restantes"]
        if restantes > 5:
            st.metric("🔄 Restantes", restantes, delta="Disponível", delta_color="normal")
        elif restantes > 0:
            st.metric("🔄 Restantes", restantes, delta="Poucas", delta_color="inverse")
        else:
            st.metric("🔄 Restantes", restantes, delta="Esgotado!", delta_color="inverse")
    with col4:
        progresso = stats_serper["usadas_hoje"] / stats_serper["limite_diario"] * 100
        cor = "green" if progresso < 70 else "orange" if progresso < 90 else "red"
        st.markdown(f"""
        <div style="margin-top: 10px;">
            <small>Uso do limite diário</small>
            <div style="background: #e0e0e0; border-radius: 10px; height: 20px; position: relative; overflow: hidden;">
                <div style="background: {cor}; width: {min(progresso, 100)}%; height: 20px; border-radius: 10px; transition: width 0.5s;">
                    <span style="position: absolute; left: 50%; top: 2px; color: {'white' if progresso > 50 else 'black'}; font-weight: bold; font-size: 12px;">{progresso:.0f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if stats_serper["termos_buscados"]:
        with st.expander(f"📋 Termos buscados hoje ({len(stats_serper['termos_buscados'])} termos)"):
            for termo in stats_serper["termos_buscados"]:
                st.caption(f"- {termo}")
    else:
        st.info("📭 Nenhum termo buscado hoje")
    
    st.markdown("---")
    
    # ============================================================
    # ESTATÍSTICAS DE LOGS
    # ============================================================
    st.markdown("### 📈 Estatísticas de Buscas")
    
    stats_logs = obter_estatisticas_logs()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total", stats_logs["total_tentativas"])
    with col2:
        st.metric("✅ Sucessos", stats_logs["sucessos"])
    with col3:
        st.metric("❌ Falhas", stats_logs["falhas"])
    with col4:
        st.metric("📈 Taxa", stats_logs["taxa_sucesso"])
    
    # ============================================================
    # BOTÕES DE AÇÃO (SEM DUPLICAÇÃO)
    # ============================================================
    st.markdown("---")
    st.markdown("### ⚙️ Ações Rápidas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Forçar Atualização", use_container_width=True):
            with st.spinner("⏳ Atualizando dados..."):
                try:
                    from modules.models import gerar_top10_produtos
                    from modules.serper import resetar_contador_serper
                    
                    resetar_contador_serper()
                    produtos = gerar_top10_produtos(forcar_atualizacao=True)
                    
                    st.success(f"✅ Atualização concluída! {len(produtos)} produtos carregados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao atualizar: {str(e)}")
    
    with col2:
        if st.button("🧹 Limpar Cache", use_container_width=True):
            try:
                from modules.produtos_dinamicos import limpar_cache_produtos
                from modules.shopee import limpar_cache_shopee
                from modules.serper import limpar_cache_serper
                
                limpar_cache_produtos()
                limpar_cache_shopee()
                limpar_cache_serper()
                
                st.success("✅ Cache limpo com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao limpar cache: {str(e)}")
    
    with col3:
        if st.button("🔄 Resetar Contador Serper", use_container_width=True):
            try:
                from modules.serper import resetar_contador_serper
                if resetar_contador_serper():
                    st.success("✅ Contador Serper resetado!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao resetar contador")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    with col4:
        if st.button("🧹 Limpar Logs", use_container_width=True):
            try:
                if limpar_logs():
                    st.success("✅ Logs limpos com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao limpar logs")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    st.markdown("---")
    
    st.caption("""
    **Legenda:**
    - ✅ Funcionando corretamente
    - 🟡 Funcionando com ressalvas (cache antigo ou vazio)
    - ⚠️ Configuração pendente
    - ❌ Com falha
    - ⏳ Aguardando
    """)


__all__ = [
    'verificar_status_buscas',
    'render_admin_resumo'
]
