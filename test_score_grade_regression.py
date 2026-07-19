"""Regressão para scores de ranking exibidos na grade e no dashboard."""

import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from modules import produtos_dinamicos, views


class ScoreGradeRegressionTest(unittest.TestCase):
    @staticmethod
    def _produto(score: int, fonte: str) -> dict:
        return {
            "score": score,
            "crescimento": 0,
            "categoria": "Teste",
            "evento": "Ranking oficial",
            "fonte": fonte,
            "tendencia": "Em destaque",
        }

    def test_dashboard_renderiza_scores_de_ranking_sem_excecao(self) -> None:
        dados = {
            "Termo líder Mercado Livre": self._produto(40, "Mercado Livre Trends"),
            "Produto líder Amazon": self._produto(30, "Amazon Bestsellers"),
        }

        with (
            patch.object(
                produtos_dinamicos,
                "obter_produtos_marketplace_v49",
                return_value=dados,
            ),
            patch.object(views, "gerar_top10_produtos", return_value=[]),
            patch.object(views, "render_grade_descoberta"),
            patch.object(views, "render_insights_estrategicos"),
            patch.object(views, "render_apoiadores_compactos"),
        ):
            app = AppTest.from_string(
                "from modules.views import render_dashboard\nrender_dashboard()\n",
                default_timeout=20,
            )
            app.run()

        erros = [str(excecao.value) for excecao in app.exception]
        self.assertEqual(erros, [], msg="Exceções no dashboard: " + " | ".join(erros))


if __name__ == "__main__":
    unittest.main()
