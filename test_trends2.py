#!/usr/bin/env python3
"""Testar extração das trending searches reais do Google Trends BR."""
import requests
from bs4 import BeautifulSoup
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}

# Abordagem: extrair dados da página do Google Trends usando regex nos scripts
print("=== GOOGLE TRENDS - EXTRACAO DE TRENDING SEARCHES ===")
url = 'https://trends.google.com/trends/trendingsearches/daily?geo=BR'
r = requests.get(url, timeout=30, headers=headers)

# O Google Trends injeta dados em script tags como JSON
# Procurar padrões de trending search queries
# Padrão 1: dados em window.__INITIAL_STATE__ ou similar
scripts = BeautifulSoup(r.text, 'html.parser').find_all('script')
print(f"Scripts encontrados: {len(scripts)}")

trending_queries = []

for script in scripts:
    text = script.string or ''
    
    # Padrão: "query":"texto" ou "query":"Texto"
    query_pattern = r'"query"\s*:\s*"([^"]{2,80})"'
    queries = re.findall(query_pattern, text)
    for q in queries:
        if q not in trending_queries and len(q) > 2:
            trending_queries.append(q)
    
    # Padrão alternativo: "title":"texto"
    title_pattern = r'"title"\s*:\s*"([^"]{2,80})"'
    titles = re.findall(title_pattern, text)
    for t in titles:
        if t not in trending_queries and len(t) > 2:
            trending_queries.append(t)

print(f"\nTrending queries encontradas: {len(trending_queries)}")
for i, q in enumerate(trending_queries[:30], 1):
    print(f"  {i}. {q}")

# Abordagem 2: Google News Trending Topics
print("\n\n=== GOOGLE NEWS - TOPICOS EM DESTAQUE ===")
url_news = 'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=pt-BR&gl=BR&ceid=BR:pt-150'
try:
    r_news = requests.get(url_news, timeout=15, headers=headers)
    print(f"Status: {r_news.status_code}")
    soup = BeautifulSoup(r_news.text, 'lxml-xml')
    items = soup.find_all('item')
    print(f"Itens encontrados: {len(items)}")
    for item in items[:10]:
        title = item.find('title')
        if title:
            print(f"  - {title.text}")
except Exception as e:
    print(f"Erro: {e}")

# Abordagem 3: Google News RSS geral
print("\n\n=== GOOGLE NEWS RSS ===")
url_rss = 'https://news.google.com/rss/search?q=site:shopee.com.br&hl=pt-BR&gl=BR&ceid=BR:pt-150'
try:
    r_rss = requests.get(url_rss, timeout=15, headers=headers)
    print(f"Status: {r_rss.status_code}")
    soup_rss = BeautifulSoup(r_rss.text, 'lxml-xml')
    items = soup_rss.find_all('item')
    print(f"Itens encontrados: {len(items)}")
    for item in items[:5]:
        title = item.find('title')
        if title:
            print(f"  - {title.text}")
except Exception as e:
    print(f"Erro: {e}")
