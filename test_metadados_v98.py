import os
import subprocess
import tempfile
import unittest
from modules import metadados_pro

class MetadadosV98Test(unittest.TestCase):
    def test_audio_morphing_processa_sem_erro(self):
        """Verifica se a v9.8 processa áudio com filtros de morphing sem falhar."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f_in:
            # Cria um vídeo de teste com áudio (tom de 440Hz)
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=30",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                "-c:v", "libx264", "-c:a", "aac", f_in.name
            ], capture_output=True)
            path_in = f_in.name

        path_out = path_in + "_v98.mp4"
        
        try:
            # Configuração v9.8 com Morphing agressivo para teste
            config = {
                "zoom": 1.01, "brilho": 0.02, "contraste": 1.02, "saturacao": 1.05,
                "hflip": False, "fps": 30.01,
                "audio_morph": True, "pitch": 1.02, "tempo": 1.01
            }
            
            # Executa a limpeza v9.8
            sucesso = metadados_pro.limpar_metadados_ffmpeg(path_in, path_out, antidup_config=config)
            self.assertTrue(sucesso)
            
            # Verificar se o áudio existe no arquivo de saída
            probe = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_streams", "-select_streams", "a", "-print_format", "json", path_out
            ], capture_output=True, text=True)
            import json
            dados = json.loads(probe.stdout)
            
            self.assertTrue(len(dados["streams"]) > 0, "O áudio foi perdido durante o morphing!")
            self.assertEqual(dados["streams"][0]["codec_name"], "aac")
            
        finally:
            for p in [path_in, path_out]:
                if os.path.exists(p):
                    os.remove(p)

if __name__ == "__main__":
    unittest.main()
