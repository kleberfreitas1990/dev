"""
Módulo de Automação e Atualização Automática
Gerencia rotinas de atualização de dados em background
"""

import streamlit as st
import time
import logging
from datetime import datetime, timedelta
from modules.produtos_dinamicos import obter_produtos_dinamicos
from modules.logger import registrar_busca

logger = logging.getLogger(__name__)

def executar_atualizacao_automatica():
    """
    Executa a atualização automática de dados se necessário.
    Renova as fontes da grelha quando a última execução ocorreu há mais de 2 horas.
    """
    # Inicializa estado se não existir
    if "ultima_atualizacao_auto" not in st.session_state:
        st.session_state.ultima_atualizacao_auto = None

    agora = datetime.now()
    
    # Define intervalo de atualização (2 horas)
    INTERVALO_HORAS = 2
    
    precisa_atualizar = False
    
    if st.session_state.ultima_atualizacao_auto is None:
        precisa_atualizar = True
    else:
        diff = agora - st.session_state.ultima_atualizacao_auto
        if diff.total_seconds() > (INTERVALO_HORAS * 3600):
            precisa_atualizar = True

    if precisa_atualizar:
        logger.info("🤖 Iniciando atualização automática de dados...")
        try:
            # Notifica o usuário discretamente se estiver na interface
            # No Streamlit, isso só aparece se o script estiver rodando
            
            inicio = time.time()
            # Renova as fontes e consolida os produtos exibidos pela grelha.
            produtos = obter_produtos_dinamicos(forcar_atualizacao=True)

            st.session_state.ultima_atualizacao_auto = agora
            # A segunda rotina do app usa esta chave; sincronizá-la evita uma
            # chamada duplicada às mesmas fontes durante o mesmo rerun.
            st.session_state["ultima_atualizacao_google_shopee"] = agora
            st.session_state["ultimo_resultado_auto"] = {
                "produtos": {"total": len(produtos)},
                "tempo_total": round(time.time() - inicio, 2),
            }
            
            registrar_busca(
                nivel="sistema",
                termo="automacao_diaria",
                sucesso=True,
                quantidade=len(produtos),
                detalhes=f"Atualização automática concluída com sucesso",
                tempo_execucao=time.time() - inicio
            )
            logger.info(f"✅ Atualização automática concluída: {len(produtos)} produtos.")
            return True
        except Exception as e:
            logger.error(f"❌ Erro na atualização automática: {e}")
            registrar_busca(
                nivel="sistema",
                termo="automacao_diaria",
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
