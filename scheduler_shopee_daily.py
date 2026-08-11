#!/usr/bin/env python3
"""
scheduler_shopee_daily.py — Agendador de Coleta Diária da Shopee
==================================================================

Responsável por executar a coleta de tendências da Shopee em horário fixo.

Pode ser integrado com:
1. APScheduler (local)
2. Manus Scheduler (manus-config schedule)
3. Cron (Linux)
4. GitHub Actions (CI/CD)

Versão: 1.0.0
Autor: Manus AI
Data: 2026-08-11
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler_shopee_daily.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================
# IMPORTAÇÕES
# ============================================================
try:
    from modules.shopee_daily_trends import (
        executar_coleta_diaria,
        obter_tendencias_historicas,
        obter_termos_permanentes,
    )
except ImportError as e:
    logger.error(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
LOG_EXECUCOES = Path(__file__).parent / "scheduler_execucoes.json"
INTERVALO_HORAS = 24  # Executar a cada 24 horas


# ============================================================
# FUNÇÕES PRINCIPAIS
# ============================================================
def registrar_execucao(resultado: dict):
    """Registra a execução em arquivo JSON."""
    try:
        execucoes = []
        if LOG_EXECUCOES.exists():
            with open(LOG_EXECUCOES, "r", encoding="utf-8") as f:
                execucoes = json.load(f)
        
        execucoes.append({
            "timestamp": datetime.now().isoformat(),
            **resultado
        })
        
        # Manter apenas os últimos 90 dias
        execucoes = execucoes[-90:]
        
        with open(LOG_EXECUCOES, "w", encoding="utf-8") as f:
            json.dump(execucoes, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Execução registrada em {LOG_EXECUCOES}")
    
    except Exception as e:
        logger.error(f"❌ Erro ao registrar execução: {e}")


def obter_historico_execucoes(dias: int = 30) -> list:
    """Obtém histórico de execuções."""
    try:
        if LOG_EXECUCOES.exists():
            with open(LOG_EXECUCOES, "r", encoding="utf-8") as f:
                execucoes = json.load(f)
            
            # Filtrar por data
            data_limite = (datetime.now() - timedelta(days=dias)).isoformat()
            return [e for e in execucoes if e.get("timestamp", "") >= data_limite]
        
        return []
    
    except Exception as e:
        logger.error(f"❌ Erro ao obter histórico: {e}")
        return []


def executar_coleta():
    """Executa a coleta diária."""
    logger.info("="*60)
    logger.info("INICIANDO COLETA DIÁRIA DE TENDÊNCIAS SHOPEE")
    logger.info("="*60)
    
    try:
        # Executar coleta
        resultado = executar_coleta_diaria(forcar_atualizacao=True)
        
        # Adicionar informações extras
        resultado["status"] = "sucesso"
        resultado["historico_dias"] = len(obter_tendencias_historicas(dias=30))
        resultado["termos_permanentes_7d"] = len(obter_termos_permanentes(dias=7))
        
        # Log do resultado
        logger.info(f"✅ Coleta concluída com sucesso")
        logger.info(f"   Data: {resultado.get('data')}")
        logger.info(f"   Total de termos: {resultado.get('total_termos')}")
        logger.info(f"   Termos bloqueados: {resultado.get('termos_bloqueados')}")
        logger.info(f"   Fonte: {resultado.get('fonte')}")
        logger.info(f"   Histórico: {resultado.get('historico_dias')} dias")
        logger.info(f"   Permanentes (7d): {resultado.get('termos_permanentes_7d')}")
        
        # Registrar
        registrar_execucao(resultado)
        
        return resultado
    
    except Exception as e:
        logger.error(f"❌ Erro durante coleta: {e}", exc_info=True)
        
        resultado = {
            "status": "erro",
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        registrar_execucao(resultado)
        
        return resultado


# ============================================================
# AGENDADOR COM APSCHEDULER
# ============================================================
def iniciar_agendador_apscheduler(hora: str = "08:00"):
    """
    Inicia o agendador com APScheduler.
    
    Exemplo de uso:
        python scheduler_shopee_daily.py --scheduler apscheduler --hora 08:00
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error("❌ APScheduler não está instalado. Instale com: pip install apscheduler")
        return False
    
    try:
        # Parsear hora (HH:MM)
        hora_parts = hora.split(":")
        if len(hora_parts) != 2:
            logger.error(f"❌ Formato de hora inválido: {hora}. Use HH:MM")
            return False
        
        hora_int = int(hora_parts[0])
        minuto_int = int(hora_parts[1])
        
        # Criar agendador
        scheduler = BackgroundScheduler()
        
        # Agendar tarefa
        trigger = CronTrigger(hour=hora_int, minute=minuto_int)
        scheduler.add_job(
            executar_coleta,
            trigger=trigger,
            id="shopee_daily_trends",
            name="Coleta Diária de Tendências Shopee",
            replace_existing=True
        )
        
        # Iniciar
        scheduler.start()
        
        logger.info(f"✅ Agendador iniciado (APScheduler)")
        logger.info(f"   Próxima execução: {scheduler.get_job('shopee_daily_trends').next_run_time}")
        logger.info(f"   Horário: {hora}")
        
        # Manter rodando
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Agendador parado pelo usuário")
            scheduler.shutdown()
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar agendador: {e}", exc_info=True)
        return False


# ============================================================
# AGENDADOR COM MANUS SCHEDULER
# ============================================================
def gerar_config_manus_scheduler(hora: str = "08:00") -> dict:
    """
    Gera configuração para Manus Scheduler.
    
    Retorna dict que pode ser usado com manus-config schedule.
    """
    return {
        "name": "shopee_daily_trends",
        "description": "Coleta diária de tendências da Shopee",
        "command": f"cd /home/ubuntu/dev && python3 scheduler_shopee_daily.py --execute",
        "schedule": f"0 {hora.split(':')[0]} * * *",  # Cron format
        "timezone": "America/Sao_Paulo",
        "enabled": True,
    }


# ============================================================
# AGENDADOR COM CRON
# ============================================================
def gerar_crontab_entry(hora: str = "08:00") -> str:
    """
    Gera entrada de crontab para agendamento.
    
    Exemplo de uso:
        python scheduler_shopee_daily.py --cron 08:00 >> /etc/crontab
    """
    hora_parts = hora.split(":")
    hora_int = int(hora_parts[0])
    minuto_int = int(hora_parts[1])
    
    return f"{minuto_int} {hora_int} * * * cd /home/ubuntu/dev && python3 scheduler_shopee_daily.py --execute"


# ============================================================
# INTERFACE CLI
# ============================================================
def main():
    """Interface CLI do agendador."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Agendador de Coleta Diária de Tendências Shopee"
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Executar coleta imediatamente"
    )
    
    parser.add_argument(
        "--scheduler",
        choices=["apscheduler", "manus", "cron"],
        default="apscheduler",
        help="Tipo de agendador a usar"
    )
    
    parser.add_argument(
        "--hora",
        default="08:00",
        help="Hora de execução (HH:MM, padrão: 08:00)"
    )
    
    parser.add_argument(
        "--historico",
        type=int,
        default=30,
        help="Dias de histórico a exibir"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Exibir status das últimas execuções"
    )
    
    args = parser.parse_args()
    
    # Executar imediatamente
    if args.execute:
        logger.info("Executando coleta imediatamente...")
        resultado = executar_coleta()
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        return 0
    
    # Exibir status
    if args.status:
        logger.info(f"Histórico dos últimos {args.historico} dias:")
        historico = obter_historico_execucoes(dias=args.historico)
        
        if historico:
            for execucao in historico[-10:]:  # Últimas 10
                timestamp = execucao.get("timestamp", "N/A")
                status = execucao.get("status", "N/A")
                total = execucao.get("total_termos", "N/A")
                print(f"  {timestamp}: {status} ({total} termos)")
        else:
            print("  Nenhuma execução registrada")
        
        return 0
    
    # Gerar configuração
    if args.scheduler == "manus":
        config = gerar_config_manus_scheduler(args.hora)
        print("Configuração para Manus Scheduler:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return 0
    
    if args.scheduler == "cron":
        crontab = gerar_crontab_entry(args.hora)
        print("Entrada para crontab:")
        print(crontab)
        return 0
    
    # Iniciar agendador
    if args.scheduler == "apscheduler":
        return 0 if iniciar_agendador_apscheduler(args.hora) else 1
    
    return 0


if __name__ == "__main__":
    from datetime import timedelta
    sys.exit(main())
