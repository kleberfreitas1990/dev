import inspect
import json
import os
import tempfile
import unittest
from collections import Counter
from unittest.mock import Mock, patch

from modules.models import gerar_top10_produtos


class WidgetKeysRegressionTest(unittest.TestCase):
    def test_widgets_da_grade_incorporam_sufixo_de_contexto(self):
        from modules import views

        codigo_sidebar = inspect.getsource(views.render_sidebar_categorias)
        codigo_grade = inspect.getsource(views.render_grade_descoberta)

        self.assertIn('key=f"sidebar_categoria_filtro_{key_suffix}"', codigo_sidebar)
        self.assertIn('key=f"sidebar_btn_atualizar_{key_suffix}"', codigo_sidebar)
        self.assertIn('key=f"grade_quantidade_slider_{key_suffix}"', codigo_grade)
        self.assertIn('key=f"grade_fonte_filtro_{key_suffix}"', codigo_grade)
        self.assertIn('key=f"grade_btn_reload_{key_suffix}"', codigo_grade)


class Top10RegressionTest(unittest.TestCase):
    @staticmethod
    def _produto(fonte, crescimento, score=10, variacao=50, buscas=50000, evento="Tendência real"):
        return {
            "fonte": fonte,
            "categoria": "Teste",
            "evento": evento,
            "score": score,
            "crescimento": crescimento,
            "variacao": variacao,
            "buscas_mes": buscas,
            "pins": 10000,
            "views_tiktok": 10,
            "resultados_ml": 1000,
            "tendencia": "Em alta",
            "atualizado": "16/07/2026 14:00",
        }

    def test_top10_diversifica_fontes_em_empates_de_score(self):
        dados = {}
        for indice in range(7):
            dados[f"Shopee {indice}"] = self._produto("Shopee Live", 200 - indice)
        for indice in range(5):
            dados[f"ML {indice}"] = self._produto("Mercado Livre Trends (Real)", 190 - indice)
        for indice in range(5):
            dados[f"Amazon {indice}"] = self._produto("Amazon Bestsellers", 180 - indice)

        with patch("modules.models.obter_produtos_dinamicos", return_value=dados):
            ranking = gerar_top10_produtos(forcar_atualizacao=False)

        fontes = Counter(item["Fonte"].replace(" ✅", "") for item in ranking)
        self.assertEqual(len(ranking), 10)
        self.assertLessEqual(max(fontes.values()), 4)
        self.assertTrue({"Shopee Live", "Mercado Livre", "Amazon"}.issubset(fontes))

    def test_top10_muda_quando_metricas_atualizadas_mudam(self):
        ciclo_1 = {
            "Produto A": self._produto("Mercado Livre Trends (Real)", 100),
            "Produto B": self._produto("Mercado Livre Trends (Real)", 200),
        }
        ciclo_2 = {
            "Produto A": self._produto("Mercado Livre Trends (Real)", 250),
            "Produto B": self._produto("Mercado Livre Trends (Real)", 90),
        }

        with patch("modules.models.obter_produtos_dinamicos", return_value=ciclo_1) as obter:
            ranking_1 = gerar_top10_produtos(forcar_atualizacao=True)
            obter.assert_called_once_with(forcar_atualizacao=True)
        with patch("modules.models.obter_produtos_dinamicos", return_value=ciclo_2):
            ranking_2 = gerar_top10_produtos(forcar_atualizacao=False)

        self.assertEqual(ranking_1[0]["Produto"], "Produto b")
        self.assertEqual(ranking_2[0]["Produto"], "Produto a")
        self.assertNotEqual(ranking_1[0]["Produto"], ranking_2[0]["Produto"])


class AmazonFallbackRegressionTest(unittest.TestCase):
    def test_http_503_nao_publica_fallback_artificial(self):
        from modules import amazon_scraper

        resposta = Mock(status_code=503)
        resposta.raise_for_status.side_effect = amazon_scraper.requests.HTTPError("HTTP 503")
        with tempfile.TemporaryDirectory() as diretorio:
            cache = os.path.join(diretorio, "amazon_trends.json")
            with patch.object(amazon_scraper, "CAMINHO_CACHE_AMAZON", cache), patch.object(
                amazon_scraper.requests, "get", return_value=resposta
            ):
                produtos = amazon_scraper.capturar_bestsellers_amazon(forcar=True)

            self.assertEqual(produtos, {})
            self.assertFalse(os.path.exists(cache))


if __name__ == "__main__":
    unittest.main()
