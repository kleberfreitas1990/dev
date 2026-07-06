import json
import os
import random
from datetime import datetime, timedelta

# ============================================================
# ARQUIVOS DE DADOS
# ============================================================
ARQUIVO_LICENCAS = "licencas.json"
ARQUIVO_APOIADORES = "apoiadores.json"
ARQUIVO_DADOS_DIARIOS = "dados_diarios.json"

# ============================================================
# CONSTANTES
# ============================================================
BUSCAS_DIARIAS = 3
LICENCA_TRIAL = "TESTE-AFILIADO-2026"
ADMIN_LICENCA = "ADMIN-2026-KLEBER"

# ============================================================
# DADOS COMPLETOS DOS PRODUTOS
# ============================================================
DADOS_COMPLETOS = {
    "casaco": {
        "pins": 3400, "pins_historico": 2900, "crescimento": 45, "views_tiktok": 5.8,
        "resultados_ml": 1240, "buscas_mes": 15200, "buscas_historico": 12800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 17.2, "tendencia": "🚀 Em alta"
    },
    "blusa de lã": {
        "pins": 2800, "pins_historico": 2200, "crescimento": 38, "views_tiktok": 4.2,
        "resultados_ml": 890, "buscas_mes": 12500, "buscas_historico": 9800,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 27.3, "tendencia": "🚀 Em alta"
    },
    "bota": {
        "pins": 1500, "pins_historico": 1200, "crescimento": 20, "views_tiktok": 2.8,
        "resultados_ml": 560, "buscas_mes": 8900, "buscas_historico": 7200,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 25.0, "tendencia": "📈 Crescendo"
    },
    "cachecol": {
        "pins": 1200, "pins_historico": 950, "crescimento": 15, "views_tiktok": 1.9,
        "resultados_ml": 430, "buscas_mes": 7800, "buscas_historico": 6500,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 26.3, "tendencia": "📈 Crescendo"
    },
    "cobertor": {
        "pins": 950, "pins_historico": 780, "crescimento": 12, "views_tiktok": 1.5,
        "resultados_ml": 380, "buscas_mes": 6500, "buscas_historico": 5200,
        "categoria": "Casa", "evento": "Férias Escolares", "variacao": 21.8, "tendencia": "➡️ Estável"
    },
    "smartwatch": {
        "pins": 2800, "pins_historico": 2500, "crescimento": 35, "views_tiktok": 4.5,
        "resultados_ml": 1500, "buscas_mes": 18500, "buscas_historico": 15200,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 12.0, "tendencia": "🚀 Em alta"
    },
    "fone bluetooth": {
        "pins": 2200, "pins_historico": 2000, "crescimento": 30, "views_tiktok": 3.8,
        "resultados_ml": 1200, "buscas_mes": 16500, "buscas_historico": 13800,
        "categoria": "Eletrônicos", "evento": "Tendência", "variacao": 10.0, "tendencia": "➡️ Estável"
    },
    "perfume": {
        "pins": 2100, "pins_historico": 1800, "crescimento": 28, "views_tiktok": 3.2,
        "resultados_ml": 1100, "buscas_mes": 14200, "buscas_historico": 11800,
        "categoria": "Beleza", "evento": "Dia dos Namorados", "variacao": 16.7, "tendencia": "🚀 Em alta"
    },
    "vestido": {
        "pins": 1900, "pins_historico": 1600, "crescimento": 25, "views_tiktok": 2.9,
        "resultados_ml": 980, "buscas_mes": 12500, "buscas_historico": 10500,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 18.8, "tendencia": "📈 Crescendo"
    },
    "bolsa": {
        "pins": 1700, "pins_historico": 1400, "crescimento": 22, "views_tiktok": 2.5,
        "resultados_ml": 850, "buscas_mes": 11000, "buscas_historico": 9200,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 21.4, "tendencia": "📈 Crescendo"
    },
    "mochila": {
        "pins": 1400, "pins_historico": 1200, "crescimento": 18, "views_tiktok": 2.1,
        "resultados_ml": 720, "buscas_mes": 9500, "buscas_historico": 7800,
        "categoria": "Moda", "evento": "Volta às Aulas", "variacao": 16.7, "tendencia": "📈 Crescendo"
    },
    "tenis": {
        "pins": 1600, "pins_historico": 1300, "crescimento": 20, "views_tiktok": 2.3,
        "resultados_ml": 780, "buscas_mes": 10200, "buscas_historico": 8500,
        "categoria": "Moda", "evento": "Férias Escolares", "variacao": 23.1, "tendencia": "📈 Crescendo"
    }
}

# ============================================================
# PALAVRAS-CHAVE E HASHTAGS
# ============================================================
PALAVRAS_CHAVE_CAUDA_LONGA = {
    "casaco": {"palavra": "casaco feminino inverno 2026", "hashtags": ["#casacofeminino", "#inverno2026", "#lookinverno"]},
    "blusa de lã": {"palavra": "blusa de lã feminina elegante", "hashtags": ["#blusadelã", "#modainverno", "#lookelegante"]},
    "bota": {"palavra": "bota feminina cano médio", "hashtags": ["#botafeminina", "#modainverno", "#lookbota"]},
    "cachecol": {"palavra": "cachecol de lã para frio extremo", "hashtags": ["#cachecoldelã", "#acessóriosdeinverno", "#lookinverno"]},
    "cobertor": {"palavra": "cobertor de lã para cama king", "hashtags": ["#cobertorlã", "#decoraçãocasa", "#conforto"]},
    "smartwatch": {"palavra": "smartwatch feminino elegante", "hashtags": ["#smartwatch", "#tecnologia", "#eletrônicos"]},
    "fone bluetooth": {"palavra": "fone bluetooth JBL original", "hashtags": ["#fonebluetooth", "#áudio", "#tecnologia"]},
    "perfume": {"palavra": "perfume importado feminino", "hashtags": ["#perfumeimportado", "#belezafeminina", "#presentes"]},
    "vestido": {"palavra": "vestido feminino 2026", "hashtags": ["#vestidofeminino", "#moda2026", "#lookverão"]},
    "bolsa": {"palavra": "bolsa feminina couro", "hashtags": ["#bolsafeminina", "#acessórios", "#moda"]},
    "mochila": {"palavra": "mochila escolar infantil", "hashtags": ["#mochilaescolar", "#voltaasaulas", "#materialescolar"]},
    "tenis": {"palavra": "tênis esportivo feminino", "hashtags": ["#tênisesportivo", "#modaesportiva", "#lookcasual"]}
}

# ============================================================
# FUNÇÕES DE SCORE
# ============================================================
def calcular_score(produto, dados):
    score = 0
    if dados.get("pins", 0) > 2000: score += 3
    elif dados.get("pins", 0) > 1000: score += 2
    else: score += 1
    
    if dados.get("crescimento", 0) > 30: score += 2
    elif dados.get("crescimento", 0) > 15: score += 1
    
    if dados.get("views_tiktok", 0) > 3: score += 2
    elif dados.get("views_tiktok", 0) > 1: score += 1
    
    if dados.get("buscas_mes", 0) > 10000: score += 2
    elif dados.get("buscas_mes", 0) > 5000: score += 1
    
    if dados.get("variacao", 0) > 15: score += 1
    
    return min(score, 10)

def gerar_top10_produtos():
    resultados = []
    for produto, dados in DADOS_COMPLETOS.items():
        score = calcular_score(produto, dados)
        
        if score >= 8: potencial = "🟢 Alto"
        elif score >= 5: potencial = "🟡 Médio"
        else: potencial = "🔴 Baixo"
        
        resultados.append({
            "Produto": produto.capitalize(),
            "Categoria": dados.get("categoria", "Geral"),
            "Evento": dados.get("evento", "Tendência"),
            "Potencial": potencial,
            "Score": score,
            "Pins": f"{dados.get('pins', 0):,}",
            "Crescimento": f"+{dados.get('crescimento', 0)}%",
            "Views TikTok": f"{dados.get('views_tiktok', 0)}M",
            "Buscas no Mês": f"{dados.get('buscas_mes', 0):,}",
            "Resultados ML": f"{dados.get('resultados_ml', 0):,}",
            "Variação": f"+{dados.get('variacao', 0):.1f}%",
            "Tendência": dados.get('tendencia', '➡️ Estável')
        })
    
    return sorted(resultados, key=lambda x: x["Score"], reverse=True)[:10]

def gerar_sugestoes_diarias():
    return gerar_top10_produtos()[:BUSCAS_DIARIAS]

# ============================================================
# SISTEMA DE LICENÇAS (SIMPLIFICADO)
# ============================================================
class SistemaLicencas:
    def __init__(self):
        self.arquivo = ARQUIVO_LICENCAS
        self.dados = self.carregar()
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._criar_estrutura_padrao()
        return self._criar_estrutura_padrao()
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, ensure_ascii=False, indent=2)
    
    def _criar_estrutura_padrao(self):
        return {
            "licencas": {
                LICENCA_TRIAL: {
                    "tipo": "trial",
                    "status": "ativo",
                    "usuario": "Usuário Trial",
                    "plano": "Trial 7 dias",
                    "is_admin": False,
                    "is_apoiador": False
                },
                ADMIN_LICENCA: {
                    "tipo": "admin",
                    "status": "ativo",
                    "usuario": "Administrador",
                    "plano": "Administrador",
                    "is_admin": True,
                    "is_apoiador": False
                }
            }
        }
    
    def validar_licenca(self, codigo):
        licenca = self.dados["licencas"].get(codigo)
        if not licenca:
            return {"valido": False, "motivo": "Licença não encontrada"}
        if licenca.get("status") != "ativo":
            return {"valido": False, "motivo": f"Licença {licenca.get('status')}"}
        
        return {
            "valido": True,
            "usuario": licenca.get("usuario"),
            "plano": licenca.get("plano"),
            "is_admin": licenca.get("is_admin", False),
            "is_apoiador": licenca.get("is_apoiador", False)
        }
    
    def is_admin(self, codigo):
        licenca = self.dados["licencas"].get(codigo)
        return licenca.get("is_admin", False) if licenca else False

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'DADOS_COMPLETOS',
    'PALAVRAS_CHAVE_CAUDA_LONGA',
    'calcular_score',
    'gerar_top10_produtos',
    'gerar_sugestoes_diarias',
    'SistemaLicencas',
    'BUSCAS_DIARIAS',
    'LICENCA_TRIAL',
    'ADMIN_LICENCA'
]
