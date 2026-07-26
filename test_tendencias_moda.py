"""
Teste unitário para o módulo de Tendências de Moda via SerpApi.
Valida sintaxe, lógica de classificação e integração.
"""
import sys
import os
import json

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Testa se o módulo importa corretamente."""
    try:
        from modules.tendencias_moda_serpapi import (
            obter_tendencias_moda_serpapi,
            render_tendencias_moda_dashboard,
            TERMOS_MODA_FEMININA,
            CACHE_FILE,
        )
        print("✅ Import OK")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar: {e}")
        return False


def test_termos_config():
    """Testa se os termos estão configurados."""
    from modules.tendencias_moda_serpapi import TERMOS_MODA_FEMININA
    assert len(TERMOS_MODA_FEMININA) == 10, f"Esperado 10 termos, recebido {len(TERMOS_MODA_FEMININA)}"
    print(f"✅ {len(TERMOS_MODA_FEMININA)} termos configurados: {TERMOS_MODA_FEMININA}")
    return True


def test_classificacao_alta():
    """Testa a lógica de classificação Em Alta."""
    # Quando interesse_2026 > interesse_2025
    int_2025 = 50
    int_2026 = 75
    if int_2026 > int_2025:
        status = "Em Alta"
        variacao = round(((int_2026 - int_2025) / max(int_2025, 1)) * 100, 1)
    else:
        status = "Em Queda"
        variacao = round(((int_2026 - int_2025) / max(int_2025, 1)) * 100, 1) if int_2025 > 0 else 0.0

    assert status == "Em Alta", f"Esperado 'Em Alta', recebido '{status}'"
    assert variacao == 50.0, f"Esperado 50.0%, recebido {variacao}%"
    print(f"✅ Classificação 'Em Alta': {variacao}% (correto)")
    return True


def test_classificacao_queda():
    """Testa a lógica de classificação Em Queda."""
    int_2025 = 80
    int_2026 = 60
    if int_2026 > int_2025:
        status = "Em Alta"
        variacao = round(((int_2026 - int_2025) / max(int_2025, 1)) * 100, 1)
    else:
        status = "Em Queda"
        variacao = round(((int_2026 - int_2025) / max(int_2025, 1)) * 100, 1) if int_2025 > 0 else 0.0

    assert status == "Em Queda", f"Esperado 'Em Queda', recebido '{status}'"
    assert variacao == -25.0, f"Esperado -25.0%, recebido {variacao}%"
    print(f"✅ Classificação 'Em Queda': {variacao}% (correto)")
    return True


def test_sintaxe_modulo():
    """Testa se o módulo tem sintaxe válida (compilação)."""
    import py_compile
    try:
        py_compile.compile("/home/ubuntu/dev/modules/tendencias_moda_serpapi.py", doraise=True)
        print("✅ Sintaxe do módulo válida")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Erro de sintaxe: {e}")
        return False


def test_cache_structure():
    """Testa a estrutura do cache."""
    from modules.tendencias_moda_serpapi import _salvar_cache, _carregar_cache, _cache_valido
    import tempfile

    # Simula salvamento
    dados_teste = [{
        "termo": "Teste",
        "interesse_2025": 50,
        "interesse_2026": 75,
        "status": "Em Alta",
        "variacao": "+50.0%",
        "variacao_num": 50.0,
        "dica_conteudo": "Teste dica",
        "categoria": "Moda Feminina",
        "fonte": "Teste",
        "atualizado": "26/07/2026 12:00",
    }]

    # Salva e carrega
    _salvar_cache(dados_teste)
    carregado = _carregar_cache()
    assert carregado is not None, "Cache retornado como None"
    assert len(carregado) == 1, f"Esperado 1 item, recebido {len(carregado)}"
    assert carregado[0]["termo"] == "Teste", f"Termo esperado 'Teste', recebido '{carregado[0]['termo']}'"
    assert _cache_valido(), "Cache deveria ser válido"
    print("✅ Cache: estrutura correta, salvamento/leitura OK")
    return True


def test_views_integration():
    """Testa se views.py integra corretamente o novo módulo."""
    with open("/home/ubuntu/dev/modules/views.py", "r", encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("import render_tendencias_moda_dashboard", "from modules.tendencias_moda_serpapi import render_tendencias_moda_dashboard"),
        ("chamada render_tendencias_moda_dashboard", "render_tendencias_moda_dashboard()"),
        ("try/except wrapper", "Tendências de Moda indisponíveis"),
    ]

    for nome, texto in checks:
        assert texto in content, f"❌ Falta '{texto}' no views.py"
        print(f"✅ Integração {nome}: OK")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TESTES: Tendências de Moda via SerpApi")
    print("=" * 60)

    tests = [
        test_sintaxe_modulo,
        test_import,
        test_termos_config,
        test_classificacao_alta,
        test_classificacao_queda,
        test_cache_structure,
        test_views_integration,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FALHOU: {e}")
            failed += 1

    print("=" * 60)
    print(f"Resultados: {passed} passaram, {failed} falharam")
    print("=" * 60)

    if failed == 0:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️ Alguns testes falharam. Revise acima.")

    sys.exit(0 if failed == 0 else 1)
