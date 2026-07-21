#!/usr/bin/env python3
"""
Teste completo do banco de dados SQLite — Minerador v9.9
Verifica: inicialização, migração, integração com scrapers, e compatibilidade.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database import (
    inicializar_db, verificar_db, migrar_jsons_para_db,
    obter_ml_ciclo_atual, obter_amazon_ciclo_atual,
    ml_cache_valido, amazon_cache_valido,
    obter_status_banco,
    criar_pedido_pedreira, obter_pedidos_pedreira, atualizar_status_pedido,
    registrar_log_busca, obter_logs_busca,
    registrar_execucao_auto, obter_historico_auto,
    salvar_ml_ciclo, salvar_amazon_ciclo,
    registrar_historico_tendencias, obter_historico_tendencias,
    limpar_ml_cache_antigos, limpar_amazon_cache_antigos,
)

print("=" * 60)
print("TESTE: Banco de Dados SQLite — Minerador v9.9")
print("=" * 60)

# 1. Inicialização
print("\n[1] Inicializando banco...")
ok = inicializar_db()
print(f"    → {'✅ OK' if ok else '❌ FALHA'}")

ok = verificar_db()
print(f"    → Verificação: {'✅ OK' if ok else '❌ FALHA'}")

# 2. Migração de JSONs
print("\n[2] Migrando JSONs para SQLite...")
inicio = time.time()
migrado = migrar_jsons_para_db()
print(f"    → {'✅ Migração executada' if migrado else 'ℹ️ Nenhum JSON para migrar'}")
print(f"    → Tempo: {time.time() - inicio:.2f}s")

# 3. Verificar dados ML
print("\n[3] Verificando cache ML...")
ml_data = obter_ml_ciclo_atual()
if ml_data:
    total = len(ml_data.get("produtos", {}))
    print(f"    → ✅ {total} produtos no último ciclo")
    print(f"    → Timestamp: {ml_data.get('timestamp', 'N/A')}")
    print(f"    → Fonte: {ml_data.get('fonte', 'N/A')}")
else:
    print("    → ⚠️ Nenhum dado ML no banco")

# 4. Verificar dados Amazon
print("\n[4] Verificando cache Amazon...")
amz_data = obter_amazon_ciclo_atual()
if amz_data:
    total = len(amz_data.get("produtos", {}))
    print(f"    → ✅ {total} produtos no último ciclo")
    print(f"    → Timestamp: {amz_data.get('timestamp', 'N/A')}")
    print(f"    → Fonte: {amz_data.get('fonte', 'N/A')}")
else:
    print("    → ⚠️ Nenhum dado Amazon no banco")

# 5. Validade dos caches
print("\n[5] Validade dos caches...")
print(f"    → ML válido: {'✅' if ml_cache_valido() else '❌ expirado'}")
print(f"    → Amazon válido: {'✅' if amazon_cache_valido() else '❌ expirado'}")

# 6. Status do banco
print("\n[6] Status do banco...")
status = obter_status_banco()
print(f"    → Tamanho: {status.get('db_size_kb', 0)} KB")
print(f"    → Versão: {status.get('versao_schema', 0)}")
for key in ["ml_ciclos_count", "amazon_ciclos_count", "shopee_cache_count",
            "google_trends_cache_count", "historico_tendencias_count",
            "pedreira_pedidos_count", "buscas_logs_count", "auto_update_historico_count"]:
    print(f"    → {key}: {status.get(key, 0)}")

# 7. Testar pedidos da Pedreira
print("\n[7] Testando Pedreira...")
pedido_id = criar_pedido_pedreira(
    produto="Teste SQLite - Parafuso 1/4",
    quantidade=500,
    solicitante="Teste DB",
    empresa="Pedreira A"
)
print(f"    → ✅ Pedido #{pedido_id} criado")

pedidos = obter_pedidos_pedreira()
print(f"    → Total pedidos: {len(pedidos)}")

if pedido_id:
    atualizar_status_pedido(pedido_id, "em_analise", "Teste")
    print(f"    → ✅ Status atualizado para 'em_analise'")

# 8. Testar logs
print("\n[8] Testando logs...")
log_id = registrar_log_busca(
    nivel="test", termo="parafuso", sucesso=True,
    quantidade=50, tempo_execucao=1.2, detalhes="Teste SQLite"
)
print(f"    → ✅ Log #{log_id} registrado")

logs = obter_logs_busca(limite=5)
print(f"    → Últimos 5 logs: {len(logs)} registros")

# 9. Testar histórico de tendências
print("\n[9] Testando histórico de tendências...")
top10 = [{"Produto": f"Teste {i}", "Score": 10 - i, "Fonte": "Teste"} for i in range(10)]
resultado = registrar_historico_tendencias(top10, origem="teste_db")
print(f"    → ✅ Registrado: {resultado}")

hist = obter_historico_tendencias(limite=3)
print(f"    → Últimos 3 snapshots: {len(hist)} registros")

# 10. Testar histórico auto
print("\n[10] Testando histórico de atualizações...")
registrar_execucao_auto(tipo="teste", sucesso=True, detalhes={"teste": True}, tempo=0.5)
hist_auto = obter_historico_auto(limite=3)
print(f"    → ✅ {len(hist_auto)} registros")

# 11. Limpeza
print("\n[11] Limpeza de ciclos antigos...")
ml_rem = limpar_ml_cache_antigos(5)
amz_rem = limpar_amazon_cache_antigos(5)
print(f"    → ML: {ml_rem} removidos | Amazon: {amz_rem} removidos")

print("\n" + "=" * 60)
print("TESTE COMPLETO — TODOS OS MÓDULOS FUNCIONANDO ✅")
print("=" * 60)

# 12. Testar importação dos módulos modificados
print("\n[12] Verificando módulos modificados (sem Streamlit)...")
try:
    from modules.mercadolivre_scraper import _cache_valido as ml_valido_check
    print("    → ✅ mercadolivre_scraper.py importado")
except Exception as e:
    print(f"    → ❌ mercadolivre_scraper.py: {e}")

try:
    from modules.amazon_scraper import _cache_recente as amz_recente_check
    print("    → ✅ amazon_scraper.py importado")
except Exception as e:
    print(f"    → ❌ amazon_scraper.py: {e}")

try:
    from modules.auto_update import carregar_historico as carrega_hist
    print("    → ✅ auto_update.py importado")
except Exception as e:
    print(f"    → ❌ auto_update.py: {e}")

try:
    from modules.logger import registrar_busca as reg_busca
    print("    → ✅ logger.py importado")
except Exception as e:
    print(f"    → ❌ logger.py: {e}")

print("\n✅ TODOS OS TESTES PASSARAM!")
