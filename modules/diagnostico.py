"""
Módulo de Diagnóstico - Verifica os 3 níveis de busca
"""
import streamlit as st
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

def diagnosticar_buscas():
    """
    Diagnostica os 3 níveis de busca: Raspagem, API e Selenium
    Retorna o status de cada um
    """
    resultados = {
        "nivel_1_raspagem": {"status": "❌", "mensagem": "Não testado"},
        "nivel_2_api": {"status": "❌", "mensagem": "Não testado"},
        "nivel_3_selenium": {"status": "❌", "mensagem": "Não testado"},
        "cache": {"status": "❌", "mensagem": "Não testado"},
        "serper": {"status": "❌", "mensagem": "Não testado"},
        "automacao": {"status": "❌", "mensagem": "Inativa"},
        "produtos_ativos": 0,
        "ultima_atualizacao": None
    }
    
    # ============================================================
    # NÍVEL 1: RASPAGEM (Shopee)
    # ============================================================
    try:
        from modules.shopee import capturar_buscas_shopee, obter_stats_cache_shopee
        
        # Tenta capturar buscas
        termos = capturar_buscas_shopee(max_tentativas=1)
        if termos and len(termos) > 0:
            resultados["nivel_1_raspagem"] = {
                "status": "✅",
                "mensagem": f"OK - {len(termos)} termos encontrados",
                "detalhes": termos[:5]
            }
        else:
            # Verifica cache
            stats = obter_stats_cache_shopee()
            if stats.get("existe") and stats.get("total_termos", 0) > 0:
                resultados["nivel_1_raspagem"] = {
                    "status": "🟡",
                    "mensagem": f"Cache - {stats.get('total_termos')} termos em cache",
                    "detalhes": f"Data: {stats.get('data')}"
                }
            else:
                resultados["nivel_1_raspagem"] = {
                    "status": "❌",
                    "mensagem": "Falha - Nenhum termo encontrado",
                    "detalhes": "Verificar conexão com Shopee"
                }
    except Exception as e:
        resultados["nivel_1_raspagem"] = {
            "status": "❌",
            "mensagem": f"Erro: {str(e)[:50]}"
        }
    
    # ============================================================
    # NÍVEL 2: API (Serper.dev)
    # ============================================================
    try:
        from modules.serper import buscar_produtos_serper, obter_stats_cache_serper
        
        # Verifica se tem chave ANTES de tentar buscar
        serper_key = st.secrets.get("SERPER_API_KEY", "")
        if not serper_key:
            resultados["nivel_2_api"] = {
                "status": "❌",
                "mensagem": "Chave Serper não configurada",
                "detalhes": "Adicione SERPER_API_KEY nos secrets do Streamlit Cloud"
            }
        else:
            # Tenta buscar um termo de teste
            termo_teste = "smartwatch"
            produtos = buscar_produtos_serper(termo_teste, limite=2, usar_cache=False)
            
            if produtos and len(produtos) > 0:
                resultados["nivel_2_api"] = {
                    "status": "✅",
                    "mensagem": f"OK - {len(produtos)} produtos encontrados",
                    "detalhes": [p.get("nome", "")[:30] for p in produtos[:3]]
                }
            else:
                resultados["nivel_2_api"] = {
                    "status": "❌",
                    "mensagem": "Falha - Nenhum produto encontrado",
                    "detalhes": "Verificar se a API Key é válida ou se o limite foi atingido"
                }
    except Exception as e:
        resultados["nivel_2_api"] = {
            "status": "❌",
            "mensagem": f"Erro: {str(e)[:50]}"
        }
    
    # ============================================================
    # NÍVEL 3: Selenium (Integração Real)
    # ============================================================
    try:
        from modules.selenium_client import verificar_status_selenium
        
        status_selenium = verificar_status_selenium()
        if status_selenium.get("online"):
            resultados["nivel_3_selenium"] = {
                "status": "✅",
                "mensagem": "OK - Servidor Selenium Online",
                "detalhes": f"URL: {status_selenium.get('url')}"
            }
        else:
            erro = status_selenium.get("error", "Servidor Offline")
            resultados["nivel_3_selenium"] = {
                "status": "❌",
                "mensagem": f"Falha - {erro}",
                "detalhes": f"URL: {status_selenium.get('url')}"
            }
    except Exception as e:
        resultados["nivel_3_selenium"] = {
            "status": "❌",
            "mensagem": f"Erro ao conectar: {str(e)[:50]}"
        }
    
    # ============================================================
    # CACHE
    # ============================================================
    try:
        from modules.produtos_dinamicos import carregar_cache_produtos
        
        cache = carregar_cache_produtos()
        if cache:
            data_cache = cache.get("data", "desconhecida")
            total = len(cache.get("produtos", {}))
            resultados["cache"] = {
                "status": "✅" if total > 0 else "🟡",
                "mensagem": f"{total} produtos em cache",
                "detalhes": f"Data: {data_cache}"
            }
            resultados["produtos_ativos"] = total
            resultados["ultima_atualizacao"] = data_cache
        else:
            resultados["cache"] = {
                "status": "🟡",
                "mensagem": "Cache vazio",
                "detalhes": "Será criado na primeira busca"
            }
    except Exception as e:
        resultados["cache"] = {
            "status": "❌",
            "mensagem": f"Erro: {str(e)[:50]}"
        }
    
    # ============================================================
    # AUTOMAÇÃO
    # ============================================================
    if "ultima_atualizacao_auto" in st.session_state:
        resultados["automacao"] = {
            "status": "✅",
            "mensagem": "Ativa",
            "detalhes": f"Última: {st.session_state.ultima_atualizacao_auto.strftime('%H:%M:%S')}"
        }
    else:
        resultados["automacao"] = {
            "status": "🟡",
            "mensagem": "Aguardando ciclo",
            "detalhes": "Será ativada no próximo recarregamento"
        }

    # ============================================================
    # STATUS GERAL
    # ============================================================
    niveis_ok = sum(1 for k in ["nivel_1_raspagem", "nivel_2_api", "nivel_3_selenium"] 
                    if resultados.get(k, {}).get("status") == "✅")
    
    resultados["status_geral"] = {
        "niveis_funcionando": niveis_ok,
        "total_niveis": 3,
        "percentual": f"{int(niveis_ok/3 * 100)}%"
    }
    
    return resultados

def render_painel_diagnostico():
    """
    Renderiza o painel de diagnóstico
    """
    st.markdown("## 🔍 Diagnóstico dos Níveis de Busca")
    st.caption("Verifique se todos os sistemas estão funcionando")
    
    with st.spinner("🔍 Executando diagnóstico..."):
        resultados = diagnosticar_buscas()
    
    # ============================================================
    # STATUS GERAL
    # ============================================================
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📡 Raspagem", resultados["nivel_1_raspagem"]["status"])
    with col2:
        st.metric("🌐 API", resultados["nivel_2_api"]["status"])
    with col3:
        st.metric("🔄 Selenium", resultados["nivel_3_selenium"]["status"])
    with col4:
        st.metric("💾 Cache", resultados["cache"]["status"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🤖 Automação", resultados["automacao"]["status"])
    
    st.markdown("---")
    
    # ============================================================
    # DETALHES DE CADA NÍVEL
    # ============================================================
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("### 📡 Nível 1 - Raspagem (Shopee)")
            status = resultados["nivel_1_raspagem"]
            st.markdown(f"**Status:** {status.get('status')} {status.get('mensagem')}")
            if status.get("detalhes"):
                st.caption(f"📌 {status.get('detalhes')}")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 🌐 Nível 2 - API (Serper.dev)")
            status = resultados["nivel_2_api"]
            st.markdown(f"**Status:** {status.get('status')} {status.get('mensagem')}")
            if status.get("detalhes"):
                st.caption(f"📌 {status.get('detalhes')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("### 🔄 Nível 3 - Selenium (Render)")
            status = resultados["nivel_3_selenium"]
            st.markdown(f"**Status:** {status.get('status')} {status.get('mensagem')}")
            if status.get("detalhes"):
                st.caption(f"📌 {status.get('detalhes')}")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 💾 Cache")
            status = resultados["cache"]
            st.markdown(f"**Status:** {status.get('status')} {status.get('mensagem')}")
            if status.get("detalhes"):
                st.caption(f"📌 {status.get('detalhes')}")
    
    # ============================================================
    # PRODUTOS ATIVOS
    # ============================================================
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📦 Produtos no Cache", resultados.get("produtos_ativos", 0))
    with col2:
        st.metric("🔄 Última Atualização", resultados.get("ultima_atualizacao", "Nunca"))
    
    # ============================================================
    # RECOMENDAÇÕES
    # ============================================================
    st.markdown("---")
    st.markdown("### 💡 Recomendações")
    
    if resultados["nivel_1_raspagem"]["status"] == "❌":
        st.warning("⚠️ **Raspagem com falha:** Verifique a conexão com a Shopee ou se o site mudou a estrutura.")
    elif resultados["nivel_1_raspagem"]["status"] == "🟡":
        st.info("ℹ️ **Raspagem usando cache:** Os dados estão sendo carregados do cache, não da fonte ao vivo.")
    else:
        st.success("✅ **Raspagem funcionando:** Os termos da Shopee estão sendo capturados corretamente.")
    
    if resultados["nivel_2_api"]["status"] == "❌":
        st.warning("⚠️ **API com falha:** Verifique a chave SERPER_API_KEY nos secrets do Streamlit Cloud.")
    else:
        st.success("✅ **API funcionando:** As buscas no Google Shopping estão ativas.")
    
    if resultados["nivel_3_selenium"]["status"] == "❌":
        st.warning("⚠️ **Selenium Offline:** Verifique se o servidor no Render está rodando e se a URL SELENIUM_API_URL está correta nos secrets.")
    elif resultados["nivel_3_selenium"]["status"] == "✅":
        st.success("✅ **Selenium Online:** O servidor de scraping está respondendo corretamente.")
    
    st.caption("🔧 Mantenha seus segredos (Secrets) atualizados no painel do Streamlit Cloud para garantir o funcionamento total.")

__all__ = [
    'diagnosticar_buscas',
    'render_painel_diagnostico'
]
