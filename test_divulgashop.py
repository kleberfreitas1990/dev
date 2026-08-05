"""Teste de sintaxe do módulo divulgashop.py"""
import sys
import ast

# Teste 1: Verificar sintaxe do divulgashop.py
print("=== Teste 1: Sintaxe divulgashop.py ===")
try:
    with open("modules/divulgashop.py", "r", encoding="utf-8") as f:
        source = f.read()
    ast.parse(source)
    print("✅ divulgashop.py - SINTAXE OK")
except SyntaxError as e:
    print(f"❌ divulgashop.py - ERRO DE SINTAXE: {e}")
    sys.exit(1)

# Teste 2: Verificar sintaxe do marketplace.app.py
print("\n=== Teste 2: Sintaxe marketplace.app.py ===")
try:
    with open("marketplace.app.py", "r", encoding="utf-8") as f:
        source = f.read()
    ast.parse(source)
    print("✅ marketplace.app.py - SINTAXE OK")
except SyntaxError as e:
    print(f"❌ marketplace.app.py - ERRO DE SINTAXE: {e}")
    sys.exit(1)

# Teste 3: Verificar que o import existe
print("\n=== Teste 3: Import do módulo ===")
if "from modules.divulgashop import render_divulga_shop" in source:
    print("✅ Import render_divulga_shop encontrado")
else:
    print("❌ Import render_divulga_shop NÃO encontrado")
    sys.exit(1)

# Teste 4: Verificar que a tab existe
print("\n=== Teste 4: Tab Divulga Shop ===")
if "tab_divulga" in source and "\"🛒 Divulga Shop\"" in source:
    print("✅ Tab '🛒 Divulga Shop' encontrada")
else:
    print("❌ Tab '🛒 Divulga Shop' NÃO encontrada")
    sys.exit(1)

# Teste 5: Verificar que o bloco with existe
print("\n=== Teste 5: Bloco with tab_divulga ===")
if "with tab_divulga:" in source:
    print("✅ Bloco 'with tab_divulga:' encontrado")
else:
    print("❌ Bloco 'with tab_divulga:' NÃO encontrado")
    sys.exit(1)

# Teste 6: Verificar que render_divulga_shop é chamado
print("\n=== Teste 6: Chamada render_divulga_shop ===")
if "render_divulga_shop()" in source:
    print("✅ Chamada render_divulga_shop() encontrada")
else:
    print("❌ Chamada render_divulga_shop() NÃO encontrada")
    sys.exit(1)

# Teste 7: Verificar que __all__ está no divulgashop
print("\n=== Teste 7: __all__ no divulgashop ===")
with open("modules/divulgashop.py", "r", encoding="utf-8") as f:
    divulgashop_source = f.read()
if '"render_divulga_shop"' in divulgashop_source:
    print("✅ render_divulga_shop no __all__")
else:
    print("❌ render_divulga_shop NÃO no __all__")
    sys.exit(1)

print("\n" + "=" * 50)
print("🎉 TODOS OS TESTES DE SINTAXE PASSARAM!")
print("=" * 50)
