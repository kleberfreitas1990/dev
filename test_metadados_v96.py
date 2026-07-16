import hashlib
import os
import subprocess
import tempfile
import unittest
from modules import metadados_pro

class MetadadosV96Test(unittest.TestCase):
    def _get_hash(self, path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def test_assinatura_digital_alterada(self):
        """Verifica se a reencodificação altera o hash do arquivo e remove metadados suspeitos."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f_in:
            # Cria um vídeo de teste mínimo usando ffmpeg
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=30",
                "-c:v", "libx264", "-metadata", "comment=ORIGINAL_VIDEO",
                "-metadata", "encoder=Lavc_Original", f_in.name
            ], capture_output=True)
            path_in = f_in.name

        path_out = path_in + "_limpo.mp4"
        
        try:
            hash_in = self._get_hash(path_in)
            
            # Executa a limpeza v9.6
            sucesso = metadados_pro.limpar_metadados_ffmpeg(path_in, path_out)
            self.assertTrue(sucesso)
            
            hash_out = self._get_hash(path_out)
            
            # 1. O Hash deve ser diferente (Assinatura digital mudou)
            self.assertNotEqual(hash_in, hash_out, "O hash do arquivo não mudou!")
            
            # 2. Verificar metadados via ffprobe
            probe = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_format", "-show_streams", "-print_format", "json", path_out
            ], capture_output=True, text=True)
            dados = probe.stdout
            
            # Não deve conter 'lavfi' ou o comentário original
            self.assertNotIn("ORIGINAL_VIDEO", dados)
            self.assertNotIn("Lavc_Original", dados)
            
            # Verificar se o hash mudou (objetivo principal da antiduplicação)
            self.assertNotEqual(hash_in, hash_out, "O hash do arquivo não mudou!")
            
        finally:
            for p in [path_in, path_out]:
                if os.path.exists(p):
                    os.remove(p)

if __name__ == "__main__":
    unittest.main()
