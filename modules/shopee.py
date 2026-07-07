import streamlit as st
import requests
import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# ARQUIVO DE CACHE
# ============================================================
ARQUIVO_SHOPEE_CACHE = "shopee_trends_cache.json"

# ============================================================
# TERMOS REAIS DA SHOPEE (FALLBACK)
# ============================================================
TERMOS_REAIS_SHOPEE = [
    "controle pc", "sapateira", "lixeira cozinha", 
    "ar condicionado portátil", "garrafa térmica", 
    "sacola personalizada", "caixa organizadora", 
    "camisa brasil", "tênis", "chopeira", 
    "relógio", "tablet", "organizador", "lingerie", 
    "espelho", "vestido", "roupas feminina", 
    "figurinha legend", "joia cobre", 
    "kenner feminina", "moto infantil", "kit cadeira",
    "ar condicionado elgin", "kit loreal"
]

# ============================================================
# FUNÇÃO PARA CAPTURAR BUSCAS DA SHOPEE
# ============================================================
def capturar_buscas_shopee():
    """Captura buscas em alta da Shopee com múltiplas estratégias"""
    
    # 1. Tenta capturar do rodapé
    try:
        url = "https://shopee.com.br"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        termos = []
        
        # Busca em links com keyword
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if '/search?keyword=' in href:
                match = re.search(r'keyword=([^&]+)', href)
                if match:
                    termo = requests.utils.unquote(match.group(1))
                    if termo and len(termo) > 2 and termo not in termos:
                        termos.append(termo)
        
        if termos:
            return termos[:20]
    except:
        pass
    
    # 2. Tenta via API de sugestões
    try:
        url = "https://shopee.com.br/api/v4/search/search_suggestions"
        params = {"search": ""}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://shopee.com.br/"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            termos = []
            
            if "items" in data:
                for item in data["items"]:
                    termo = item.get("keyword", "")
                    if termo and len(termo) > 2:
                        termos.append(termo)
            
            if termos:
                return termos[:20]
    except:
        pass
    
    # 3. FALLBACK: Usa termos reais do rodapé
    return TERMOS_REAIS_SHOPEE

def capturar_buscas_shopee_com_cache():
    """Captura buscas com cache diário"""
    
    hoje = datetime.now().date().isoformat()
    
    # Tenta carregar do cache
    if os.path.exists(ARQUIVO_SHOPEE_CACHE):
        try:
            with open(ARQUIVO_SHOPEE_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if dados.get("data") == hoje:
                    return dados.get("termos", [])
        except:
            pass
    
    # Se não tem cache, busca novos dados
    termos = capturar_buscas_shopee()
    
    # Salva no cache
    try:
        with open(ARQUIVO_SHOPEE_CACHE, 'w', encoding='utf-8') as f:
            json.dump({
                "data": hoje,
                "termos": termos,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except:
        pass
    
    return termos

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'capturar_buscas_shopee',
    'capturar_buscas_shopee_com_cache',
    'TERMOS_REAIS_SHOPEE'
]
