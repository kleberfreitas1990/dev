"""
Painel Administrativo - Resumo das Buscas
Mostra se cada nível rodou ou deu erro
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

from modules.logger import carregar_logs, obter_estatisticas_logs
from modules.shopee import obter_stats_cache_shopee
from modules.serper import obter_stats_cache_serper
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
            
            # Verifica se o cache é de hoje
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
            # Verifica se a chave está configurada
            import streamlit as st
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
    
    # Busca status
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
    
    # Cria DataFrame resumido
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
    
    # Estiliza o DataFrame
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
    # BOTÃO PARA FORÇAR ATUALIZAÇÃO
    # ============================================================
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Forçar Atualização", use_container_width=True):
            with st.spinner("⏳ Atualizando dados..."):
                try:
                    from modules.models import gerar_top10_produtos
                    gerar_top10_produtos(forcar_atualizacao=True)
                    st.success("✅ Dados atualizados com sucesso!")
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
    
    st.markdown("---")
    
    # ============================================================
    # LEGENDA
    # ============================================================
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
