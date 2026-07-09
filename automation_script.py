import os
import sys
import logging
from datetime import datetime

# Adiciona o diretório atual ao path para importar os módulos
sys.path.append(os.getcwd())

from modules.produtos_dinamicos import obter_produtos_dinamicos
from modules.logger import registrar_busca

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutomationScript")

def executar_atualizacao_automatica():
    """
    Executa a captura de dados reais e atualiza o cache do sistema.
    """
    try:
        logger.info(f"🚀 Iniciando atualização automática: {datetime.now()}")
        
        # Força a atualização dos produtos dinâmicos (Selenium -> Shopee -> Serper)
        produtos = obter_produtos_dinamicos(forcar_atualizacao=True)
        
        if produtos:
            total = len(produtos)
            logger.info(f"✅ Atualização concluída com sucesso! {total} produtos capturados.")
            registrar_busca(
                nivel="sistema",
                termo="automacao_agendada",
                sucesso=True,
                quantidade=total,
                detalhes=f"Execução automática via agendador Manus."
            )
        else:
            logger.warning("⚠️ Nenhum produto capturado na atualização automática.")
            
    except Exception as e:
        logger.error(f"❌ Erro na atualização automática: {str(e)}")
        registrar_busca(
            nivel="sistema",
            termo="automacao_agendada",
            sucesso=False,
            detalhes=f"Erro: {str(e)}"
        )

if __name__ == "__main__":
    executar_atualizacao_automatica()
