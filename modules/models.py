# modules/models.py

import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Importa sistema de produtos dinâmicos
from modules.produtos_dinamicos import obter_produtos_dinamicos, PRODUTOS_FALLBACK

# ============================================================
# ARQUIVOS DE DADOS (NA RAIZ)
# ============================================================
ARQUIVO_APOIADORES = "apoiadores.json"  # <-- NA RAIZ

# ============================================================
# FUNÇÕES DE APOIADORES
# ============================================================
def carregar_apoiadores():
    """Carrega a lista de apoiadores do arquivo na raiz"""
    if os.path.exists(ARQUIVO_APOIADORES):
        try:
            with open(ARQUIVO_APOIADORES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Dados padrão
    apoiadores_padrao = {
        "mayara": {
            "nome": "Mayara Veloso",
            "ordem": 1,
            "email": "mayara@email.com",
            "coroinha": "👑",
            "cor": "#FF6B6B",
            "data_entrada": "2026-07-01",
            "royalties_recebidos": 0.0,
            "repasse_ativo": True,
            "plano": "Fundadora"
        },
        "iago": {
            "nome": "Iago Coelho",
            "ordem": 2,
            "email": "iago@email.com",
            "coroinha": "👑",
            "cor": "#4ECDC4",
            "data_entrada": "2026-07-05",
            "royalties_recebidos": 0.0,
            "repasse_ativo": True,
            "plano": "Apoiador"
        }
    }
    
   
