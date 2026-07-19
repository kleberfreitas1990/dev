"""Comando de compatibilidade para atualizar Best Sellers oficiais da Amazon Brasil.

A coleta e a validação de origem são centralizadas em ``modules.amazon_scraper``.
Este script não gera listas estáticas nem métricas artificiais.
"""

from __future__ import annotations

from modules.amazon_scraper import capturar_bestsellers_amazon


def capturar_amazon_bestsellers():
    """Mantém a API legada, retornando títulos confirmados pela página oficial."""
    return list(capturar_bestsellers_amazon(forcar=True).keys())


if __name__ == "__main__":
    termos = capturar_amazon_bestsellers()
    if not termos:
        raise SystemExit("Nenhum Best Seller oficial da Amazon foi confirmado.")
    print(f"Amazon Best Sellers oficial: {len(termos)} produtos atualizados.")
