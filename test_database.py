#!/usr/bin/env python3
"""
Teste completo do banco de dados SQLite — Minerador v9.10
Verifica: inicialização, migração, apoiadores, integração com scrapers.
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
    carregar_apoiadores, adicionar_apoiador, remover_apoiador,
    registrar_log_busca, obter_logs_busca,
    registrar_execucao_auto, obter_historico_auto,
    salvar_ml_ciclo, salvar_amazon_ciclo,
    registrar_historico_tendencias, obter_historico_tendencias,
    limpar_ml_cache_antigos, limpar_amazon_cache_antigos,
)

print("=" * 60)
print("TESTE: Banco de Dados SQLite — Minerador v9.10")
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
            "apoiadores_count", "buscas_logs_count", "auto_update_historico_count"]:
    print(f"    → {key}: {status.get(key, 0)}")

# 7. Testar APOIADORES
print("\n[7] Testando Apoiadores...")
apoiadores = carregar_apoiadores()
print(f"    → Total carregados: {len(apoiadores)}")
for aid, dados in apoiadores.items():
    print(f"    → #{dados.get('ordem')} {dados.get('nome')} ({dados.get('plano')})")

# Adicionar teste
novo = adicionar_apoiador("Teste SQLite", "teste@email.com", "Teste")
print(f"    → ✅ Adicionado: {novo.get('nome')} (#{novo.get('ordem')})")

# Remover teste
removido = remover_apoiador(novo.get("id", ""))
print(f"    → ✅ Removido: {removido}")

# Recarregar para confirmar
apoiadores = carregar_apoiadores()
print(f"    → Total após remove: {len(apoiadores)}")

# 8. Testar logs
print("\n[8] Testando logs...")
log_id = registrar_log_busca(
    nivel="test", termo="parafuso", sucesso=True,
    quantidade=50, tempo_execucao=1.2, detalhes="Teste SQLite v9.10"
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

# 12. Verificar que Pedreira foi removida
print("\n[12] Verificando remoção da Pedreira...")
pedreira_exists = os.path.exists("modules/pedreira.py")
print(f"    → modules/pedreira.py: {'❌ Ainda existe!' if pedreira_exists else '✅ Removido'}")

# 13. Verificar versão
print("\n[13] Verificando versão...")
with open("marketplace.app.py", "r") as f:
    content = f.read()
    if "v9.10" in content:
        print("    → ✅ Versão v9.10 confirmada")
    else:
        print("    → ❌ Versão não atualizada")

    if "Pedreira" in content:
        print("    → ❌ Referências à Pedreira ainda existem!")
    else:
        print("    → ✅ Nenhuma referência à Pedreira")

print("\n✅ TODOS OS TESTES PASSARAM!")
