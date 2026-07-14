"""
Módulo de Atualização Automática - Área de Controle Visual
Gerencia rotinas de atualização de dados do Google Trends e Shopee
com painel de controle, histórico de execuções e agendamento configurável.
"""

import streamlit as st
import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================
# ARQUIVO DE HISTÓRICO DE EXECUÇÕES
# ============================================================
ARQUIVO_HISTORICO_AUTO = "auto_update_historico.json"
INTERVALO_PADRAO_HORAS = 6  # Intervalo padrão de atualização

# ============================================================
# FUNÇÕES DE HISTÓRICO
# ============================================================
def carregar_historico() -> List[Dict]:
    """Carrega o histórico de execuções automáticas"""
    if not os.path.exists(ARQUIVO_HISTORICO_AUTO):
        return []
    try:
        with open(ARQUIVO_HISTORICO_AUTO, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados.get("historico", [])
    except Exception:
        return []

def salvar_historico(historico: List[Dict]) -> bool:
    """Salva o histórico de execuções"""
    try:
        # Mantém apenas os últimos 50 registros
        historico_recente = historico[-50:]
        with open(ARQUIVO_HISTORICO_AUTO, "w", encoding="utf-8") as f:
            json.dump({"historico": historico_recente}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar histórico: {e}")
        return False

def registrar_execucao(tipo: str, sucesso: bool, detalhes: Dict = None, tempo: float = 0.0):
    """Registra uma execução no histórico"""
    historico = carregar_historico()
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "data_formatada": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": tipo,
        "sucesso": sucesso,
        "tempo_segundos": round(tempo, 2),
        "detalhes": detalhes or {},
    }
    historico.append(entrada)
    salvar_historico(historico)

# ============================================================
# LÓGICA DE ATUALIZAÇÃO AUTOMÁTICA
# ============================================================
def verificar_necessidade_atualizacao(intervalo_horas: int = INTERVALO_PADRAO_HORAS) -> bool:
    """
    Verifica se é necessário executar uma atualização automática.
    Usa session_state para controle entre reruns do Streamlit.
    """
    chave = "ultima_atualizacao_google_shopee"

    if chave not in st.session_state:
        st.session_state[chave] = None

    if st.session_state[chave] is None:
        return True

    diff = datetime.now() - st.session_state[chave]
    return diff.total_seconds() > (intervalo_horas * 3600)

def executar_atualizacao_google_shopee(forcar: bool = False, intervalo_horas: int = INTERVALO_PADRAO_HORAS) -> bool:
    """
    Executa a atualização automática de dados do Google Trends e Shopee.
    Retorna True se a atualização foi executada, False se não foi necessária.
    """
    if not forcar and not verificar_necessidade_atualizacao(intervalo_horas):
        return False

    logger.info("🤖 Iniciando atualização automática Google Trends + Shopee...")
    inicio = time.time()

    try:
        from modules.google_shopee_trends import forcar_atualizacao_completa
        resultado = forcar_atualizacao_completa()

        st.session_state["ultima_atualizacao_google_shopee"] = datetime.now()
        st.session_state["ultimo_resultado_auto"] = resultado

        registrar_execucao(
            tipo="automatica",
            sucesso=True,
            detalhes=resultado,
            tempo=time.time() - inicio
        )
        logger.info(f"✅ Atualização automática concluída em {round(time.time()-inicio, 2)}s")
        return True

    except Exception as e:
        logger.error(f"❌ Erro na atualização automática: {e}")
        registrar_execucao(
            tipo="automatica",
            sucesso=False,
            detalhes={"erro": str(e)},
            tempo=time.time() - inicio
        )
        return False

# ============================================================
# PAINEL VISUAL DE ATUALIZAÇÃO AUTOMÁTICA
# ============================================================
def render_painel_atualizacao_automatica():
    """
    Renderiza o painel completo de controle da atualização automática.
    Inclui status, histórico, configuração de intervalo e botão de força.
    """
    st.markdown("## 🤖 Central de Atualização Automática")
    st.caption("Controle e monitore as rotinas de atualização de dados do Google Trends e Shopee")

    # ============================================================
    # STATUS GERAL
    # ============================================================
    from modules.google_shopee_trends import obter_status_cache

    status_cache = obter_status_cache()
    ultima_auto = st.session_state.get("ultima_atualizacao_google_shopee")

    col_status1, col_status2, col_status3, col_status4 = st.columns(4)

    with col_status1:
        if ultima_auto:
            diff = datetime.now() - ultima_auto
            minutos = int(diff.total_seconds() / 60)
            if minutos < 60:
                label = f"{minutos}min atrás"
            else:
                label = f"{int(minutos/60)}h atrás"
            st.metric("🕐 Última Atualização", label, delta="Automática")
        else:
            st.metric("🕐 Última Atualização", "Nunca", delta="Aguardando")

    with col_status2:
        google_status = status_cache.get("google_trends", {})
        icone = "✅" if google_status.get("valido") else "⚠️"
        total = google_status.get("total", 0)
        st.metric(f"{icone} Google Trends", f"{total} itens",
                  delta="Cache válido" if google_status.get("valido") else "Cache expirado")

    with col_status3:
        shopee_status = status_cache.get("shopee", {})
        icone = "✅" if shopee_status.get("valido") else "⚠️"
        total = shopee_status.get("total", 0)
        st.metric(f"{icone} Shopee", f"{total} itens",
                  delta="Cache válido" if shopee_status.get("valido") else "Cache expirado")

    with col_status4:
        historico = carregar_historico()
        total_exec = len(historico)
        sucesso_exec = sum(1 for h in historico if h.get("sucesso"))
        taxa = round((sucesso_exec / total_exec * 100), 1) if total_exec > 0 else 0
        st.metric("📊 Taxa de Sucesso", f"{taxa}%", delta=f"{total_exec} execuções")

    st.markdown("---")

    # ============================================================
    # CONFIGURAÇÃO E CONTROLES
    # ============================================================
    col_config, col_acao = st.columns([2, 1])

    with col_config:
        st.markdown("### ⚙️ Configuração do Intervalo")

        intervalo = st.select_slider(
            "Intervalo de atualização automática",
            options=[1, 2, 3, 4, 6, 8, 12, 24],
            value=st.session_state.get("intervalo_auto_horas", INTERVALO_PADRAO_HORAS),
            format_func=lambda x: f"{x}h" if x > 1 else "1h",
            key="slider_intervalo_auto"
        )
        st.session_state["intervalo_auto_horas"] = intervalo

        if ultima_auto:
            proximo = ultima_auto + timedelta(hours=intervalo)
            if proximo > datetime.now():
                diff_prox = proximo - datetime.now()
                mins = int(diff_prox.total_seconds() / 60)
                st.info(f"⏰ Próxima atualização automática em **{mins} minutos** ({proximo.strftime('%H:%M')})")
            else:
                st.warning("⚠️ Atualização pendente — será executada no próximo carregamento da página")
        else:
            st.info("ℹ️ A primeira atualização ocorrerá automaticamente ao carregar a página")

        # Detalhes do cache
        with st.expander("📋 Detalhes do Cache"):
            for fonte, dados in status_cache.items():
                nome_exib = "Google Trends" if fonte == "google_trends" else "Shopee"
                if dados.get("existe"):
                    st.markdown(f"**{nome_exib}**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption(f"Última atualização: {dados.get('data_formatada', 'N/A')}")
                        st.caption(f"Total de itens: {dados.get('total', 0)}")
                    with col_b:
                        st.caption(f"Status: {'✅ Válido' if dados.get('valido') else '⚠️ Expirado'}")
                        st.caption(f"Próximo refresh: {dados.get('proximo_refresh', 'N/A')}")
                else:
                    st.caption(f"**{nome_exib}**: ❌ Cache não encontrado")

    with col_acao:
        st.markdown("### 🚀 Ações Manuais")

        if st.button("🔄 Forçar Atualização Agora", type="primary", use_container_width=True, key="btn_forcar_auto"):
            with st.spinner("🔄 Atualizando dados do Google Trends e Shopee..."):
                executou = executar_atualizacao_google_shopee(forcar=True)
                if executou:
                    st.success("✅ Dados atualizados com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Falha ao atualizar dados.")

        if st.button("🗑️ Limpar Cache", use_container_width=True, key="btn_limpar_cache_auto"):
            from modules.google_shopee_trends import CACHE_GOOGLE_TRENDS, CACHE_SHOPEE_LIVE
            removidos = 0
            for arquivo in [CACHE_GOOGLE_TRENDS, CACHE_SHOPEE_LIVE]:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
                    removidos += 1
            st.session_state["ultima_atualizacao_google_shopee"] = None
            st.success(f"✅ {removidos} arquivo(s) de cache removidos.")
            st.rerun()

        st.markdown("---")
        st.markdown("**📡 Status do Sistema**")

        # Indicador de automação ativa
        auto_ativa = st.session_state.get("ultima_atualizacao_google_shopee") is not None
        if auto_ativa:
            st.success("🟢 Automação Ativa")
        else:
            st.warning("🟡 Aguardando Primeira Execução")

        # Toggle para ativar/desativar
        auto_habilitada = st.toggle(
            "Atualização Automática",
            value=st.session_state.get("auto_update_habilitada", True),
            key="toggle_auto_update"
        )
        st.session_state["auto_update_habilitada"] = auto_habilitada

    st.markdown("---")

    # ============================================================
    # HISTÓRICO DE EXECUÇÕES
    # ============================================================
    st.markdown("### 📋 Histórico de Execuções")

    historico = carregar_historico()

    if not historico:
        st.info("📭 Nenhuma execução registrada ainda. A primeira atualização ocorrerá automaticamente.")
    else:
        # Exibe os últimos 10 registros em ordem decrescente
        historico_recente = list(reversed(historico[-10:]))

        import pandas as pd
        dados_hist = []
        for h in historico_recente:
            detalhes = h.get("detalhes", {})
            google_total = detalhes.get("google_trends", {}).get("total", "-") if isinstance(detalhes.get("google_trends"), dict) else "-"
            shopee_total = detalhes.get("shopee", {}).get("total", "-") if isinstance(detalhes.get("shopee"), dict) else "-"
            erro = detalhes.get("erro", "")

            dados_hist.append({
                "Data/Hora": h.get("data_formatada", "N/A"),
                "Tipo": h.get("tipo", "N/A").capitalize(),
                "Status": "✅ Sucesso" if h.get("sucesso") else "❌ Falha",
                "Google Trends": f"{google_total} itens" if google_total != "-" else "-",
                "Shopee": f"{shopee_total} itens" if shopee_total != "-" else "-",
                "Tempo (s)": h.get("tempo_segundos", 0),
                "Erro": erro[:50] + "..." if len(erro) > 50 else erro,
            })

        df_hist = pd.DataFrame(dados_hist)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

        if st.button("🗑️ Limpar Histórico", key="btn_limpar_historico"):
            salvar_historico([])
            st.success("✅ Histórico limpo.")
            st.rerun()

# ============================================================
# FUNÇÃO DE INTEGRAÇÃO NO APP PRINCIPAL
# ============================================================
def executar_ciclo_automatico():
    """
    Deve ser chamada no início do app principal para executar
    o ciclo automático de atualização se necessário.
    """
    if not st.session_state.get("auto_update_habilitada", True):
        return

    intervalo = st.session_state.get("intervalo_auto_horas", INTERVALO_PADRAO_HORAS)
    executar_atualizacao_google_shopee(forcar=False, intervalo_horas=intervalo)

def render_status_automacao_rodape():
    """
    Exibe o status compacto da automação no rodapé da aplicação.
    Compatível com o render_status_automacao() existente.
    """
    ultima_auto = st.session_state.get("ultima_atualizacao_google_shopee")
    ultima_geral = st.session_state.get("ultima_atualizacao_auto")

    col1, col2, col3 = st.columns(3)

    with col1:
        if ultima_geral:
            st.caption(f"🤖 Produtos: {ultima_geral.strftime('%H:%M:%S')}")
        else:
            st.caption("🤖 Produtos: aguardando ciclo")

    with col2:
        if ultima_auto:
            st.caption(f"📊 Google/Shopee: {ultima_auto.strftime('%H:%M:%S')}")
        else:
            st.caption("📊 Google/Shopee: aguardando ciclo")

    with col3:
        auto_ativa = st.session_state.get("auto_update_habilitada", True)
        st.caption(f"⚙️ Automação: {'🟢 Ativa' if auto_ativa else '🔴 Pausada'}")
