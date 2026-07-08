import json
import os
import sys

# Mock streamlit para evitar erro de importação
sys.modules['streamlit'] = type('MockStreamlit', (), {'secrets': {}, 'session_state': {}})

from modules.models import gerar_top10_produtos

def validar():
    print("--- VALIDANDO TOP 10 PRODUTOS ---")
    
    from modules.produtos_dinamicos import carregar_cache_produtos
    cache = carregar_cache_produtos()
    print(f"DEBUG: Cache carregado tem {len(cache.get('produtos', {}))} produtos.")
    if cache.get('produtos'):
        print(f"DEBUG: Primeiro produto no cache: {list(cache['produtos'].keys())[0]}")
    
    # Não forçamos atualização para ler do cache que acabamos de injetar
    top10 = gerar_top10_produtos(forcar_atualizacao=False)
    
    if not top10:
        print("❌ Nenhum produto retornado!")
        return

    print(f"✅ Retornados {len(top10)} produtos.")
    for i, p in enumerate(top10):
        print(f"{i+1}. {p['Produto']} - Score: {p['Score']} - Categoria: {p['Categoria']}")
    
    primeiro = top10[0]['Produto'].lower()
    if "air fryer" in primeiro or "motorola" in primeiro:
        print("\n✨ SUCESSO: Dados reais injetados estão aparecendo no topo!")
    else:
        print("\n⚠️ AVISO: O topo ainda não reflete os dados injetados.")

if __name__ == "__main__":
    validar()
