#!/usr/bin/env python3
"""
Teste de Integração do Módulo Metadados Pro Unificado
Verifica se todas as funções necessárias estão presentes e compilam sem erros
"""

import sys
import os

sys.path.insert(0, '/home/ubuntu/dev')

def test_integration():
    try:
        from modules.metadados_pro import (
            render_metadados_pro,
            PRESETS_SHOPEE,
            ALGORITMOS_INPAINTING,
            calcular_coordenadas_reais,
            processar_remocao_marca_dagua,
            limpar_metadados_ffmpeg
        )
        
        print("✅ Módulo metadados_pro importado com sucesso!")
        print(f"✅ Presets Shopee: {len(PRESETS_SHOPEE)}")
        print(f"✅ Algoritmos Inpainting: {len(ALGORITMOS_INPAINTING)}")
        
        # Valida cálculo de coordenadas
        x, y, w, h = calcular_coordenadas_reais(1080, 1920, 0.75, 0.85, 0.20, 0.12)
        print(f"✅ Cálculo de coordenadas OK: X={x}, Y={y}, W={w}, H={h}")
        
        return True
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False

if __name__ == "__main__":
    sucesso = test_integration()
    sys.exit(0 if sucesso else 1)
