#!/usr/bin/env python3
"""Testar Google Trends dailytrends API com endpoint correto."""
import requests
import json
from datetime import datetime

# Endpoint correto baseado no artigo - usa 'ed' (end date) como parâmetro numérico
today = datetime.now().strftime('%Y%m%d')
print(f"Data hoje: {today}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/plain,*/*;q=0.5',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Referer': 'https://trends.google.com/trends/trendingsearches/daily?geo=BR',
}

url = f'https://trends.google.com/trends/api/dailytrends?hl=pt-BR&tz=-180&ed={today}&geo=BR&hl=pt-BR&ns=15'
print(f"URL: {url}")

r = requests.get(url, timeout=20, headers=headers)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type', '?')}")

if r.status_code == 200:
    text = r.text
    if text.startswith(")]}'"):
        text = text[5:]
    try:
        data = json.loads(text)
        default = data.get('default', {})
        days = default.get('trendingSearchesDays', [])
        print(f"\nDias com dados: {len(days)}")
        for day in days[:3]:
            print(f"  Data: {day.get('formattedDate', '?')}")
            searches = day.get('trendingSearches', [])
            print(f"  Trending searches: {len(searches)}")
            for s in searches[:15]:
                query = s.get('title', {}).get('query', 'N/A')
                traffic = s.get('formattedTraffic', 'N/A')
                print(f"    - {query} ({traffic})")
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        print(f"Text: {text[:500]}")
else:
    print(f"Response: {r.text[:500]}")
