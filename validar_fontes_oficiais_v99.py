"""Valida as duas fontes oficiais sem aceitar listas estáticas como substituição."""

from __future__ import annotations

from modules.amazon_scraper import capturar_bestsellers_amazon
from modules.mercadolivre_scraper import forcar_atualizacao_ml


def main() -> int:
    mercado_livre = forcar_atualizacao_ml()
    amazon = capturar_bestsellers_amazon(forcar=True)

    print(f"Mercado Livre oficial confirmado: {len(mercado_livre)} termos")
    print(f"Amazon Best Sellers oficial confirmado: {len(amazon)} produtos")

    # A Amazon pode bloquear uma sessão temporariamente. O resultado vazio é
    # informativo e não autoriza a criação de fallback artificial.
    return 0 if mercado_livre else 1


if __name__ == "__main__":
    raise SystemExit(main())
