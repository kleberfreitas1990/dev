#!/usr/bin/env python3
"""
Teste de Integração: Download via Link + Metadados Pro
"""

import sys
import os

sys.path.insert(0, '/home/ubuntu/dev')

def test_link_feature():
    try:
        from modules.metadados_pro import (
            render_metadados_pro,
            validar_url_video,
            baixar_video_yt_dlp,
            limpar_metadados_ffmpeg
        )
        
        print("✅ Módulo importado com sucesso!")
        
        # Valida URLs
        assert validar_url_video("https://www.tiktok.com/@test/video/123") == True
        assert validar_url_video("https://www.instagram.com/reel/abc/") == True
        assert validar_url_video("invalid-url") == False
        print("✅ Validação de URLs funcionando corretamente!")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    res = test_link_feature()
    sys.exit(0 if res else 1)
