# test_produtos.py
import sys
sys.path.append('.')

from modules.models import gerar_top10_produtos, gerar_sugestoes_diarias
from modules.produtos_dinamicos import limpar_cache_produtos

print("=== TESTE DE PRODUTOS DINÂMICOS ===\n")

# Limpa cache para forçar atualização
print("1. Limpando cache...")
limpar_cache_produtos()

# Gera produtos
print("\n2. Buscando produtos...")
produtos = gerar_top10_produtos(forcar_atualizacao=True)

print(f"\n3. Encontrados {len(produtos)} produtos:\n")

for i, produto in enumerate(produtos, 1):
    print(f"{i}. {produto['Produto']}")
    print(f"   Score: {produto['Score']}/10")
    print(f"   Categoria: {produto['Categoria']}")
    print(f"   Tendência: {produto['Tendência']}")
    print(f"   Buscas no Mês: {produto['Buscas no Mês']}")
    print()

print("4. Sugestões diárias:")
sugestoes = gerar_sugestoes_diarias()
for s in sugestoes:
    print(f"   - {s['Produto']} (Score: {s['Score']})")
