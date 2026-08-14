#!/usr/bin/env python3
"""
test_shopee_daily_trends.py — Teste do módulo de coleta diária
"""

import logging
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import modules.shopee_daily_trends as daily_trends

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importar módulos
from modules.adult_content_filter import (
    filtrar_lista_termos,
    obter_estatisticas_filtro,
    eh_termo_adulto
)
from modules.shopee_daily_trends import (
    normalizar_termos,
    _inicializar_banco,
    persistir_tendencias_sqlite,
    obter_termos_do_dia,
    obter_resumo_diario,
    obter_termos_permanentes,
    _salvar_cache_diario,
    _carregar_cache_diario
)

def teste_filtro_adulto():
    """Testa o filtro de conteúdo adulto."""
    print("\n" + "="*60)
    print("TESTE 1: Filtro de Conteúdo Adulto")
    print("="*60)
    
    termos_teste = [
        "Consolo",
        "Moto Elétrica Scooter",
        "Boneco Sexual",
        "Brinquedo Sexual Masculino",
        "iPhone",
        "Vibrador",
        "PS5",
        "Bloqueador de Sinal Bluetooth",
        "Papel de Parede",
        "Cumeeira PVC",
    ]
    
    print(f"\nTermos originais ({len(termos_teste)}):")
    for termo in termos_teste:
        bloqueado = eh_termo_adulto(termo)
        status = "🚫 BLOQUEADO" if bloqueado else "✅ OK"
        print(f"  - {termo}: {status}")
    
    # Filtrar
    termos_filtrados = filtrar_lista_termos(termos_teste)
    stats = obter_estatisticas_filtro(termos_teste)
    
    print(f"\nResultado após filtro:")
    print(f"  Total original: {stats['total_original']}")
    print(f"  Total filtrado: {stats['total_filtrado']}")
    print(f"  Total bloqueado: {stats['total_bloqueado']}")
    print(f"  Taxa de bloqueio: {stats['taxa_bloqueio']}%")
    print(f"  Termos bloqueados: {stats['termos_bloqueados']}")
    
    assert "Brinquedo Sexual Masculino" in stats["termos_bloqueados"]
    assert "Brinquedo Sexual Masculino" not in termos_filtrados
    return len(stats['termos_bloqueados']) > 0


def teste_normalizacao():
    """Testa a normalização de termos."""
    print("\n" + "="*60)
    print("TESTE 2: Normalização de Termos")
    print("="*60)
    
    termos_teste = [
        "  iPhone  ",
        "iphone",
        "IPHONE",
        "PS5",
        "ps5",
        "Moto Elétrica Scooter",
        "Moto Elétrica Scooter",  # Duplicado
        "  Sofá  ",
    ]
    
    print(f"\nTermos antes da normalização ({len(termos_teste)}):")
    for termo in termos_teste:
        print(f"  - '{termo}'")
    
    termos_normalizados = normalizar_termos(termos_teste)
    
    print(f"\nTermos após normalização ({len(termos_normalizados)}):")
    for termo in termos_normalizados:
        print(f"  - {termo}")
    
    return len(termos_normalizados) < len(termos_teste)


def teste_persistencia():
    """Testa a persistência em SQLite em banco temporário isolado."""
    print("\n" + "="*60)
    print("TESTE 3: Persistência SQLite isolada")
    print("="*60)

    hoje = datetime.now().strftime("%Y-%m-%d")
    termos_teste = [
        "iPhone",
        "PS5",
        "Moto Elétrica Scooter",
        "Sofá",
        "Tablet Lenovo M10",
    ]

    caminho_original = daily_trends.DB_PATH
    with tempfile.TemporaryDirectory() as diretorio:
        daily_trends.DB_PATH = Path(diretorio) / "teste_trends.db"
        try:
            _inicializar_banco()
            print(f"\nPersistindo {len(termos_teste)} termos para {hoje}...")
            persistir_tendencias_sqlite(hoje, termos_teste, "teste", 2)
            termos_recuperados = obter_termos_do_dia(hoje)
            resumo = obter_resumo_diario(hoje)
        finally:
            daily_trends.DB_PATH = caminho_original

    print(f"\nTermos recuperados ({len(termos_recuperados)}):")
    for termo in termos_recuperados:
        print(f"  - {termo}")

    print("\nResumo do dia:")
    if resumo:
        print(f"  Data: {resumo.get('data_coleta')}")
        print(f"  Total: {resumo.get('total_termos')}")
        print(f"  Bloqueados: {resumo.get('termos_filtrados')}")
        print(f"  Fonte: {resumo.get('fonte_primaria')}")

    return len(termos_recuperados) == len(termos_teste)


def teste_cache():
    """Testa o cache diário em arquivo temporário isolado."""
    print("\n" + "="*60)
    print("TESTE 4: Cache Diário isolado (JSON)")
    print("="*60)

    hoje = datetime.now().strftime("%Y-%m-%d")
    termos_teste = ["iPhone", "PS5", "Sofá"]
    caminho_original = daily_trends.CACHE_DIARIO
    with tempfile.TemporaryDirectory() as diretorio:
        daily_trends.CACHE_DIARIO = Path(diretorio) / "cache_teste.json"
        try:
            print(f"\nSalvando cache para {hoje}...")
            _salvar_cache_diario(hoje, termos_teste, "teste", 0)
            print("Carregando cache...")
            cache = _carregar_cache_diario()
        finally:
            daily_trends.CACHE_DIARIO = caminho_original

    if cache:
        print("\nCache carregado:")
        print(f"  Data: {cache.get('data_coleta')}")
        print(f"  Total: {cache.get('total')}")
        print(f"  Fonte: {cache.get('fonte')}")
        print(f"  Termos: {cache.get('termos')}")
        return True

    print("❌ Falha ao carregar cache")
    return False


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("TESTES: Módulo Shopee Daily Trends")
    print("="*60)
    
    resultados = {
        "Filtro Adulto": teste_filtro_adulto(),
        "Normalização": teste_normalizacao(),
        "Persistência SQLite": teste_persistencia(),
        "Cache JSON": teste_cache(),
    }
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    for nome, resultado in resultados.items():
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"  {nome}: {status}")
    
    total_passou = sum(1 for r in resultados.values() if r)
    total = len(resultados)
    
    print(f"\nTotal: {total_passou}/{total} testes passaram")
    
    return 0 if total_passou == total else 1


if __name__ == "__main__":
    sys.exit(main())
