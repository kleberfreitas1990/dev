import requests
from bs4 import BeautifulSoup
import re
import os
import sys
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o diretório atual ao path para manipulação de arquivos
sys.path.append(os.getcwd())

def capturar_tendencias_ml():
    """Extrai os termos em alta do Mercado Livre Brasil."""
    url = "https://tendencias.mercadolivre.com.br/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            logger.error(f"Erro ao acessar ML: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Tenta capturar termos da lista de "Termos mais procurados"
        termos = []
        
        # Procura por links dentro de listas de tendências
        links_tendencia = soup.find_all('a', href=re.compile(r'lista.mercadolivre.com.br/'))
        
        for link in links_tendencia:
            texto = link.get_text().strip()
            # Filtra termos muito curtos ou que parecem ser apenas letras de navegação
            if texto and len(texto) > 2 and len(texto) < 50 and texto not in termos:
                # Evita capturar apenas letras do alfabeto de navegação
                if not (len(texto) == 1 and texto.isalpha()):
                    termos.append(texto)
        
        logger.info(f"Capturados {len(termos)} termos do Mercado Livre.")
        return termos[:40] # Retorna os top 40
    except Exception as e:
        logger.error(f"Falha no scraping: {str(e)}")
        return []

def atualizar_modulo_produtos(novos_termos):
    """Atualiza a lista TERMOS_ML no arquivo produtos_dinamicos.py."""
    if not novos_termos:
        logger.warning("Nenhum termo novo para atualizar.")
        return False
    
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_atual, "modules", "produtos_dinamicos.py")
    
    if not os.path.exists(caminho_arquivo):
        logger.error("Arquivo produtos_dinamicos.py não encontrado.")
        return False
    
    try:
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
        
        logger.info(f"Módulo atualizado com {len(novos_termos)} termos reais do ML.")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar módulo: {e}")
        return False

if __name__ == "__main__":
    logger.info("Iniciando captura de tendências reais do Mercado Livre...")
    termos = capturar_tendencias_ml()
    if termos:
        atualizar_modulo_produtos(termos)
    else:
        logger.error("Não foi possível obter novos termos.")
