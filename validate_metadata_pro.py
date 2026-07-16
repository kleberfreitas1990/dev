import ast
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent
MODULO = ROOT / "modules" / "metadados_pro.py"


def carregar_construtor():
    arvore = ast.parse(MODULO.read_text(encoding="utf-8"))
    funcao = next(
        no for no in arvore.body
        if isinstance(no, ast.FunctionDef) and no.name == "construir_comando_ffmpeg"
    )
    namespace = {"datetime": datetime, "timezone": timezone}
    exec(compile(ast.Module(body=[funcao], type_ignores=[]), str(MODULO), "exec"), namespace)
    return namespace["construir_comando_ffmpeg"]


def executar():
    construir = carregar_construtor()
    with tempfile.TemporaryDirectory() as pasta:
        entrada = Path(pasta) / "entrada.mp4"
        saida = Path(pasta) / "saida.mp4"

        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                "-metadata", "make=Apple",
                "-metadata", "model=iPhone 15 Pro Max",
                "-metadata", "encoder=com.apple.avfoundation.avcapturesession",
                "-metadata:s:v", "vendor_id=apl0",
                "-c:v", "libx264", "-c:a", "aac", "-shortest", "-y", str(entrada),
            ],
            check=True,
        )

        comando = construir(
            str(entrada),
            str(saida),
            coordenadas=(-23.5505, -46.6333),
            altitude=760,
            resolucao_alvo="320x240",
        )
        subprocess.run(comando, check=True)

        probe = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format_tags:stream_tags", "-of", "json", str(saida),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        metadados = json.loads(probe.stdout)
        texto = json.dumps(metadados, ensure_ascii=False).lower()

        assert saida.exists() and saida.stat().st_size > 0
        assert "iphone" not in texto
        assert "avfoundation" not in texto
        assert "apl0" not in texto
        assert "samsung" not in texto
        assert "location" in texto
        assert "creation_time" in texto

        print(json.dumps(metadados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    executar()
