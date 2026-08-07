#!/usr/bin/env python3
"""
Teste de Regressão para Metadados Pro
Verifica se o módulo metadados_pro.py continua funcionando após as alterações
"""

import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, '/home/ubuntu/dev')

def test_metadados_pro_import():
    """Testa a importação do módulo metadados_pro"""
    try:
        from modules.metadados_pro import (
            render_metadados_pro,
            LOCALIZACOES_REAIS,
            gerar_nome_arquivo_limpo,
            validar_url_video,
            construir_comando_ffmpeg,
            limpar_metadados_ffmpeg
        )
        
        print("✅ Módulo metadados_pro importado com sucesso!")
        print(f"✅ Localizações disponíveis: {len(LOCALIZACOES_REAIS)}")
        
        # Testa geração de nome
        nome = gerar_nome_arquivo_limpo()
        print(f"✅ Nome gerado: {nome}")
        
        # Testa validação de URL
        url_valida = "https://example.com/video.mp4"
        url_invalida = "não é uma URL"
        
        assert validar_url_video(url_valida) == True, "URL válida deveria ser aceita"
        assert validar_url_video(url_invalida) == False, "URL inválida deveria ser rejeitada"
        print("✅ Validação de URL funcionando corretamente")
        
        return True
    
    except ImportError as e:
        print(f"❌ Erro de Importação: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Erro de Asserção: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro Inesperado: {e}")
        return False

def test_marketplace_import():
    """Testa a importação do marketplace.app.py"""
    try:
        # Verifica se o arquivo pode ser compilado
        import py_compile
        py_compile.compile('/home/ubuntu/dev/marketplace.app.py', doraise=True)
        print("✅ marketplace.app.py compilado com sucesso!")
        
        # Verifica se as importações estão corretas
        with open('/home/ubuntu/dev/marketplace.app.py', 'r') as f:
            conteudo = f.read()
        
        assert 'from modules.watermark_remover import render_watermark_remover' in conteudo, \
            "Importação do watermark_remover não encontrada"
        print("✅ Importação do watermark_remover presente no marketplace.app.py")
        
        assert 'tab_watermark' in conteudo, "Variável tab_watermark não encontrada"
        print("✅ Variável tab_watermark presente no marketplace.app.py")
        
        assert 'render_watermark_remover()' in conteudo, "Chamada de render_watermark_remover não encontrada"
        print("✅ Chamada de render_watermark_remover presente no marketplace.app.py")
        
        return True
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando Testes de Regressão...\n")
    
    print("1️⃣ Testando Metadados Pro...")
    teste1 = test_metadados_pro_import()
    
    print("\n2️⃣ Testando Marketplace App...")
    teste2 = test_marketplace_import()
    
    print("\n" + "="*50)
    if teste1 and teste2:
        print("✅ TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        sys.exit(1)
