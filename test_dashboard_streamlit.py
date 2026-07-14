import unittest

from streamlit.testing.v1 import AppTest


class DashboardStreamlitSmokeTest(unittest.TestCase):
    def test_dashboard_renderiza_sem_import_error(self):
        app = AppTest.from_string(
            "from modules.views import render_dashboard\nrender_dashboard()\n",
            default_timeout=20,
        )
        app.run()

        erros = [str(excecao.value) for excecao in app.exception]
        self.assertEqual(erros, [], msg="Exceções no dashboard: " + " | ".join(erros))


if __name__ == "__main__":
    unittest.main()
