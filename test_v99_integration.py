
import os
import json
import sys

def test_integration():
    print("--- 🔍 Teste de Integração v9.9 ---")
    
    # 1. Verificar Cache Shopee
    print("\n1. Verificando Cache Shopee...")
    if os.path.exists("shopee_trends.json"):
        with open("shopee_trends.json", "r", encoding="utf-8") as f:
            cache = json.load(f)
            termos = cache.get("data", [])
            print(f"✅ Cache Shopee contém {len(termos)} termos.")
            if "Tênis Masculino" in termos:
                print("✅ Novo termo 'Tênis Masculino' encontrado no cache.")
    else:
        print("❌ Cache Shopee não encontrado.")

    # 2. Verificar Integração Pedreira no app principal
    print("\n2. Verificando Integração no marketplace.app.py...")
    if os.path.exists("marketplace.app.py"):
        with open("marketplace.app.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "🏗️ Pedreira" in content and "render_pedreira()" in content:
                print("✅ Aba 'Pedreira' integrada com sucesso.")
            else:
                print("❌ Aba 'Pedreira' não encontrada no marketplace.app.py.")
    else:
        print("❌ marketplace.app.py não encontrado.")

    # 3. Verificar Módulo Pedreira
    print("\n3. Verificando Módulo modules/pedreira.py...")
    if os.path.exists("modules/pedreira.py"):
        print("✅ Módulo modules/pedreira.py criado.")
    else:
        print("❌ Módulo modules/pedreira.py não encontrado.")

if __name__ == "__main__":
    test_integration()
