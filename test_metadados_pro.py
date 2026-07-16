import ast
from pathlib import Path


MODULO = Path(__file__).parent / "modules" / "metadados_pro.py"


def carregar_funcao(nome):
    arvore = ast.parse(MODULO.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name == nome:
            modulo = ast.Module(body=[no], type_ignores=[])
            namespace = {"datetime": __import__("datetime").datetime, "timezone": __import__("datetime").timezone}
            exec(compile(modulo, str(MODULO), "exec"), namespace)
            return namespace[nome]
    raise AssertionError(f"Função {nome} não encontrada")


def test_comando_ffmpeg_nao_falsifica_origem_de_hardware():
    construir = carregar_funcao("construir_comando_ffmpeg")
    comando = construir("entrada.mp4", "saida.mp4")
    texto = " ".join(comando).lower()

    assert "libx264" in comando
    assert "vendor_id" not in texto
    assert "handler_vendor_id" not in texto
    assert "com.apple.avfoundation" not in texto
    assert "omx.sec.avc.encoder" not in texto
    assert "make=apple" not in texto
    assert "make=samsung" not in texto


def test_comando_remove_metadados_anteriores():
    construir = carregar_funcao("construir_comando_ffmpeg")
    comando = construir("entrada.mp4", "saida.mp4")

    assert comando[comando.index("-map_metadata") + 1] == "-1"
    assert comando[comando.index("-map_chapters") + 1] == "-1"


def test_localizacao_inclui_altitude_no_iso6709():
    construir = carregar_funcao("construir_comando_ffmpeg")
    comando = construir(
        "entrada.mp4",
        "saida.mp4",
        coordenadas=(-23.5505, -46.6333),
        altitude=760,
    )
    texto = " ".join(comando)

    assert "-23.5505-46.6333+760CRS/" in texto


def test_interface_nao_contem_gatilho_automatico_por_url():
    codigo = MODULO.read_text(encoding="utf-8")

    assert "last_processed_url" not in codigo
    assert "Gatilho Automático" not in codigo
    assert 'if st.button(' in codigo
    assert '"Limpar metadados"' in codigo
    assert '"Baixar vídeo limpo"' in codigo
