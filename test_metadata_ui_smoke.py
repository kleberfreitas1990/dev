from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).parent / "metadata_ui_harness.py"


def test_metadata_pro_carrega_sem_excecao():
    APP.write_text(
        "from modules.metadados_pro import render_metadados_pro\n"
        "render_metadados_pro()\n",
        encoding="utf-8",
    )
    try:
        teste = AppTest.from_file(str(APP)).run(timeout=10)
        assert not teste.exception
        assert teste.button[0].label == "Limpar metadados" if teste.button else True
    finally:
        APP.unlink(missing_ok=True)
