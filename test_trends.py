#!/usr/bin/env python3
"""Testar extração de dados reais de tendências."""
import requests
from bs4 import BeautifulSoup
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}

# 1. Google Trends - Tentar extrair dados da página
print("=== GOOGLE TRENDS BRASIL ===")
url = 'https://trends.google.com/trends/trendingsearches/daily?geo=BR'
r = requests.get(url, timeout=30, headers=headers)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

# Tentar encontrar dados JSON no HTML
# Google Trends usa dados em JavaScript
pattern = r'trends\s*=\s*(\{.*?\});'
matches = re.findall(pattern, r.text, re.DOTALL)
print(f"Matches JSON: {len(matches)}")

# Tentar encontrar trending topics na página
soup = BeautifulSoup(r.text, 'html.parser')

# Buscar elementos com textos relevantes
trending_texts = []
for tag in soup.find_all(['a', 'span', 'div', 'h3', 'h4', 'p']):
    text = tag.get_text(strip=True)
    if text and len(text) > 2 and len(text) < 100:
        # Filtrar apenas textos que parecem ser tendências
        if any(kw in text.lower() for kw in ['trending', 'search', 'queries', 'busca']):
            trending_texts.append(text)

print(f"\nTextos encontrados com keywords: {len(trending_texts)}")
for t in trending_texts[:10]:
    print(f"  - {t}")

# 2. Tentar outra abordagem - Google Trends explore
print("\n=== GOOGLE TRENDS EXPLORE ===")
url2 = 'https://trends.google.com/trends/explore?geo=BR&q='
r2 = requests.get(url2, timeout=30, headers=headers)
print(f"Status: {r2.status_code}")

# 3. Tentar Google News como proxy para tendências
print("\n=== GOOGLE NEWS BRASIL (TENDÊNCIAS) ===")
url3 = 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB'
r3 = requests.get(url3, timeout=30, headers=headers)
print(f"Status: {r3.status_code}, Length: {len(r3.text)}")
soup3 = BeautifulSoup(r3.text, 'html.parser')
headlines = soup3.find_all(['h3', 'h4', 'a'])
titles = set()
for h in headlines:
    text = h.get_text(strip=True)
    if text and 3 < len(text) < 80 and text not in titles:
        titles.add(text)

print(f"Headlines encontradas: {len(titles)}")
for t in list(titles)[:15]:
    print(f"  - {t}")
