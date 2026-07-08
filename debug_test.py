import sys
import os

# Adiciona o diretório atual ao path para importar os módulos
sys.path.append(os.getcwd())

try:
    from modules.models import gerar_top10_produtos
    from modules.grade_descoberta import descobrir_produtos_grade
    
    print("--- Testando gerar_top10_produtos ---")
    top10 = gerar_top10_produtos(forcar_atualizacao=True)
    print(f"Tipo retornado: {type(top10)}")
    if top10:
        print(f"Quantidade: {len(top10)}")
        print(f"Primeiro item: {top10[0]}")
    else:
        print("Top 10 retornou vazio!")
        
    print("\n--- Testando descobrir_produtos_grade ---")
    grade = descobrir_produtos_grade(quantidade=5)
    print(f"Tipo retornado: {type(grade)}")
    if grade:
        print(f"Quantidade: {len(grade)}")
        print(f"Primeiro item: {grade[0]}")
    else:
        print("Grade retornou vazia!")

except Exception as e:
    print(f"ERRO DURANTE O TESTE: {e}")
    import traceback
    traceback.print_exc()
