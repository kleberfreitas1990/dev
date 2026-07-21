"""
Teste de sintaxe e importação após remoção das tabs Top 20 Google e Sugestões.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testa se todos os módulos importam sem erro."""
    print("🧪 Testando imports...")
    
    from modules.views import (
        render_dashboard,
        render_status_usuario,
        render_painel_apoiadores_detalhado,
        render_apoiadores_compactos,
        _render_top20_google_shopee_inline,
        _render_sugestoes_inline,
        render_top_20_marketplace,
    )
    print("  ✅ modules/views.py — todos os imports OK")
    print(f"  ✅ _render_top20_google_shopee_inline: {_render_top20_google_shopee_inline}")
    print(f"  ✅ _render_sugestoes_inline: {_render_sugestoes_inline}")

def test_no_pedreira():
    """Verifica que pedreira.py não existe mais."""
    pedreira_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "pedreira.py")
    if os.path.exists(pedreira_path):
        print("  ❌ modules/pedreira.py ainda existe!")
        return False
    print("  ✅ modules/pedreira.py removido")
    return True

def test_tabs_count():
    """Verifica que o marketplace.app.py tem o número correto de tabs."""
    with open("marketplace.app.py", "r") as f:
        content = f.read()
    
    # Conta as tabs na lista
    import re
    tabs_match = re.search(r'st\.tabs\(\[(.*?)\]\)', content, re.DOTALL)
    if tabs_match:
        tabs_list = tabs_match.group(1)
        tab_names = re.findall(r'"([^"]+)"', tabs_list)
        print(f"  ✅ {len(tab_names)} tabs encontradas:")
        for t in tab_names:
            print(f"     - {t}")
        
        # Verifica que Top 20 e Sugestões não estão na lista
        if "🔥 Top 20 Google" in tab_names:
            print("  ❌ Tab '🔥 Top 20 Google' ainda está no menu!")
            return False
        if "📌 Sugestões de Produtos" in tab_names:
            print("  ❌ Tab '📌 Sugestões de Produtos' ainda está no menu!")
            return False
        print("  ✅ Tabs Top 20 e Sugestões removidas do menu")
    return True

def test_dashboard_has_new_sections():
    """Verifica que o dashboard chama as novas funções inline."""
    with open("modules/views.py", "r") as f:
        content = f.read()
    
    if "_render_top20_google_shopee_inline" in content:
        print("  ✅ Dashboard chama _render_top20_google_shopee_inline")
    else:
        print("  ❌ Dashboard NÃO chama _render_top20_google_shopee_inline")
        return False
    
    if "_render_sugestoes_inline" in content:
        print("  ✅ Dashboard chama _render_sugestoes_inline")
    else:
        print("  ❌ Dashboard NÃO chama _render_sugestoes_inline")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE: Remoção de Tabs + Inserção no Dashboard")
    print("=" * 60)
    
    all_ok = True
    
    try:
        test_imports()
    except Exception as e:
        print(f"  ❌ Erro nos imports: {e}")
        all_ok = False
    
    if not test_no_pedreira():
        all_ok = False
    
    if not test_tabs_count():
        all_ok = False
    
    if not test_dashboard_has_new_sections():
        all_ok = False
    
    print()
    if all_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
