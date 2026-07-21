"""
Script de teste para verificar se os scrapers de ML e Amazon funcionam corretamente.
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mercadolivre():
    """Testa o scraper do Mercado Livre"""
    print("\n" + "="*60)
    print("🛒 TESTANDO MERCADO LIVRE")
    print("="*60)
    
    from modules.mercadolivre_scraper import forcar_atualizacao_ml, obter_status_cache_ml
    
    resultado = forcar_atualizacao_ml()
    print(f"✅ ML: {len(resultado)} termos coletados")
    
    if resultado:
        print("\n📋 Primeiros 10 termos:")
        for i, (termo, dados) in enumerate(list(resultado.items())[:10]):
            print(f"  {i+1}. {termo} (Score: {dados.get('score', 0)})")
    
    status = obter_status_cache_ml()
    print(f"\n📊 Status do cache ML:")
    print(f"  Válido: {status.get('valido')}")
    print(f"  Total: {status.get('total')}")
    print(f"  Data: {status.get('data_formatada')}")
    
    return len(resultado) > 0

def test_amazon():
    """Testa o scraper da Amazon"""
    print("\n" + "="*60)
    print("📦 TESTANDO AMAZON")
    print("="*60)
    
    from modules.amazon_scraper import capturar_bestsellers_amazon, obter_status_cache_amazon
    
    resultado = capturar_bestsellers_amazon(forcar=True)
    print(f"✅ Amazon: {len(resultado)} produtos coletados")
    
    if resultado:
        print("\n📋 Primeiros 10 produtos:")
        for i, (nome, dados) in enumerate(list(resultado.items())[:10]):
            print(f"  {i+1}. {nome[:60]}... (Score: {dados.get('score', 0)})")
    
    status = obter_status_cache_amazon()
    print(f"\n📊 Status do cache Amazon:")
    print(f"  Válido: {status.get('valido')}")
    print(f"  Total: {status.get('total')}")
    print(f"  Data: {status.get('data_formatada')}")
    
    return len(resultado) > 0

def test_pipeline_dinamico():
    """Testa o pipeline completo de produtos dinâmicos"""
    print("\n" + "="*60)
    print("🔄 TESTANDO PIPELINE DE PRODUTOS DINÂMICOS")
    print("="*60)
    
    from modules.produtos_dinamicos import obter_produtos_dinamicos
    
    produtos = obter_produtos_dinamicos(forcar_atualizacao=True)
    print(f"✅ Total de produtos na grade: {len(produtos)}")
    
    # Contar por fonte
    fontes = {}
    for nome, dados in produtos.items():
        fonte = dados.get("fonte", "Desconhecida")
        fontes[fonte] = fontes.get(fonte, 0) + 1
    
    print("\n📊 Distribuição por fonte:")
    for fonte, count in sorted(fontes.items(), key=lambda x: -x[1]):
        print(f"  {fonte}: {count} produtos")
    
    return len(produtos) > 0

if __name__ == "__main__":
    success_ml = False
    success_amazon = False
    success_pipeline = False
    
    try:
        success_ml = test_mercadolivre()
    except Exception as e:
        print(f"❌ Erro no teste ML: {e}")
    
    try:
        success_amazon = test_amazon()
    except Exception as e:
        print(f"❌ Erro no teste Amazon: {e}")
    
    try:
        success_pipeline = test_pipeline_dinamico()
    except Exception as e:
        print(f"❌ Erro no teste pipeline: {e}")
    
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    print(f"  Mercado Livre: {'✅ PASSOU' if success_ml else '❌ FALHOU'}")
    print(f"  Amazon:        {'✅ PASSOU' if success_amazon else '❌ FALHOU'}")
    print(f"  Pipeline:      {'✅ PASSOU' if success_pipeline else '❌ FALHOU'}")
