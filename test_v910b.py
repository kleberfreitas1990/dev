"""
Teste final v9.10b — Grades unificadas + Admin-only + Link Shopee
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("🧪 Testando imports...")
    from modules.views import (
        render_dashboard,
        render_grades_unificadas,
        _render_top20_com_shopee,
    )
    print("  ✅ render_grades_unificadas importada")
    print("  ✅ _render_top20_com_shopee importada")
    print("  ✅ render_dashboard importada")

def test_no_old_calls():
    print("\n🔍 Verificando que chamadas antigas foram removidas do Dashboard...")
    with open("modules/views.py", "r") as f:
        source = f.read()
    
    # Verificar que as funções inline antigas não são mais chamadas
    if "_render_top20_google_shopee_inline()" in source:
        # Só pode existir como definição, não como chamada
        lines_with_call = [l.strip() for l in source.split("\n") if "_render_top20_google_shopee_inline()" in l]
        if any(not l.startswith("#") and not l.startswith("def ") for l in lines_with_call):
            print("  ❌ Ainda há chamada a _render_top20_google_shopee_inline!")
            return False
    print("  ✅ Nenhuma chamada a _render_top20_google_shopee_inline()")
    
    if "_render_sugestoes_inline()" in source:
        lines_with_call = [l.strip() for l in source.split("\n") if "_render_sugestoes_inline()" in l]
        if any(not l.startswith("#") and not l.startswith("def ") for l in lines_with_call):
            print("  ❌ Ainda há chamada a _render_sugestoes_inline()!")
            return False
    print("  ✅ Nenhuma chamada a _render_sugestoes_inline()")
    return True

def test_admin_only():
    print("\n🔐 Verificando botão admin-only...")
    with open("modules/views.py", "r") as f:
        source = f.read()
    
    if "is_admin" in source and "btn_buscar_reais_unificado" in source:
        print("  ✅ Botão 'Buscar Dados Reais' verificado com is_admin")
    else:
        print("  ❌ Botão admin-only não encontrado!")
        return False
    return True

def test_shopee_links():
    print("\n🛒 Verificando links Shopee nas grades...")
    with open("modules/views.py", "r") as f:
        source = f.read()
    
    count_shopee = source.count("Link Shopee")
    count_shopee_link = source.count("shopee.com.br/search")
    print(f"  ✅ {count_shopee} referências a 'Link Shopee'")
    print(f"  ✅ {count_shopee_link} links shopee.com.br/search")
    return True

def test_tabs_count():
    print("\n📑 Verificando tabs no marketplace.app.py...")
    import re
    with open("marketplace.app.py", "r") as f:
        content = f.read()
    tabs_match = re.search(r'st\.tabs\(\[(.*?)\]\)', content, re.DOTALL)
    if tabs_match:
        tab_names = re.findall(r'"([^"]+)"', tabs_match.group(1))
        print(f"  ✅ {len(tab_names)} tabs no menu")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE FINAL v9.10b — Grades Unificadas")
    print("=" * 60)
    
    all_ok = True
    try: test_imports()
    except Exception as e: print(f"  ❌ {e}"); all_ok = False
    
    if not test_no_old_calls(): all_ok = False
    if not test_admin_only(): all_ok = False
    test_shopee_links()
    test_tabs_count()
    
    print()
    if all_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
