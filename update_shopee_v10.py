
import json
import os
from datetime import datetime
import random

# Novos termos fornecidos pelo usuário
novos_termos = [
    "Escrivaninha", "Fone de Ouvido Bluetooth", "Crocs Relâmpago Mcqueen", "Prateleira",
    "Capacete Norisk Route FF345 Roxo", "Fone de Ouvido Disney LF-918", "Penteadeira",
    "PC Gamer", "SSD", "Mochila", "Squishy", "Poltrona", "Câmera Babá Eletrônica Tarktark",
    "Pipa", "Escova Progressiva Everk", "Controle PC", "Armário Kapesberg", "Café Orfeu 1Kg",
    "100 Pacotes de Figurinhas da Copa", "Moto Elétrica Scooter", "Caixa de Som Bluetooth JBL",
    "Celular Xiaomi Redmi 13 4G 256GB 8GB", "Celular Xiaomi Redmi 15C 256GB 8GB RAM Dual Sim Preto",
    "Kettlebell Acte Sports", "Carrinho de Controle Remoto 4x4", "Caixa de Vela 7 Dias",
    "Cama Triliche", "Cama Box Viúva D45", "Celular Xiaomi 128 GB", "Caixa de Som Boombox 4 Branco"
]

def generate_mock_data(termo):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    return {
        "pins": random.randint(40000, 95000),
        "crescimento": random.randint(80, 300),
        "views_tiktok": round(random.uniform(50.0, 90.0), 1),
        "score": random.randint(8, 10),
        "fonte": "Shopee — termos priorizados (v10)",
        "origem_coleta": "fallback",
        "atualizado": agora,
        "tendencia": "🔥 Explosão Shopee"
    }

def update_files():
    # 1. Atualizar shopee_trends.json
    cache_file = "shopee_trends.json"
    new_data = {}
    for termo in novos_termos:
        new_data[termo] = generate_mock_data(termo)
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print(f"✅ {cache_file} atualizado com {len(novos_termos)} termos.")

    # 2. Atualizar scraping_shopee_v2.py (lista dentro de termos = [...])
    scraper_path = "scraping_shopee_v2.py"
    if os.path.exists(scraper_path):
        with open(scraper_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        in_fallback_list = False
        for line in lines:
            if "termos = [" in line and "list(dict.fromkeys" not in line:
                new_lines.append(f"            termos = [\n")
                for termo in novos_termos:
                    new_lines.append(f"                \"{termo}\",\n")
                in_fallback_list = True
            elif in_fallback_list and "]" in line:
                new_lines.append(f"            ]\n")
                in_fallback_list = False
            elif not in_fallback_list:
                new_lines.append(line)
        
        with open(scraper_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ {scraper_path} atualizado.")

    # 3. Atualizar google_shopee_trends.py
    google_path = "modules/google_shopee_trends.py"
    if os.path.exists(google_path):
        with open(google_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        in_hot = False
        for line in lines:
            if "TERMOS_HOT_TRENDS =" in line:
                new_lines.append(f"TERMOS_HOT_TRENDS = {json.dumps(novos_termos, ensure_ascii=False)}\n")
                in_hot = True
            elif in_hot and "]" in line:
                in_hot = False
                continue
            elif not in_hot:
                new_lines.append(line)
        
        with open(google_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ {google_path} atualizado.")

if __name__ == "__main__":
    update_files()
