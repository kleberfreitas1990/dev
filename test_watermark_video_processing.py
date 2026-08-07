#!/usr/bin/env python3
"""
Teste Funcional de Processamento de Vídeo
Cria um vídeo sintético e testa as funções de remoção de marca d'água
"""

import sys
import os
import cv2
import numpy as np
import tempfile

# Adiciona o diretório ao path
sys.path.insert(0, '/home/ubuntu/dev')

from modules.watermark_remover import (
    calcular_coordenadas_reais,
    obter_informacoes_video,
    extrair_primeiro_frame,
)

def criar_video_teste(caminho_saida: str, duracao_segundos: int = 2) -> bool:
    """
    Cria um vídeo sintético para testes.
    
    Args:
        caminho_saida: Caminho do arquivo de saída
        duracao_segundos: Duração do vídeo em segundos
    
    Returns:
        True se bem-sucedido
    """
    try:
        # Configurações do vídeo
        largura = 1920
        altura = 1080
        fps = 30
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        # Cria o writer
        out = cv2.VideoWriter(caminho_saida, fourcc, fps, (largura, altura))
        
        if not out.isOpened():
            print("❌ Não foi possível criar o writer de vídeo")
            return False
        
        # Número de frames
        num_frames = duracao_segundos * fps
        
        print(f"🎬 Criando vídeo de teste ({largura}×{altura}, {fps} FPS, {duracao_segundos}s)...")
        
        for frame_num in range(num_frames):
            # Cria um frame com gradiente
            frame = np.zeros((altura, largura, 3), dtype=np.uint8)
            
            # Fundo com gradiente
            for y in range(altura):
                cor = int(255 * (y / altura))
                frame[y, :] = [cor, cor // 2, 255 - cor]
            
            # Adiciona um texto animado
            texto = f"Frame {frame_num + 1}/{num_frames}"
            cv2.putText(
                frame, texto,
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (255, 255, 255),
                2
            )
            
            # Adiciona uma "marca d'água" simulada (Shopee logo)
            # Retângulo no canto inferior direito
            x1, y1 = 1600, 900
            x2, y2 = 1900, 1050
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), -1)
            cv2.putText(
                frame, "SHOPEE",
                (x1 + 50, y1 + 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2
            )
            
            out.write(frame)
        
        out.release()
        
        if os.path.exists(caminho_saida):
            tamanho_mb = os.path.getsize(caminho_saida) / (1024 * 1024)
            print(f"✅ Vídeo de teste criado: {caminho_saida} ({tamanho_mb:.2f} MB)")
            return True
        else:
            print("❌ Arquivo de vídeo não foi criado")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao criar vídeo de teste: {e}")
        return False

def test_obter_informacoes():
    """Testa a função obter_informacoes_video"""
    print("\n🧪 Testando obter_informacoes_video...")
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        caminho_video = tmp.name
    
    try:
        # Cria vídeo de teste
        if not criar_video_teste(caminho_video):
            return False
        
        # Obtém informações
        info = obter_informacoes_video(caminho_video)
        
        print(f"  📐 Resolução: {info['largura']}×{info['altura']}")
        print(f"  🎞️ FPS: {info['fps']}")
        print(f"  ⏱️ Duração: {info['duracao_segundos']}s")
        print(f"  📊 Total de frames: {info['total_frames']}")
        
        # Validações
        assert info['largura'] == 1920, "Largura incorreta"
        assert info['altura'] == 1080, "Altura incorreta"
        assert info['fps'] == 30, "FPS incorreto"
        assert info['duracao_segundos'] == 2, "Duração incorreta"
        
        print("✅ obter_informacoes_video funcionando corretamente")
        return True
    
    except AssertionError as e:
        print(f"❌ Erro: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        if os.path.exists(caminho_video):
            os.remove(caminho_video)

def test_extrair_primeiro_frame():
    """Testa a função extrair_primeiro_frame"""
    print("\n🧪 Testando extrair_primeiro_frame...")
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        caminho_video = tmp.name
    
    try:
        # Cria vídeo de teste
        if not criar_video_teste(caminho_video):
            return False
        
        # Extrai primeiro frame
        frame = extrair_primeiro_frame(caminho_video)
        
        print(f"  📐 Frame shape: {frame.shape}")
        print(f"  📊 Tipo de dados: {frame.dtype}")
        
        # Validações
        assert frame.shape == (1080, 1920, 3), "Shape do frame incorreto"
        assert frame.dtype == np.uint8, "Tipo de dados incorreto"
        
        print("✅ extrair_primeiro_frame funcionando corretamente")
        return True
    
    except AssertionError as e:
        print(f"❌ Erro: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        if os.path.exists(caminho_video):
            os.remove(caminho_video)

def test_calcular_coordenadas():
    """Testa a função calcular_coordenadas_reais"""
    print("\n🧪 Testando calcular_coordenadas_reais...")
    
    try:
        # Teste 1: Canto inferior direito (padrão Shopee)
        x, y, w, h = calcular_coordenadas_reais(
            altura_frame=1080,
            largura_frame=1920,
            x_percent=0.75,
            y_percent=0.85,
            width_percent=0.20,
            height_percent=0.12
        )
        
        print(f"  📍 Canto Inferior Direito: X={x}, Y={y}, W={w}, H={h}")
        assert x == 1440, f"X incorreto: {x}"
        assert y == 918, f"Y incorreto: {y}"
        assert w == 384, f"W incorreto: {w}"
        assert h == 129, f"H incorreto: {h}"
        
        # Teste 2: Canto superior esquerdo
        x, y, w, h = calcular_coordenadas_reais(
            altura_frame=1080,
            largura_frame=1920,
            x_percent=0.02,
            y_percent=0.02,
            width_percent=0.18,
            height_percent=0.10
        )
        
        print(f"  📍 Canto Superior Esquerdo: X={x}, Y={y}, W={w}, H={h}")
        assert x == 38, f"X incorreto: {x}"
        assert y == 21, f"Y incorreto: {y}"
        
        # Teste 3: Validação de limites
        x, y, w, h = calcular_coordenadas_reais(
            altura_frame=1080,
            largura_frame=1920,
            x_percent=0.95,  # Muito à direita
            y_percent=0.95,  # Muito abaixo
            width_percent=0.20,
            height_percent=0.20
        )
        
        print(f"  📍 Limites Validados: X={x}, Y={y}, W={w}, H={h}")
        assert x >= 0 and x < 1920, "X fora dos limites"
        assert y >= 0 and y < 1080, "Y fora dos limites"
        assert w > 0 and w <= 1920, "W inválido"
        assert h > 0 and h <= 1080, "H inválido"
        
        print("✅ calcular_coordenadas_reais funcionando corretamente")
        return True
    
    except AssertionError as e:
        print(f"❌ Erro: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando Testes Funcionais de Processamento de Vídeo...\n")
    
    teste1 = test_calcular_coordenadas()
    teste2 = test_obter_informacoes()
    teste3 = test_extrair_primeiro_frame()
    
    print("\n" + "="*60)
    if teste1 and teste2 and teste3:
        print("✅ TODOS OS TESTES FUNCIONAIS PASSARAM!")
        sys.exit(0)
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        sys.exit(1)
