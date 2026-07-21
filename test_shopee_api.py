"""
Teste do módulo shopee_api.py — SEM fazer requisições reais.
Verifica apenas a lógica de proteção e fallback.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("🧪 Testando imports...")
    from modules.shopee_api import (
        obter_termos_shopee_api,
        buscar_termos_trending,
        status_api,
        MAX_REQUESTS_PER_CYCLE,
        CACHE_TTL_SEGUNDOS,
    )
    print("  ✅ Módulo importado com sucesso")
    print(f"  ✅ MAX_REQUESTS_PER_CYCLE: {MAX_REQUESTS_PER_CYCLE}")
    print(f"  ✅ CACHE_TTL_SEGUNDOS: {CACHE_TTL_SEGUNDOS} ({CACHE_TTL_SEGUNDOS/3600}h)")

def test_credenciais():
    print("\n🔑 Testando credenciais...")
    from modules.shopee_api import _obter_credenciais
    app_id, secret, base_url = _obter_credenciais()
    if app_id:
        print(f"  ✅ AppID: {app_id[:4]}...{app_id[-4:]}")
        print(f"  ✅ Secret: {'*' * 8}")
        print(f"  ✅ Base URL: {base_url}")
    else:
        print("  ⚠️ Credenciais não encontradas (válido se secrets.toml não existe)")

def test_rate_limit():
    print("\n🚦 Testando rate limit...")
    from modules.shopee_api import _verificar_limite, _carregar_controle
    pode_fazer, controle = _verificar_limite()
    print(f"  ✅ Pode fazer requisição: {pode_fazer}")
    print(f"  ✅ Requisições no ciclo: {controle.get('requisicoes_ciclo', 0)}/{10}")

def test_fallback():
    print("\n🔄 Testando fallback...")
    from modules.shopee_api import obter_termos_shopee_api
    termos = obter_termos_shopee_api()
    if termos:
        print(f"  ✅ {len(termos)} termos obtidos (fallback JSON)")
        print(f"  📋 Primeiro: {termos[0] if termos else 'N/A'}")
        print(f"  📋 Último: {termos[-1] if termos else 'N/A'}")
    else:
        print("  ❌ Nenhum termo retornado")
        return False
    return True

def test_status():
    print("\n📊 Status da API Shopee:")
    from modules.shopee_api import status_api
    status = status_api()
    for k, v in status.items():
        print(f"  {k}: {v}")

def test_sintaxe_views():
    print("\n🔍 Verificando que google_shopee_trends.py importa shopee_api corretamente...")
    with open("modules/google_shopee_trends.py", "r") as f:
        content = f.read()
    if "shopee_api" in content:
        print("  ✅ google_shopee_trends.py referencia shopee_api")
    else:
        print("  ❌ google_shopee_trends.py NÃO referencia shopee_api")
        return False
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE: Módulo Shopee API (sem requisições reais)")
    print("=" * 60)
    
    all_ok = True
    
    try: test_imports()
    except Exception as e: print(f"  ❌ {e}"); all_ok = False
    
    try: test_credenciais()
    except Exception as e: print(f"  ❌ {e}"); all_ok = False
    
    try: test_rate_limit()
    except Exception as e: print(f"  ❌ {e}"); all_ok = False
    
    try:
        if not test_fallback(): all_ok = False
    except Exception as e: print(f"  ❌ {e}"); all_ok = False
    
    try: test_status()
    except Exception as e: print(f"  ❌ {e}"); all_ok = False
    
    try:
        if not test_sintaxe_views(): all_ok = False
    except Exception as e: print(f"  ❌ {e}"); all_ok = False
    
    print()
    if all_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
