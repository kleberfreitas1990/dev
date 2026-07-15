import requests
from bs4 import BeautifulSoup
import re
import os
import sys

# Adiciona o diretório atual ao path para manipulação de arquivos
sys.path.append(os.getcwd())

def capturar_tendencias_ml():
    """Extrai os termos em alta do Mercado Livre Brasil."""
    url = "https://tendencias.mercadolivre.com.br/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ Erro ao acessar ML: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Busca links que contenham termos de pesquisa
        links = soup.find_all('a', href=re.compile(r'lista.mercadolivre.com.br/'))
        
        termos = []
        for link in links:
            texto = link.get_text().strip()
            if texto and len(texto) > 2 and texto not in termos:
                termos.append(texto)
                if len(termos) >= 20: # Limite de 20 termos
                    break
        
        return termos
    except Exception as e:
        print(f"❌ Falha no scraping: {str(e)}")
        return []

def atualizar_modulo_produtos(novos_termos):
    """Atualiza a lista TERMOS_ML no arquivo produtos_dinamicos.py."""
    if not novos_termos:
        print("⚠️ Nenhum termo novo para atualizar.")
        return False
    
    # Usar caminho relativo baseado no local do script
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_atual, "modules", "produtos_dinamicos.py")
    if not os.path.exists(caminho_arquivo):
        print("❌ Arquivo produtos_dinamicos.py não encontrado.")
        return False
    
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()
    
    # Regex para encontrar a lista TERMOS_ML
    padrao = r"TERMOS_ML = \[(.*?)\]"
    nova_lista_str = "TERMOS_ML = [\n"
    for termo in novos_termos:
        nova_lista_str += f"    \"{termo}\",\n"
    nova_lista_str += "]"
    
    novo_conteudo = re.sub(padrao, nova_lista_str, conteudo, flags=re.DOTALL)
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)
    
    print(f"✅ Módulo atualizado com {len(novos_termos)} termos reais do ML.")
    return True

if __name__ == "__main__":
    print("🔍 Iniciando captura de tendências reais do Mercado Livre...")
    termos = capturar_tendencias_ml()
    if termos:
        atualizar_modulo_produtos(termos)
    else:
        print("❌ Não foi possível obter novos termos.")
