import os
import tempfile
import unittest

from modules import produtos_dinamicos


class ProdutosDinamicosCompatibilityTest(unittest.TestCase):
    def test_alias_marketplace_v49_esta_disponivel(self):
        produtos = produtos_dinamicos.obter_produtos_marketplace_v49()

        self.assertIsInstance(produtos, dict)
        self.assertGreaterEqual(len(produtos), len(produtos_dinamicos.TERMOS_PRINT))
        self.assertIn("iPhone 17", produtos)
        self.assertIn("score", produtos["iPhone 17"])

    def test_imports_publicos_usados_pelo_dashboard(self):
        self.assertTrue(callable(produtos_dinamicos.obter_produtos_dinamicos))
        self.assertTrue(callable(produtos_dinamicos.obter_produtos_marketplace_v49))
        self.assertTrue(callable(produtos_dinamicos.carregar_cache_produtos))
        self.assertTrue(callable(produtos_dinamicos.salvar_cache_produtos))
        self.assertTrue(callable(produtos_dinamicos.limpar_cache_produtos))
        self.assertTrue(callable(produtos_dinamicos.verificar_data_cache))
        self.assertIsInstance(produtos_dinamicos.PRODUTOS_FALLBACK, dict)

    def test_ciclo_de_vida_do_cache(self):
        caminho_original = produtos_dinamicos.CAMINHO_PRODUTOS_CACHE

        with tempfile.TemporaryDirectory() as diretorio:
            caminho_temporario = os.path.join(diretorio, "produtos_cache_v48.json")
            produtos_dinamicos.CAMINHO_PRODUTOS_CACHE = caminho_temporario
            try:
                self.assertTrue(produtos_dinamicos.salvar_cache_produtos({"Produto Teste": {"score": 10}}))
                cache = produtos_dinamicos.carregar_cache_produtos()
                self.assertIn("Produto Teste", cache["produtos"])
                self.assertTrue(produtos_dinamicos.verificar_data_cache()["cache_existe"])

                self.assertTrue(produtos_dinamicos.limpar_cache_produtos())
                self.assertFalse(os.path.exists(caminho_temporario))
                self.assertFalse(produtos_dinamicos.verificar_data_cache()["cache_existe"])
            finally:
                produtos_dinamicos.CAMINHO_PRODUTOS_CACHE = caminho_original


if __name__ == "__main__":
    unittest.main()
