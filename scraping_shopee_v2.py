"""Compatibilidade do coletor legado de tendências da Shopee.

O fluxo principal é ``modules.shopee_daily_trends``: ele coleta dados quando
possível, filtra conteúdo adulto, registra a origem e persiste um cache diário.
Este arquivo preserva o ponto de entrada que gera ``shopee_trends.json`` para
consumidores legados.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from modules.shopee import TERMOS_REAIS_SHOPEE
from modules.shopee_daily_trends import executar_coleta_curada, executar_coleta_diaria


CAMINHO_SAIDA = Path(__file__).parent / "shopee_trends.json"


def capturar_shopee_v2(usar_curadoria: bool = False) -> Dict:
    """Executa a coleta normal ou aplica a curadoria explícita de tendências."""
    if usar_curadoria:
        return executar_coleta_curada(
            TERMOS_REAIS_SHOPEE,
            fonte="curadoria_manual_2026-08-14",
        )
    return executar_coleta_diaria(forcar_atualizacao=True)


def salvar_formato_legado(termos: List[str], fonte: str, atualizado_em: str) -> Dict[str, dict]:
    """Converte os termos filtrados no formato historicamente consumido."""
    dados: Dict[str, dict] = {}
    for posicao, termo in enumerate(termos, start=1):
        dados[termo] = {
            "pins": 0,
            "crescimento": max(50, 200 - (posicao * 5)),
            "views_tiktok": 0,
            "score": max(2, 10 - (posicao // 5)),
            "fonte": fonte,
            "origem_coleta": "rotina_diaria_filtrada",
            "atualizado": atualizado_em,
            "tendencia": "Em destaque",
        }
    return dados


def main() -> int:
    """Atualiza a Shopee e grava o artefato legado sem conteúdo adulto."""
    parser = argparse.ArgumentParser(description="Atualiza tendências diárias da Shopee.")
    parser.add_argument(
        "--usar-curadoria",
        action="store_true",
        help="Grava a curadoria atual de termos em vez de consultar fontes online.",
    )
    args = parser.parse_args()

    resultado = capturar_shopee_v2(usar_curadoria=args.usar_curadoria)
    termos = list(resultado.get("termos_completos", resultado.get("termos", [])))
    dados = salvar_formato_legado(
        termos,
        str(resultado.get("fonte", "rotina_diaria")),
        str(resultado.get("timestamp", datetime.now().isoformat())),
    )

    with CAMINHO_SAIDA.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    print(
        "Shopee atualizada: "
        f"{len(dados)} termos válidos; "
        f"{resultado.get('termos_bloqueados', 0)} bloqueado(s); "
        f"fonte={resultado.get('fonte', 'desconhecida')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
