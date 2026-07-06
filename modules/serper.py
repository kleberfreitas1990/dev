import streamlit as st
import requests
import json
import os
from datetime import datetime

ARQUIVO_SERPER_CACHE = "serper_cache.json"

def buscar_produtos_serper(termo, limite=5):
    """Busca produtos no Google Shopping via Serper.dev"""
    
    api_key = st.secrets.get("SERPER_API_KEY", "")
    if not api_key:
        return []
    
    try:
        url = "https://google.serper.dev/shopping"
        payload = {"q": termo, "gl": "br", "hl": "pt"}
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            produtos = []
            for item in data.get("shopping", [])[:limite]:
                produtos.append({
                    "nome": item.get("title", ""),
                    "preco": item.get("price", "R$ 0"),
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "avaliacao": item.get("rating", None)
                })
            return produtos
        return []
    except Exception as e:
        return []

def buscar_total_resultados_serper(termo):
    """Busca total de resultados para um termo"""
    produtos = buscar_produtos_serper(termo, 10)
    return len(produtos) * 10

__all__ = ['buscar_produtos_serper', 'buscar_total_resultados_serper']
