#!/usr/bin/env python3
"""Testar extração de trending searches do Google Trends via scraping."""
import requests
from bs4 import BeautifulSoup
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Cookie': 'CONSENT=YES+cb.20210328-17-p0.en+FX+471',
}

# Google Trends carrega dados via XHR/API interna
# Vamos tentar a API interna do Google Trends
print("=== GOOGLE TRENDS API INTERNA ===")

# A API interna do Google Trends para trending searches
api_url = 'https://trends.google.com/trends/api/dailytrends?hl=pt-BR&tz=180&geo=BR&ns=15'
try:
    r = requests.get(api_url, timeout=20, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type', '?')}")
    print(f"First 2000 chars: {r.text[:2000]}")
except Exception as e:
    print(f"Erro: {e}")

# Tentar com cookie diferente
print("\n=== COM COOKIE DIFERENTE ===")
headers2 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/plain,*/*;q=0.5',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}
try:
    r2 = requests.get(api_url, timeout=20, headers=headers2)
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        # O resultado pode ter prefixo ")]}'\n" que precisa ser removido
        text = r2.text
        if text.startswith(')]}\''):
            text = text[5:]
        try:
            data = json.loads(text)
            print(f"JSON parsed successfully!")
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            if 'default' in data:
                d = data['default']
                print(f"Default keys: {list(d.keys())[:10]}")
                if 'trendingSearchesDays' in d:
                    days = d['trendingSearchesDays']
                    for day in days[:2]:
                        searches = day.get('trendingSearches', [])
                        print(f"\nTrending searches ({len(searches)}):")
                        for s in searches[:20]:
                            query = s.get('title', {}).get('query', 'N/A')
                            traffic = s.get('formattedTraffic', 'N/A')
                            print(f"  - {query} ({traffic})")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Text: {text[:500]}")
    else:
        print(f"Response: {r2.text[:300]}")
except Exception as e:
    print(f"Erro: {e}")
