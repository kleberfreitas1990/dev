import os
import subprocess
import tempfile
import unittest
from modules import metadados_pro

class MetadadosV97Test(unittest.TestCase):
    def test_disfarce_de_encoder_remove_lavc_lavf(self):
        """Verifica se a v9.7 remove as tags Lavc e Lavf do arquivo final."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f_in:
            # Cria um vídeo de teste que naturalmente teria tags Lavc/Lavf
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=30",
                "-c:v", "libx264", f_in.name
            ], capture_output=True)
            path_in = f_in.name

        path_out = path_in + "_v97.mp4"
        
        try:
            # Executa a limpeza v9.7
            sucesso = metadados_pro.limpar_metadados_ffmpeg(path_in, path_out)
            self.assertTrue(sucesso)
            
            # Verificar metadados via ffprobe
            probe = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_format", "-show_streams", "-print_format", "json", path_out
            ], capture_output=True, text=True)
            dados = probe.stdout.lower()
            
            # 1. Não deve conter as marcas do FFmpeg
            self.assertNotIn("lavc", dados, "Tag 'Lavc' ainda presente nos metadados!")
            self.assertNotIn("lavf", dados, "Tag 'Lavf' ainda presente nos metadados!")
            
            # 2. Deve conter o disfarce
            self.assertIn("camera", dados)
            
        finally:
            for p in [path_in, path_out]:
                if os.path.exists(p):
                    os.remove(p)

if __name__ == "__main__":
    unittest.main()
