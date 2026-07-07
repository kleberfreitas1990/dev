# test_validation.py
import sys
sys.path.append('.')

from modules.validation import *
from modules.shopee import capturar_buscas_shopee_com_cache, obter_stats_cache_shopee

# Teste 1: Validar termos
print("=== TESTE VALIDAÇÃO DE TERMOS ===")
termos_teste = [
    "  camisa  ", 
    "<script>alert('xss')</script>", 
    "a", 
    "smartwatch",
    "      ",
    "produto muito longo " * 10
]

for termo in termos_teste:
    resultado = validar_termo_busca(termo)
    print(f"'{termo[:30]}...' → '{resultado}'")

# Teste 2: Cache da Shopee
print("\n=== TESTE CACHE SHOPEE ===")
termos = capturar_buscas_shopee_com_cache()
print(f"Termos capturados: {len(termos)}")
print(f"Primeiros 5: {termos[:5]}")

stats = obter_stats_cache_shopee()
print(f"Stats: {stats}")

# Teste 3: Validar apoiador
print("\n=== TESTE VALIDAÇÃO APOIADOR ===")
apoiador_teste = {
    "nome": "João Teste",
    "email": "joao@teste.com",
    "ordem": 5,
    "plano": "Premium"
}
resultado = validar_apoiador(apoiador_teste)
print(f"Apoiador validado: {resultado}")
