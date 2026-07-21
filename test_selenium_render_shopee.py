
import requests
import json
import time

def test_selenium_shopee():
    url_base = "https://selenium-scraper-emnc.onrender.com"
    print(f"--- Testando Servidor Selenium: {url_base} ---")
    
    # 1. Verificar Status
    try:
        print("Verificando status do servidor...")
        status = requests.get(f"{url_base}/", timeout=15)
        print(f"Status: {status.status_code}")
        print(f"Resposta: {status.json()}")
    except Exception as e:
        print(f"Erro ao verificar status: {e}")
        print("Dica: O servidor no Render pode estar 'acordando' (cold start).")

    # 2. Tentar Capturar Buscas (o que pega o rodapé)
    print("\nTentando capturar buscas da Shopee (rodapé)...")
    try:
        # Aumentamos o timeout porque o Render demora para acordar e a raspagem é lenta
        start_time = time.time()
        response = requests.get(f"{url_base}/buscas", timeout=120)
        end_time = time.time()
        
        print(f"Tempo de resposta: {end_time - start_time:.2f}s")
        print(f"Status API: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            if dados.get("success"):
                termos = dados.get("data", [])
                print(f"✅ SUCESSO! Capturados {len(termos)} termos:")
                for i, termo in enumerate(termos[:10]):
                    print(f"  {i+1}. {termo}")
                
                # Salvar resultado para verificação
                with open("shopee_selenium_result.json", "w", encoding="utf-8") as f:
                    json.dump(dados, f, indent=4, ensure_ascii=False)
            else:
                print(f"❌ Erro na API: {dados.get('error')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT: O servidor demorou demais para responder. Tente novamente em alguns segundos.")
    except Exception as e:
        print(f"❌ Erro ao chamar /buscas: {e}")

if __name__ == "__main__":
    test_selenium_shopee()
