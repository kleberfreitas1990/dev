#!/usr/bin/env python3
"""
Teste de Importação do Módulo Watermark Remover
Verifica se o módulo pode ser carregado sem erros
"""

import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, '/home/ubuntu/dev')

def test_import():
    """Testa a importação do módulo"""
    try:
        from modules.watermark_remover import (
            render_watermark_remover,
            PRESETS_SHOPEE,
            ALGORITMOS_INPAINTING,
            calcular_coordenadas_reais,
            extrair_primeiro_frame,
            obter_informacoes_video,
            extrair_audio,
            remover_marca_dagua,
            muxar_audio_video,
            processar_video_completo
        )
        
        print("✅ Importação bem-sucedida!")
        print(f"✅ Presets disponíveis: {len(PRESETS_SHOPEE)}")
        print(f"✅ Algoritmos disponíveis: {len(ALGORITMOS_INPAINTING)}")
        
        # Testa presets
        print("\n📋 Presets Shopee:")
        for nome, config in PRESETS_SHOPEE.items():
            print(f"  - {config['icone']} {nome}")
        
        # Testa algoritmos
        print("\n🔧 Algoritmos de Inpainting:")
        for nome in ALGORITMOS_INPAINTING.keys():
            print(f"  - {nome}")
        
        # Testa função de cálculo de coordenadas
        print("\n🧮 Teste de Cálculo de Coordenadas:")
        x, y, w, h = calcular_coordenadas_reais(
            altura_frame=1080,
            largura_frame=1920,
            x_percent=0.75,
            y_percent=0.85,
            width_percent=0.20,
            height_percent=0.12
        )
        print(f"  Frame 1920×1080 → Coordenadas: X={x}, Y={y}, W={w}, H={h}")
        
        return True
    
    except ImportError as e:
        print(f"❌ Erro de Importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro Inesperado: {e}")
        return False

if __name__ == "__main__":
    sucesso = test_import()
    sys.exit(0 if sucesso else 1)
