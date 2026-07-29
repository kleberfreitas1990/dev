import os
import json
import logging
from datetime import datetime
from modules.database import (
    inicializar_db, 
    salvar_shopee_ciclo, 
    salvar_google_trends_ciclo, 
    obter_status_banco
)

logger = logging.getLogger(__name__)

def forcar_sincronizacao_json_to_db():
    """
    Lê os arquivos JSON de cache (que foram atualizados manualmente) 
    e força a inserção no SQLite para garantir que o painel mostre os dados novos.
    """
    logger.info("Iniciando sincronização forçada JSON -> SQLite")
    
    # Garante que o banco existe
    inicializar_db()
    
    DIRETORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Sincronizar Shopee
    sp_path = os.path.join(DIRETORIO_RAIZ, "shopee_live_cache.json")
    if os.path.exists(sp_path):
        try:
            with open(sp_path, "r", encoding="utf-8") as f:
                sp_data = json.load(f)
            itens = sp_data.get("dados", [])
            if itens:
                ciclo_id = salvar_shopee_ciclo(itens)
                logger.info(f"Shopee sincronizado: {len(itens)} itens (ciclo: {ciclo_id})")
        except Exception as e:
            logger.error(f"Erro ao sincronizar Shopee: {e}")

    # 2. Sincronizar Google Trends (que contém os termos Shopee Hot)
    gt_path = os.path.join(DIRETORIO_RAIZ, "google_trends_cache.json")
    if os.path.exists(gt_path):
        try:
            with open(gt_path, "r", encoding="utf-8") as f:
                gt_data = json.load(f)
            itens = gt_data.get("dados", [])
            if itens:
                ciclo_id = salvar_google_trends_ciclo(itens)
                logger.info(f"Google Trends sincronizado: {len(itens)} itens (ciclo: {ciclo_id})")
        except Exception as e:
            logger.error(f"Erro ao sincronizar Google Trends: {e}")

    return obter_status_banco()

if __name__ == "__main__":
    # Permite rodar via CLI para teste
    logging.basicConfig(level=logging.INFO)
    status = forcar_sincronizacao_json_to_db()
    print(json.dumps(status, indent=2))
