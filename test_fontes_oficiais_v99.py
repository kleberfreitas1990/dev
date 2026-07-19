"""Testes de regressão para proveniência oficial e categorias da grade v9.9."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from modules import amazon_scraper, mercadolivre_scraper
from modules import produtos_dinamicos


class RespostaFalsa:
    """Resposta mínima compatível com requests para testes de parsing."""

    def __init__(self, texto: str, status_code: int = 200) -> None:
        self.text = texto
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class TestFontesOficiais(unittest.TestCase):
    def test_mercado_livre_aceita_somente_links_da_secao_de_termos(self) -> None:
        html = """
        <nav class="menu"><a href="https://lista.mercadolivre.com.br/celulares/acessorios#menu=categories">Acessórios para Celulares</a></nav>
        <nav aria-label="Termos mais procurados">
            <a class="nav-footer-seo__link" href="https://lista.mercadolivre.com.br/apple-watch">apple watch</a>
            <a class="nav-footer-seo__link" href="https://lista.mercadolivre.com.br/ar-condicionado">ar condicionado</a>
        </nav>
        """
        with patch.object(mercadolivre_scraper.requests, "get", return_value=RespostaFalsa(html)):
            termos = mercadolivre_scraper._raspar_tendencias_pagina()

        self.assertEqual(termos, ["apple watch", "ar condicionado"])
        self.assertNotIn("Acessórios para Celulares", termos)

    def test_mercado_livre_aplica_categorias_da_grade_corretamente(self) -> None:
        self.assertEqual(mercadolivre_scraper._inferir_categoria("apple watch"), "Eletrônicos")
        self.assertEqual(mercadolivre_scraper._inferir_categoria("ar condicionado"), "Eletrodomésticos")
        self.assertEqual(mercadolivre_scraper._inferir_categoria("tenis masculino"), "Moda")

    def test_amazon_extrai_titulo_posicao_e_link_da_pagina_oficial(self) -> None:
        html = """
        <ol id="zg-ordered-list">
          <li>
            <span class="zg-bdg-text">#1</span>
            <div class="p13n-sc-truncate">Fritadeira Air Fryer Teste</div>
            <a href="/dp/B000TESTE">Ver produto</a>
          </li>
          <li>
            <span class="zg-bdg-text">#2</span>
            <div class="p13n-sc-truncate">Livro de Teste</div>
            <a href="/dp/B000LIVRO">Ver produto</a>
          </li>
          <li>
            <span class="zg-bdg-text">#3</span>
            <div class="p13n-sc-truncate">Echo de Teste</div>
            <a href="/dp/B000ECHO">Ver produto</a>
          </li>
        </ol>
        """
        with patch.object(amazon_scraper.requests, "get", return_value=RespostaFalsa(html)):
            produtos = amazon_scraper._raspar_pagina_oficial()

        air_fryer = produtos["Fritadeira Air Fryer Teste"]
        self.assertEqual(air_fryer["posicao_ranking"], 1)
        self.assertEqual(air_fryer["categoria"], "Casa e Cozinha")
        self.assertEqual(air_fryer["url_produto"], "https://www.amazon.com.br/dp/B000TESTE")
        self.assertEqual(air_fryer["origem_coleta"], "pagina_oficial")
        self.assertEqual(air_fryer["url_fonte"], amazon_scraper.URL_BESTSELLERS_AMAZON)

    def test_caches_sem_proveniencia_oficial_sao_rejeitados(self) -> None:
        cache_legado = {"produtos": {"Produto": {"fonte": "Amazon Bestsellers"}}}
        self.assertFalse(amazon_scraper._cache_e_oficial(cache_legado))
        self.assertFalse(mercadolivre_scraper._cache_e_oficial(cache_legado))

    def test_pipeline_nao_mantem_listas_estaticas_de_mercado_livre(self) -> None:
        self.assertEqual(produtos_dinamicos.TERMOS_ML, ())
        self.assertEqual(produtos_dinamicos.TERMOS_PRINT, ())


if __name__ == "__main__":
    unittest.main(verbosity=2)
