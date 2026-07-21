
import json
import os

# Novos termos enviados pelo usuário
novos_termos = [
    "Tênis Masculino", "Chopeira", "Fone de Ouvido Bluetooth", "Alexa", "Sex Doll", 
    "Tênis", "Crocs", "Moto Elétrica Scooter", "Balcão de Pia de Cozinha 160 cm", "Decoração",
    "Caixa Cacau Show Branca", "Caixa de Som Britânia PCX 12500", "Jibbitz", "Luminária", "Gabinete",
    "Bola Jabulani", "Masturbador Masculino", "Poltrona", "Camisa Espanha", "Chopp",
    "Cama Triliche", "Carrinho de Controle Remoto 4x4", "Kettlebell Acte Sports", "Fone de Ouvido Miniso", "Celular Xiaomi 14C 256GB 8GB RAM",
    "Celular Motorola 60 Pro", "Capacete Norisk Route FF345 Roxo", "Cama Box Viúva D45", "Caixa de Som Boombox 4 Branco", "Celular Xiaomi Redmi 13 4G 256GB 8GB"
]

def update_files():
    # 1. Atualizar shopee_trends.json (Cache imediato)
    cache_file = "shopee_trends.json"
    data = {
        "success": True,
        "data": novos_termos,
        "timestamp": "2026-07-20",
        "url_fonte": "https://shopee.com.br/ (Fallback v9.9)"
    }
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ {cache_file} atualizado.")

    # 2. Atualizar scraping_shopee_v2.py (Código fonte do fallback)
    scraper_path = "scraping_shopee_v2.py"
    if os.path.exists(scraper_path):
        with open(scraper_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        in_fallback = False
        for line in lines:
            if "TERMOS_FALLBACK =" in line:
                new_lines.append(f"    TERMOS_FALLBACK = {json.dumps(novos_termos, ensure_ascii=False)}\n")
                in_fallback = True
            elif in_fallback and "]" in line:
                in_fallback = False
                continue
            elif not in_fallback:
                new_lines.append(line)
        
        with open(scraper_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ {scraper_path} atualizado com novos termos de fallback.")

    # 3. Atualizar google_shopee_trends.py (Hot Trends)
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
