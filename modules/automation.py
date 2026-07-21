"""
Módulo de Automação e Atualização Automática
Gerencia rotinas de atualização de dados em background

Atualizado: Intervalo corrigido de 2h para 12h.
Verifica expiração real dos caches em disco (não apenas session_state).
"""

import streamlit as st
import time
import logging
from datetime import datetime, timedelta
from modules.produtos_dinamicos import obter_produtos_dinamicos
from modules.logger import registrar_busca

logger = logging.getLogger(__name__)


def _caches_estao_expirados() -> bool:
    """
    Verifica se os caches em disco de ML e Amazon estão expirados.
    Retorna True se QUALQUER um estiver expirado ou ausente.
    """
    try:
        from modules.mercadolivre_scraper import _cache_valido
        if not _cache_valido():
            logger.info("Cache do Mercado Livre expirado ou ausente — atualização necessária")
            return True
    except Exception as e:
        logger.warning(f"Falha ao verificar cache do ML: {e}")
        return True  # Se falhar a verificação, assume que precisa atualizar

    try:
        from modules.amazon_scraper import _carregar_cache_amazon, _cache_recente
        cache_amazon = _carregar_cache_amazon()
        if not _cache_recente(cache_amazon):
            logger.info("Cache da Amazon expirado ou ausente — atualização necessária")
            return True
    except Exception as e:
        logger.warning(f"Falha ao verificar cache da Amazon: {e}")
        return True

    return False


def executar_atualizacao_automatica():
    """
    Executa a atualização automática de dados se necessário.
    Renova as fontes da grade quando:
    1. Nunca foi executada nesta sessão, OU
    2. Já se passaram mais de 12 horas desde a última execução, OU
    3. Os caches em disco de ML ou Amazon estão expirados.
    """
    # Inicializa estado se não existir
    if "ultima_atualizacao_auto" not in st.session_state:
        st.session_state.ultima_atualizacao_auto = None

    agora = datetime.now()

    # Define intervalo de atualização (12 horas — sincronizado com a expectativa do sistema)
    INTERVALO_HORAS = 12

    precisa_atualizar = False

    # Se nunca atualizou nesta sessão, SEMPRE atualiza na primeira carga
    if st.session_state.ultima_atualizacao_auto is None:
        precisa_atualizar = True
    else:
        diff = agora - st.session_state.ultima_atualizacao_auto
        if diff.total_seconds() > (INTERVALO_HORAS * 3600):
            precisa_atualizar = True

    # IMPORTANTE: Mesmo que o session_state diga "recente", verificar se os caches
    # dos arquivos JSON estão expirados. Isso garante atualização quando o app
    # é re-deployado ou hibernado no Streamlit Cloud.
    if not precisa_atualizar:
        precisa_atualizar = _caches_estao_expirados()

    if precisa_atualizar:
        logger.info("🤖 Iniciando atualização automática de dados...")
        try:
            inicio = time.time()
            # Renova as fontes e consolida os produtos exibidos pela grade.
            produtos = obter_produtos_dinamicos(forcar_atualizacao=True)

            st.session_state.ultima_atualizacao_auto = agora
            # A segunda rotina do app usa esta chave; sincronizá-la evita uma
            # chamada duplicada às mesmas fontes durante o mesmo rerun.
            st.session_state["ultima_atualizacao_google_shopee"] = agora
            st.session_state["ultimo_resultado_auto"] = {
                "produtos": {"total": len(produtos)},
                "google_trends": {"total": st.session_state.get("ultimo_resultado_auto", {}).get("google_trends", {}).get("total", 0)},
                "shopee": {"total": st.session_state.get("ultimo_resultado_auto", {}).get("shopee", {}).get("total", 0)},
                "mercadolivre": st.session_state.get("ultimo_resultado_auto", {}).get("mercadolivre", 0),
                "amazon": st.session_state.get("ultimo_resultado_auto", {}).get("amazon", 0),
                "tempo_total": round(time.time() - inicio, 2),
            }

            registrar_busca(
                nivel="sistema",
                termo="automacao_12h",
                sucesso=True,
                quantidade=len(produtos),
                detalhes=f"Atualização automática concluída (intervalo: {INTERVALO_HORAS}h)",
                tempo_execucao=time.time() - inicio
            )
            logger.info(f"✅ Atualização automática concluída: {len(produtos)} produtos em {round(time.time()-inicio, 2)}s")
            return True
        except Exception as e:
            logger.error(f"❌ Erro na atualização automática: {e}")
            registrar_busca(
                nivel="sistema",
                termo="automacao_12h",
                sucesso=False,
                erro=str(e),
                detalhes="Falha na rotina automática"
            )
            return False
    return False


def render_status_automacao():
    """
    Exibe o status da automação no dashboard (opcional)
    """
    if "ultima_atualizacao_auto" in st.session_state and st.session_state.ultima_atualizacao_auto:
        data_formatada = st.session_state.ultima_atualizacao_auto.strftime("%H:%M:%S")
        st.caption(f"🤖 Última atualização automática: {data_formatada}")
    else:
        st.caption("🤖 Automação ativa (aguardando ciclo)")
