"""Comando de compatibilidade para atualizar tendências oficiais do Mercado Livre.

Este arquivo não edita listas no código-fonte. A atualização é delegada ao
coletor canônico, que valida a página oficial antes de persistir o cache.
"""

from __future__ import annotations

import logging

from modules.mercadolivre_scraper import forcar_atualizacao_ml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def capturar_tendencias_ml():
    """Mantém a API legada, retornando apenas termos confirmados na página oficial."""
    return list(forcar_atualizacao_ml().keys())


def atualizar_modulo_produtos(_novos_termos):
    """Mantido por compatibilidade; a grade agora lê o cache, não listas estáticas."""
    logger.info("Nenhum arquivo de código será alterado; a grade usa o cache oficial.")
    return True


if __name__ == "__main__":
    termos = capturar_tendencias_ml()
    if not termos:
        raise SystemExit("Nenhuma tendência oficial do Mercado Livre foi confirmada.")
    print(f"Mercado Livre oficial: {len(termos)} termos atualizados.")
