import json
import os
import tempfile
import unittest
from unittest.mock import patch

from modules import grade_descoberta, produtos_dinamicos


class GradeAutoUpdateTest(unittest.TestCase):
    def test_cache_shopee_live_alimenta_produtos_dinamicos(self):
        caminhos_originais = {
            "live": produtos_dinamicos.CAMINHO_SHOPEE_LIVE_CACHE,
            "legacy": produtos_dinamicos.CAMINHO_SHOPEE_CACHE,
            "amazon": produtos_dinamicos.CAMINHO_AMAZON_CACHE,
            "produtos": produtos_dinamicos.CAMINHO_PRODUTOS_CACHE,
        }

        with tempfile.TemporaryDirectory() as diretorio:
            caminho_live = os.path.join(diretorio, "shopee_live_cache.json")
            with open(caminho_live, "w", encoding="utf-8") as arquivo:
                json.dump(
                    {
                        "timestamp": "2026-07-16T10:00:00",
                        "dados": [
                            {
                                "termo": "Produto Automático",
                                "vendas": "12.5k",
                                "avaliacao": 4.9,
                                "preco": "R$ 99,90",
                                "categoria": "Casa",
                                "fonte": "Shopee Live",
                            }
                        ],
                    },
                    arquivo,
                    ensure_ascii=False,
                )

            produtos_dinamicos.CAMINHO_SHOPEE_LIVE_CACHE = caminho_live
            produtos_dinamicos.CAMINHO_SHOPEE_CACHE = os.path.join(diretorio, "legacy.json")
            produtos_dinamicos.CAMINHO_AMAZON_CACHE = os.path.join(diretorio, "amazon.json")
            produtos_dinamicos.CAMINHO_PRODUTOS_CACHE = os.path.join(diretorio, "produtos.json")
            try:
                produtos = produtos_dinamicos.obter_produtos_dinamicos()
            finally:
                produtos_dinamicos.CAMINHO_SHOPEE_LIVE_CACHE = caminhos_originais["live"]
                produtos_dinamicos.CAMINHO_SHOPEE_CACHE = caminhos_originais["legacy"]
                produtos_dinamicos.CAMINHO_AMAZON_CACHE = caminhos_originais["amazon"]
                produtos_dinamicos.CAMINHO_PRODUTOS_CACHE = caminhos_originais["produtos"]

        self.assertIn("Produto Automático", produtos)
        self.assertEqual(produtos["Produto Automático"]["fonte"], "Shopee Live")
        self.assertGreaterEqual(produtos["Produto Automático"]["score"], 8)

    @patch("modules.produtos_dinamicos._forcar_atualizacao_google_shopee")
    def test_forcar_atualizacao_aciona_fontes_automaticas(self, atualizar):
        atualizar.return_value = {"google_trends": {"total": 1}, "shopee": {"total": 1}}

        produtos_dinamicos.obter_produtos_dinamicos(forcar_atualizacao=True)

        atualizar.assert_called_once_with()

    def test_grade_prioriza_dez_produtos_da_atualizacao_automatica(self):
        dados = {}
        fontes = [
            ("Shopee Live", 12),
            ("Amazon Bestsellers", 3),
            ("Shopee Real-Time Scraping", 3),
            ("Mercado Livre Trends", 4),
        ]
        for fonte, quantidade in fontes:
            for indice in range(quantidade):
                dados[f"{fonte} {indice}"] = {
                    "fonte": fonte,
                    "categoria": "Teste",
                    "score": 10,
                    "evento": "Atualizado",
                }

        with patch.object(grade_descoberta, "obter_produtos_marketplace_v49", return_value=dados):
            grade = grade_descoberta.descobrir_produtos_grade(quantidade=20)

        fontes_grade = [item["fonte"] for item in grade]
        self.assertEqual(len(grade), 20)
        self.assertEqual(fontes_grade[:10], ["Shopee Live"] * 10)
        self.assertEqual(fontes_grade.count("Amazon Bestsellers"), 3)
        self.assertEqual(fontes_grade.count("Shopee Real-Time Scraping"), 3)
        self.assertEqual(fontes_grade.count("Mercado Livre Trends"), 4)


if __name__ == "__main__":
    unittest.main()
