import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

from modules.historico_tendencias import (
    listar_ciclos,
    obter_evolucao_produto,
    obter_produtos_persistentes,
    obter_resumo,
    registrar_ciclo,
)


class HistoricoTendenciasTest(unittest.TestCase):
    @staticmethod
    def _item(nome, score=10, crescimento=100, fonte="Mercado Livre"):
        return {
            "Produto": nome,
            "Fonte": fonte,
            "Categoria": "Teste",
            "Score": score,
            "Crescimento": f"+{crescimento}%",
            "Tendência": "Em alta",
            "Atualizado": f"ciclo-{crescimento}",
        }

    def test_snapshot_identico_nao_gera_ciclo_duplicado(self):
        with tempfile.TemporaryDirectory() as diretorio:
            banco = os.path.join(diretorio, "historico.db")
            ranking = [self._item("Produto A"), self._item("Produto B", 9, 80)]

            primeiro = registrar_ciclo(ranking, caminho_banco=banco)
            duplicado = registrar_ciclo(ranking, caminho_banco=banco)

            self.assertTrue(primeiro["registrado"])
            self.assertFalse(duplicado["registrado"])
            self.assertEqual(duplicado["motivo"], "snapshot_duplicado")
            self.assertEqual(len(listar_ciclos(caminho_banco=banco)), 1)

    def test_identifica_permanencia_consecutiva_no_ciclo_atual(self):
        with tempfile.TemporaryDirectory() as diretorio:
            banco = os.path.join(diretorio, "historico.db")
            inicio = datetime(2026, 7, 16, 10, 0)
            rankings = [
                [self._item("Produto A", 8, 40), self._item("Produto B", 7, 30)],
                [self._item("Produto A", 8, 50), self._item("Produto C", 8, 20)],
                [self._item("Produto A", 9, 60), self._item("Produto B", 8, 35)],
                [self._item("Produto A", 10, 70), self._item("Produto B", 9, 45)],
            ]

            for indice, ranking in enumerate(rankings):
                registrar_ciclo(
                    ranking,
                    capturado_em=inicio + timedelta(hours=indice),
                    caminho_banco=banco,
                )

            persistentes = obter_produtos_persistentes(minimo_ciclos=3, caminho_banco=banco)

            self.assertEqual([item["Produto"] for item in persistentes], ["Produto A"])
            self.assertEqual(persistentes[0]["Ciclos Consecutivos"], 4)
            self.assertEqual(persistentes[0]["Aparições Totais"], 4)

    def test_evolucao_e_resumo_refletem_os_ciclos_reais(self):
        with tempfile.TemporaryDirectory() as diretorio:
            banco = os.path.join(diretorio, "historico.db")
            inicio = datetime(2026, 7, 16, 10, 0)
            registrar_ciclo(
                [self._item("Cafeteira Elétrica", 8, 35)],
                capturado_em=inicio,
                caminho_banco=banco,
            )
            registrar_ciclo(
                [self._item("cafeteira eletrica", 9, 55)],
                capturado_em=inicio + timedelta(hours=2),
                caminho_banco=banco,
            )

            evolucao = obter_evolucao_produto("CAFETEIRA ELÉTRICA", caminho_banco=banco)
            resumo = obter_resumo(caminho_banco=banco)

            self.assertEqual(len(evolucao), 2)
            self.assertEqual([item["score"] for item in evolucao], [8.0, 9.0])
            self.assertEqual(resumo["total_ciclos"], 2)
            self.assertEqual(resumo["total_snapshots"], 2)
            self.assertEqual(resumo["produtos_unicos"], 1)


class HistoricoTendenciasStreamlitTest(unittest.TestCase):
    def test_painel_renderiza_com_produto_persistente(self):
        codigo = r'''
from streamlit.testing.v1 import AppTest

app = AppTest.from_string(r"""
import os
import tempfile
from datetime import datetime, timedelta
from modules import historico_tendencias as historico

historico.CAMINHO_BANCO_HISTORICO = os.path.join(
    tempfile.mkdtemp(prefix="historico_ui_"), "historico.db"
)
for indice in range(3):
    historico.registrar_ciclo(
        [{
            "Produto": "Produto Persistente",
            "Fonte": "Amazon",
            "Categoria": "Teste",
            "Score": 8 + indice,
            "Crescimento": f"+{40 + indice}%",
            "Tendência": "Em alta",
            "Atualizado": f"ciclo-{indice}",
        }],
        capturado_em=datetime(2026, 7, 16, 10, 0) + timedelta(hours=indice),
    )
historico.render_historico_tendencias()
""", default_timeout=20)
app.run()
erros = [str(excecao.value) for excecao in app.exception]
if erros:
    raise RuntimeError(" | ".join(erros))
'''
        resultado = subprocess.run(
            [sys.executable, "-c", codigo],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=40,
        )
        self.assertEqual(
            resultado.returncode,
            0,
            msg="Falha no smoke test do histórico:\n" + resultado.stdout + resultado.stderr,
        )


if __name__ == "__main__":
    unittest.main()
