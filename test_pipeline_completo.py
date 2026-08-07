#!/usr/bin/env python3
"""
Teste de Pipeline Completo: Watermark -> Metadados
Cria vídeo sintético com marca d'água, processa via pipeline unificado e verifica saída
"""

import sys
import os
import cv2
import numpy as np
import tempfile

sys.path.insert(0, '/home/ubuntu/dev')

from modules.metadados_pro import (
    calcular_coordenadas_reais,
    processar_remocao_marca_dagua,
    limpar_metadados_ffmpeg,
    obter_informacoes_video
)

def criar_video_com_logo(caminho: str):
    largura, altura, fps = 640, 360, 30
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(caminho, fourcc, fps, (largura, altura))
    
    for i in range(30): # 1 segundo
        frame = np.zeros((altura, largura, 3), dtype=np.uint8)
        frame[:, :] = [50, 100, 150]
        # Adiciona logo simulada no canto inferior direito
        cv2.rectangle(frame, (500, 280), (620, 340), (0, 0, 255), -1)
        cv2.putText(frame, "SHOPEE", (510, 315), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        out.write(frame)
    out.release()

def test_pipeline():
    print("🎬 Iniciando teste de pipeline completo...")
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_in:
        caminho_in = tmp_in.name
    
    caminho_sem_wm = None
    caminho_out = None
    
    try:
        criar_video_com_logo(caminho_in)
        print(f"✅ Vídeo de entrada criado: {caminho_in} ({os.path.getsize(caminho_in)/(1024*1024):.2f} MB)")
        
        info = obter_informacoes_video(caminho_in)
        rx, ry, rw, rh = calcular_coordenadas_reais(info['altura'], info['largura'], 0.75, 0.85, 0.20, 0.12)
        
        print("💧 Removendo marca d'água...")
        caminho_sem_wm = processar_remocao_marca_dagua(caminho_in, rx, ry, rw, rh)
        assert os.path.exists(caminho_sem_wm) and os.path.getsize(caminho_sem_wm) > 0, "Vídeo sem watermark não gerado"
        print(f"✅ Marca d'água removida com sucesso! ({os.path.getsize(caminho_sem_wm)/(1024*1024):.2f} MB)")
        
        print("🛡️ Aplicando antiduplicação e metadados...")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_out:
            caminho_out = tmp_out.name
        
        config = {
            "zoom": 1.01,
            "brilho": 0.02,
            "contraste": 1.02,
            "saturacao": 1.05,
            "hflip": False,
            "fps": 30.01,
            "audio_morph": True,
            "pitch": 1.005,
            "tempo": 1.001
        }
        coordenadas = (-23.5505, -46.6333)
        
        sucesso = limpar_metadados_ffmpeg(caminho_sem_wm, caminho_out, coordenadas, 760.0, config)
        assert sucesso and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0, "Falha no FFmpeg"
        print(f"✅ Vídeo final gerado com sucesso: {caminho_out} ({os.path.getsize(caminho_out)/(1024*1024):.2f} MB)")
        
        return True
    except Exception as e:
        print(f"❌ Erro no pipeline: {e}")
        return False
    finally:
        for p in [caminho_in, caminho_sem_wm, caminho_out]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

if __name__ == "__main__":
    res = test_pipeline()
    sys.exit(0 if res else 1)
