import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from datetime import datetime, date, timedelta
import time
import json
import os
import warnings
import random

# ============================================================
# SUPRIMIR WARNINGS
# ============================================================
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="Minerador de Produtos - Afiliados",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTES
# ============================================================
CHAVE_TESTE = "TESTE-AFILIADO-2026"
ARQUIVO_CACHE = "cache_tendencias.json"
ARQUIVO_CONSULTAS = "consultas_dia.json"

# ============================================================
# CONFIGURACAO DAS APIS
# ============================================================
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================
# CONTROLE DE CONSULTAS DIARIAS
# ============================================================
class ControleConsultas:
    def __init__(self):
        self.arquivo = ARQUIVO_CONSULTAS
        self.dados = self.carregar()
        self.limite_diario = 3
    
    def carregar(self):
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def salvar(self):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, ensure_ascii=False, indent=2)
    
    def consultas_hoje(self):
        hoje = datetime.now().date().isoformat()
        if hoje not in self.dados:
            self.dados[hoje] = {"consultas": 0, "termos": []}
            self.salvar()
        return self.dados[hoje]["consultas"]
    
    def pode_consultar(self):
        return self.consultas_hoje() < self.limite_diario
    
    def registrar_consulta(self, termo):
        hoje = datetime.now().date().isoformat()
        if hoje not in self.dados:
            self.dados[hoje] = {"consultas": 0, "termos": []}
        
        self.dados[hoje]["consultas"] += 1
        self.dados[hoje]["termos"].append({
            "termo": termo,
            "hora": datetime.now().strftime("%H:%M")
        })
        self.salvar()
    
    def get_status(self):
        hoje = datetime.now().date().isoformat()
        if hoje in self.dados:
            return {
                "usadas": self.dados[hoje]["consultas"],
                "limite": self.limite_diario,
                "restam": self.limite_diario - self.dados[hoje]["consultas"],
                "termos": [t["termo"] for t in self.dados[hoje]["termos"]]
            }
        return {
            "usadas": 0,
            "limite": self.limite_diario,
            "restam": self.limite_diario,
            "termos": []
        }

# ============================================================
# DADOS HISTORICOS POR MES (COM INSIGHTS ADICIONAIS)
# ============================================================
DADOS_HISTORICOS = {
    1: {
        "tendencias": [
            {"produto": "material escolar", "categoria": "Papelaria", "potencial": "Alto", "pins": 4500, "crescimento": "+35%", "tiktok": "8.2M"},
            {"produto": "mochila escolar", "categoria": "Moda", "potencial": "Alto", "pins": 3200, "crescimento": "+28%", "tiktok": "5.1M"},
            {"produto": "smartwatch", "categoria": "Eletrônicos", "potencial": "Médio", "pins": 1800, "crescimento": "+12%", "tiktok": "3.4M"},
            {"produto": "fone bluetooth", "categoria": "Eletrônicos", "potencial": "Médio", "pins": 1500, "crescimento": "+8%", "tiktok": "2.8M"},
            {"produto": "tenis", "categoria": "Moda", "potencial": "Médio", "pins": 2800, "crescimento": "+5%", "tiktok": "4.2M"},
            {"produto": "caderno", "categoria": "Papelaria", "potencial": "Médio", "pins": 900, "crescimento": "+15%", "tiktok": "1.2M"},
            {"produto": "estojo", "categoria": "Papelaria", "potencial": "Médio", "pins": 750, "crescimento": "+10%", "tiktok": "0.9M"},
            {"produto": "luminaria de mesa", "categoria": "Casa", "potencial": "Baixo", "pins": 600, "crescimento": "+3%", "tiktok": "0.5M"}
        ],
        "eventos": ["Volta às Aulas", "Ano Novo"],
        "sazonal": "Verão",
        "insight": "Foco em produtos para estudantes: mochilas e material escolar estão em alta. Aproveite o início do ano letivo."
    },
    2: {
        "tendencias": [
            {"produto": "fantasia carnaval", "categoria": "Moda", "potencial": "Alto", "pins": 5200, "crescimento": "+45%", "tiktok": "12.5M"},
            {"produto": "biquini", "categoria": "Moda", "potencial": "Alto", "pins": 3800, "crescimento": "+30%", "tiktok": "6.8M"},
            {"produto": "protetor solar", "categoria": "Beleza", "potencial": "Alto", "pins": 2100, "crescimento": "+25%", "tiktok": "4.5M"},
            {"produto": "caixa de som", "categoria": "Eletrônicos", "potencial": "Médio", "pins": 1200, "crescimento": "+10%", "tiktok": "2.1M"},
            {"produto": "chinelo", "categoria": "Moda", "potencial": "Médio", "pins": 1600, "crescimento": "+8%", "tiktok": "3.2M"},
            {"produto": "glitter", "categoria": "Beleza", "potencial": "Médio", "pins": 800, "crescimento": "+20%", "tiktok": "1.8M"},
            {"produto": "maquiagem", "categoria": "Beleza", "potencial": "Médio", "pins": 1400, "crescimento": "+12%", "tiktok": "3.8M"},
            {"produto": "sungas", "categoria": "Moda", "potencial": "Baixo", "pins": 500, "crescimento": "+5%", "tiktok": "0.7M"}
        ],
        "eventos": ["Carnaval"],
        "sazonal": "Verão",
        "insight": "Carnaval é o destaque! Fantasias e acessórios para folia estão bombando. Produtos para praia também têm alta demanda."
    },
    3: {
        "tendencias": [
            {"produto": "kit praia", "categoria": "Moda", "potencial": "Alto", "pins": 3400, "crescimento": "+32%", "tiktok": "5.8M"},
            {"produto": "oculos sol", "categoria": "Moda", "potencial": "Alto", "pins": 2900, "crescimento": "+28%", "tiktok": "4.9M"},
            {"produto": "canga", "categoria": "Moda", "potencial": "Médio", "pins": 1200, "crescimento": "+15%", "tiktok": "1.5M"},
            {"produto": "vestido", "categoria": "Moda", "potencial": "Médio", "pins": 2100, "crescimento": "+10%", "tiktok": "3.6M"},
            {"produto": "sandalia", "categoria": "Moda", "potencial": "Médio", "pins": 1800, "crescimento": "+8%", "tiktok": "2.9M"},
            {"produto": "bolsa praia", "categoria": "Moda", "potencial": "Médio", "pins": 950, "crescimento": "+12%", "tiktok": "1.1M"},
            {"produto": "toalha", "categoria": "Casa", "potencial": "Baixo", "pins": 700, "crescimento": "+5%", "tiktok": "0.6M"},
            {"produto": "chapeu", "categoria": "Moda", "potencial": "Baixo", "pins": 650, "crescimento": "+3%", "tiktok": "0.8M"}
        ],
        "eventos": ["Dia da Mulher", "Outono"],
        "sazonal": "Outono",
        "insight": "Transição de verão para outono. Kits praia ainda em alta, mas já comece a preparar conteúdo para moda outono."
    },
    4: {
        "tendencias": [
            {"produto": "ovo pascoa", "categoria": "Alimentos", "potencial": "Alto", "pins": 4600, "crescimento": "+55%", "tiktok": "8.9M"},
            {"produto": "chocolate", "categoria": "Alimentos", "potencial": "Alto", "pins": 3900, "crescimento": "+40%", "tiktok": "7.2M"},
            {"produto": "cesta", "categoria": "Casa", "potencial": "Alto", "pins": 1800, "crescimento": "+35%", "tiktok": "2.5M"},
            {"produto": "brinquedo", "categoria": "Brinquedos", "potencial": "Médio", "pins": 2200, "crescimento": "+18%", "tiktok": "4.1M"},
            {"produto": "pelucia", "categoria": "Brinquedos", "potencial": "Médio", "pins": 1400, "crescimento": "+12%", "tiktok": "2.2M"},
            {"produto": "jogo", "categoria": "Brinquedos", "potencial": "Médio", "pins": 1100, "crescimento": "+8%", "tiktok": "1.8M"},
            {"produto": "boneca", "categoria": "Brinquedos", "potencial": "Baixo", "pins": 800, "crescimento": "+5%", "tiktok": "1.2M"},
            {"produto": "carrinho", "categoria": "Brinquedos", "potencial": "Baixo", "pins": 700, "crescimento": "+3%", "tiktok": "0.9M"}
        ],
        "eventos": ["Páscoa", "Tiradentes"],
        "sazonal": "Outono",
        "insight": "Páscoa é o grande evento! Ovos de chocolate e cestas estão com alta demanda. Brinquedos também são uma boa oportunidade."
    },
    5: {
        "tendencias": [
            {"produto": "dia das maes", "categoria": "Presentes", "potencial": "Alto", "pins": 5800, "crescimento": "+60%", "tiktok": "15.2M"},
            {"produto": "perfume", "categoria": "Beleza", "potencial": "Alto", "pins": 3500, "crescimento": "+35%", "tiktok": "6.8M"},
            {"produto": "bolsa", "categoria": "Moda", "potencial": "Alto", "pins": 2800, "crescimento": "+28%", "tiktok": "4.5M"},
            {"produto": "flores", "categoria": "Presentes", "potencial": "Médio", "pins": 1600, "crescimento": "+20%", "tiktok": "3.2M"},
            {"produto": "kit beleza", "categoria": "Beleza", "potencial": "Médio", "pins": 1200, "crescimento": "+15%", "tiktok": "2.1M"},
            {"produto": "caneca", "categoria": "Presentes", "potencial": "Médio", "pins": 900, "crescimento": "+10%", "tiktok": "1.5M"},
            {"produto": "bijuteria", "categoria": "Moda", "potencial": "Baixo", "pins": 650, "crescimento": "+5%", "tiktok": "0.8M"},
            {"produto": "cartao presente", "categoria": "Presentes", "potencial": "Baixo", "pins": 500, "crescimento": "+3%", "tiktok": "0.6M"}
        ],
        "eventos": ["Dia das Mães", "Dia do Trabalho"],
        "sazonal": "Outono",
        "insight": "Dia das Mães é a maior oportunidade do mês! Perfumes, bolsas e kits de beleza são os mais procurados. Crie conteúdo focado em presentes."
    },
    6: {
        "tendencias": [
            {"produto": "dia dos namorados", "categoria": "Presentes", "potencial": "Alto", "pins": 6200, "crescimento": "+70%", "tiktok": "18.5M"},
            {"produto": "perfume", "categoria": "Beleza", "potencial": "Alto", "pins": 3800, "crescimento": "+40%", "tiktok": "7.8M"},
            {"produto": "vinho", "categoria": "Alimentos", "potencial": "Alto", "pins": 2100, "crescimento": "+30%", "tiktok": "3.5M"},
            {"produto": "kit jantar", "categoria": "Casa", "potencial": "Médio", "pins": 1100, "crescimento": "+18%", "tiktok": "1.8M"},
            {"produto": "lingerie", "categoria": "Moda", "potencial": "Médio", "pins": 1400, "crescimento": "+22%", "tiktok": "2.5M"},
            {"produto": "jantar", "categoria": "Presentes", "potencial": "Médio", "pins": 800, "crescimento": "+12%", "tiktok": "1.2M"},
            {"produto": "flores", "categoria": "Presentes", "potencial": "Baixo", "pins": 600, "crescimento": "+8%", "tiktok": "0.9M"},
            {"produto": "chocolate", "categoria": "Alimentos", "potencial": "Baixo", "pins": 550, "crescimento": "+5%", "tiktok": "0.7M"}
        ],
        "eventos": ["Dia dos Namorados", "Festa Junina"],
        "sazonal": "Inverno",
        "insight": "Dia dos Namorados é o ápice! Perfumes e presentes românticos são os mais buscados. Vinho e kits de jantar também têm alta procura."
    },
    7: {
        "tendencias": [
            {"produto": "casaco", "categoria": "Moda", "potencial": "Alto", "pins": 3400, "crescimento": "+45%", "tiktok": "5.8M"},
            {"produto": "blusa de la", "categoria": "Moda", "potencial": "Alto", "pins": 2800, "crescimento": "+38%", "tiktok": "4.2M"},
            {"produto": "bota", "categoria": "Moda", "potencial": "Médio", "pins": 1500, "crescimento": "+20%", "tiktok": "2.8M"},
            {"produto": "cachecol", "categoria": "Moda", "potencial": "Médio", "pins": 1200, "crescimento": "+15%", "tiktok": "1.9M"},
            {"produto": "cobertor", "categoria": "Casa", "potencial": "Médio", "pins": 950, "crescimento": "+12%", "tiktok": "1.5M"},
            {"produto": "meia", "categoria": "Moda", "potencial": "Médio", "pins": 800, "crescimento": "+10%", "tiktok": "1.1M"},
            {"produto": "luva", "categoria": "Moda", "potencial": "Baixo", "pins": 500, "crescimento": "+8%", "tiktok": "0.6M"},
            {"produto": "jaqueta", "categoria": "Moda", "potencial": "Baixo", "pins": 450, "crescimento": "+5%", "tiktok": "0.5M"}
        ],
        "eventos": ["Férias Escolares"],
        "sazonal": "Inverno",
        "insight": "Inverno no auge! Casacos e blusas de lã são os mais procurados. Aproveite as férias para conteúdo de viagens e looks de inverno."
    },
    8: {
        "tendencias": [
            {"produto": "dia dos pais", "categoria": "Presentes", "potencial": "Alto", "pins": 4900, "crescimento": "+55%", "tiktok": "14.2M"},
            {"produto": "relogio", "categoria": "Moda", "potencial": "Alto", "pins": 2700, "crescimento": "+32%", "tiktok": "4.8M"},
            {"produto": "ferramenta", "categoria": "Casa", "potencial": "Alto", "pins": 1900, "crescimento": "+28%", "tiktok": "3.2M"},
            {"produto": "camisa", "categoria": "Moda", "potencial": "Médio", "pins": 1600, "crescimento": "+18%", "tiktok": "2.5M"},
            {"produto": "perfume masculino", "categoria": "Beleza", "potencial": "Médio", "pins": 1300, "crescimento": "+15%", "tiktok": "2.1M"},
            {"produto": "kit churrasco", "categoria": "Casa", "potencial": "Médio", "pins": 850, "crescimento": "+12%", "tiktok": "1.4M"},
            {"produto": "caneca", "categoria": "Presentes", "potencial": "Baixo", "pins": 600, "crescimento": "+8%", "tiktok": "0.8M"},
            {"produto": "carteira", "categoria": "Moda", "potencial": "Baixo", "pins": 500, "crescimento": "+5%", "tiktok": "0.6M"}
        ],
        "eventos": ["Dia dos Pais", "Volta às Aulas"],
        "sazonal": "Inverno",
        "insight": "Dia dos Pais! Relógios e ferramentas são os presentes mais procurados. Também comece a preparar conteúdo para volta às aulas."
    },
    9: {
        "tendencias": [
            {"produto": "camisa", "categoria": "Moda", "potencial": "Alto", "pins": 2200, "crescimento": "+25%", "tiktok": "3.8M"},
            {"produto": "calca", "categoria": "Moda", "potencial": "Alto", "pins": 1900, "crescimento": "+22%", "tiktok": "3.2M"},
            {"produto": "tenis", "categoria": "Moda", "potencial": "Alto", "pins": 2500, "crescimento": "+20%", "tiktok": "4.5M"},
            {"produto": "blusa", "categoria": "Moda", "potencial": "Médio", "pins": 1400, "crescimento": "+15%", "tiktok": "2.8M"},
            {"produto": "jaqueta jeans", "categoria": "Moda", "potencial": "Médio", "pins": 1100, "crescimento": "+12%", "tiktok": "1.9M"},
            {"produto": "sapato social", "categoria": "Moda", "potencial": "Médio", "pins": 850, "crescimento": "+10%", "tiktok": "1.5M"},
            {"produto": "mochila", "categoria": "Moda", "potencial": "Baixo", "pins": 700, "crescimento": "+8%", "tiktok": "1.1M"},
            {"produto": "bolsa", "categoria": "Moda", "potencial": "Baixo", "pins": 650, "crescimento": "+5%", "tiktok": "0.9M"}
        ],
        "eventos": ["Independência do Brasil", "Primavera"],
        "sazonal": "Primavera",
        "insight": "Primavera chegando! Moda leve e colorida começa a bombar. Camisas e calças são a base do guarda-roupa de primavera."
    },
    10: {
        "tendencias": [
            {"produto": "fantasia halloween", "categoria": "Moda", "potencial": "Alto", "pins": 4800, "crescimento": "+65%", "tiktok": "12.8M"},
            {"produto": "brinquedo", "categoria": "Brinquedos", "potencial": "Alto", "pins": 3200, "crescimento": "+40%", "tiktok": "5.8M"},
            {"produto": "decoracao", "categoria": "Casa", "potencial": "Alto", "pins": 2100, "crescimento": "+35%", "tiktok": "3.5M"},
            {"produto": "maquiagem", "categoria": "Beleza", "potencial": "Médio", "pins": 1400, "crescimento": "+20%", "tiktok": "2.8M"},
            {"produto": "doces", "categoria": "Alimentos", "potencial": "Médio", "pins": 1100, "crescimento": "+18%", "tiktok": "2.2M"},
            {"produto": "mascara", "categoria": "Moda", "potencial": "Médio", "pins": 850, "crescimento": "+15%", "tiktok": "1.6M"},
            {"produto": "abobora", "categoria": "Casa", "potencial": "Baixo", "pins": 550, "crescimento": "+10%", "tiktok": "0.9M"},
            {"produto": "livro infantil", "categoria": "Livros", "potencial": "Baixo", "pins": 450, "crescimento": "+8%", "tiktok": "0.6M"}
        ],
        "eventos": ["Dia das Crianças", "Halloween"],
        "sazonal": "Primavera",
        "insight": "Halloween e Dia das Crianças! Fantasias e brinquedos estão em alta. Decoração também tem grande procura para festas."
    },
    11: {
        "tendencias": [
            {"produto": "black friday", "categoria": "Eletrônicos", "potencial": "Alto", "pins": 7200, "crescimento": "+85%", "tiktok": "25.5M"},
            {"produto": "smartwatch", "categoria": "Eletrônicos", "potencial": "Alto", "pins": 4500, "crescimento": "+50%", "tiktok": "8.5M"},
            {"produto": "fone", "categoria": "Eletrônicos", "potencial": "Alto", "pins": 3800, "crescimento": "+45%", "tiktok": "7.2M"},
            {"produto": "celular", "categoria": "Eletrônicos", "potencial": "Médio", "pins": 2900, "crescimento": "+30%", "tiktok": "5.8M"},
            {"produto": "caixa de som", "categoria": "Eletrônicos", "potencial": "Médio", "pins": 1600, "crescimento": "+20%", "tiktok": "3.2M"},
            {"produto": "carregador", "categoria": "Eletrônicos", "potencial": "Médio", "pins": 1200, "crescimento": "+15%", "tiktok": "2.1M"},
            {"produto": "power bank", "categoria": "Eletrônicos", "potencial": "Baixo", "pins": 850, "crescimento": "+10%", "tiktok": "1.5M"},
            {"produto": "notebook", "categoria": "Eletrônicos", "potencial": "Baixo", "pins": 700, "crescimento": "+8%", "tiktok": "1.2M"}
        ],
        "eventos": ["Black Friday", "Cyber Monday"],
        "sazonal": "Primavera",
        "insight": "Black Friday é o evento do ano! Eletrônicos dominam as buscas. Smartwatches e fones estão com crescimento explosivo."
    },
    12: {
        "tendencias": [
            {"produto": "natal", "categoria": "Presentes", "potencial": "Alto", "pins": 8500, "crescimento": "+95%", "tiktok": "32.5M"},
            {"produto": "brinquedo", "categoria": "Brinquedos", "potencial": "Alto", "pins": 5200, "crescimento": "+60%", "tiktok": "9.8M"},
            {"produto": "perfume", "categoria": "Beleza", "potencial": "Alto", "pins": 4200, "crescimento": "+50%", "tiktok": "7.5M"},
            {"produto": "decoracao", "categoria": "Casa", "potencial": "Médio", "pins": 2800, "crescimento": "+35%", "tiktok": "4.8M"},
            {"produto": "kit beleza", "categoria": "Beleza", "potencial": "Médio", "pins": 1600, "crescimento": "+25%", "tiktok": "2.8M"},
            {"produto": "vinho", "categoria": "Alimentos", "potencial": "Médio", "pins": 1200, "crescimento": "+20%", "tiktok": "2.1M"},
            {"produto": "espumante", "categoria": "Alimentos", "potencial": "Baixo", "pins": 800, "crescimento": "+15%", "tiktok": "1.4M"},
            {"produto": "arvore", "categoria": "Casa", "potencial": "Baixo", "pins": 650, "crescimento": "+12%", "tiktok": "1.1M"}
        ],
        "eventos": ["Natal", "Réveillon"],
        "sazonal": "Verão",
        "insight": "Natal é o pico do ano! Presentes, brinquedos e perfumes dominam as buscas. Decoração também tem alta demanda."
    }
}

# ============================================================
# FUNCOES DE API
# ============================================================
class GoogleShoppingAPI:
    def __init__(self):
        self.api_key = SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
    
    def buscar_produtos(self, termo, limite=3):
        if not self.api_key:
            return []
        
        try:
            params = {
                "q": termo,
                "tbm": "shop",
                "api_key": self.api_key,
                "gl": "br",
                "hl": "pt",
                "num": limite,
                "location": "Brazil",
                "device": "desktop"
            }
            
            resp = requests.get(self.base_url, params=params, timeout=15)
            data = resp.json()
            
            produtos = []
            for item in data.get("shopping_results", [])[:limite]:
                preco_str = item.get("price", "R$ 0").replace("R$", "").replace(",", ".").strip()
                try:
                    preco_num = float(preco_str.split()[0]) if preco_str else 0
                except:
                    preco_num = 0
                
                produtos.append({
                    "nome": item.get("title", ""),
                    "preco": item.get("price", "R$ 0"),
                    "loja": item.get("source", ""),
                    "link": item.get("link", ""),
                    "avaliacao": item.get("rating", None),
                    "reviews": item.get("reviews", 0)
                })
            
            return produtos
        except Exception as e:
            return []
    
    def buscar_total_resultados(self, termo):
        if not self.api_key:
            return 0
        
        try:
            params = {
                "q": termo,
                "tbm": "shop",
                "api_key": self.api_key,
                "gl": "br",
                "hl": "pt",
                "num": 1
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            data = resp.json()
            return data.get("search_information", {}).get("total_results", 0)
        except:
            return 0

# ============================================================
# FUNCOES DE LOGIN
# ============================================================
def verificar_login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛒 Minerador de Produtos - Afiliados")
        st.markdown("### 🔐 Login")
        chave = st.text_input("Digite sua chave de acesso:", type="password")
        if st.button("Entrar", type="primary"):
            if chave == CHAVE_TESTE:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Chave invalida. Tente novamente.")
        st.stop()

# ============================================================
# FUNCAO PARA ATUALIZAR SUGESTOES COM SERPAPI
# ============================================================
def atualizar_sugestoes_com_serpapi(tendencias):
    controle = ControleConsultas()
    resultados = []
    
    for item in tendencias:
        termo = item["produto"]
        
        if controle.pode_consultar():
            produtos = google_shopping.buscar_produtos(termo, 2)
            total = google_shopping.buscar_total_resultados(termo)
            
            if produtos:
                controle.registrar_consulta(termo)
                
                if total < 50:
                    potencial = "Alto"
                    status = "🟢"
                elif total < 200:
                    potencial = "Médio"
                    status = "🟡"
                else:
                    potencial = "Baixo"
                    status = "🟠"
                
                resultados.append({
                    "produto": termo,
                    "categoria": item["categoria"],
                    "potencial": potencial,
                    "status": status,
                    "total_resultados": total,
                    "produtos_encontrados": len(produtos),
                    "pins": item.get("pins", "N/A"),
                    "crescimento": item.get("crescimento", "N/A"),
                    "tiktok": item.get("tiktok", "N/A"),
                    "evento": ", ".join([e for e in item.get("eventos", ["Geral"])])
                })
            else:
                resultados.append({
                    "produto": termo,
                    "categoria": item["categoria"],
                    "potencial": item["potencial"],
                    "status": "🟡" if item["potencial"] == "Alto" else "🟠",
                    "total_resultados": "N/A",
                    "produtos_encontrados": 0,
                    "pins": item.get("pins", "N/A"),
                    "crescimento": item.get("crescimento", "N/A"),
                    "tiktok": item.get("tiktok", "N/A"),
                    "evento": ", ".join([e for e in item.get("eventos", ["Geral"])])
                })
        else:
            resultados.append({
                "produto": termo,
                "categoria": item["categoria"],
                "potencial": item["potencial"],
                "status": "🟢" if item["potencial"] == "Alto" else "🟡" if item["potencial"] == "Médio" else "🟠",
                "total_resultados": "N/A",
                "produtos_encontrados": 0,
                "pins": item.get("pins", "N/A"),
                "crescimento": item.get("crescimento", "N/A"),
                "tiktok": item.get("tiktok", "N/A"),
                "evento": ", ".join([e for e in item.get("eventos", ["Geral"])])
            })
    
    return resultados

# ============================================================
# APP PRINCIPAL
# ============================================================
verificar_login()

google_shopping = GoogleShoppingAPI()
controle_consultas = ControleConsultas()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    status = controle_consultas.get_status()
    st.markdown("### 🔢 Consultas SerpApi Hoje")
    st.caption(f"📊 {status['usadas']} de {status['limite']} usadas")
    
    if status['restam'] > 0:
        st.success(f"✅ {status['restam']} consultas restantes")
    else:
        st.warning("⚠️ Limite de 3 consultas/dia atingido")
    
    if status['termos']:
        st.caption(f"📌 Termos: {', '.join(status['termos'])}")
    
    st.markdown("---")
    
    st.markdown("### 🔌 Status da API")
    if SERPAPI_KEY:
        st.success("✅ SerpApi configurada")
        st.caption("3 consultas automáticas/dia")
    else:
        st.warning("⚠️ SerpApi não configurada")
    
    st.markdown("---")
    
    st.markdown("### 📌 Como funciona")
    st.caption("1. Sugestões baseadas no mês atual")
    st.caption("2. 3 consultas automáticas na SerpApi")
    st.caption("3. Status visuais indicam oportunidade")

# ============================================================
# PAINEL PRINCIPAL
# ============================================================
st.title("🛒 Minerador de Produtos")
st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")

# ============================================================
# DADOS DO MES ATUAL
# ============================================================
mes_atual = datetime.now().month
dados_mes = DADOS_HISTORICOS.get(mes_atual, DADOS_HISTORICOS[1])

# Adiciona eventos aos itens
for item in dados_mes["tendencias"]:
    item["eventos"] = dados_mes["eventos"]

st.markdown(f"""
### 📊 Tendências para {datetime.now().strftime('%B').capitalize()}
**Eventos:** {', '.join(dados_mes['eventos'])} | **Sazonal:** {dados_mes['sazonal']}
""")

st.markdown("---")

# ============================================================
# ATUALIZA SUGESTOES COM SERPAPI
# ============================================================
with st.spinner("Atualizando sugestões com dados reais..."):
    sugestoes_atualizadas = atualizar_sugestoes_com_serpapi(dados_mes["tendencias"])

# ============================================================
# TABELA DE SUGESTOES (SEM COLUNA STATUS, SEM BUSCA ESPECIFICA)
# ============================================================
st.markdown("### 🎯 Sugestões de Produtos para este Mês")

# Prepara dados para tabela
dados_tabela = []
for item in sugestoes_atualizadas:
    # Define status visual
    if item["potencial"] == "Alto":
        potencial_display = "🟢 Alto"
    elif item["potencial"] == "Médio":
        potencial_display = "🟡 Médio"
    else:
        potencial_display = "🟠 Baixo"
    
    # Formata resultados
    if item["total_resultados"] != "N/A":
        resultados_str = f"{item['total_resultados']} resultados"
    else:
        resultados_str = "Histórico"
    
    dados_tabela.append({
        "Produto": item["produto"],
        "Categoria": item["categoria"],
        "Evento": item["evento"],
        "Potencial": potencial_display,
        "📌 Pinterest": f"{item['pins']} pins",
        "📈 Crescimento": item["crescimento"],
        "📱 TikTok": item["tiktok"],
        "Resultados": resultados_str,
        "Ação": f"🔍 {item['produto']}"
    })

# Cria DataFrame
df_sugestoes = pd.DataFrame(dados_tabela)

# Exibe tabela
st.dataframe(
    df_sugestoes,
    column_config={
        "Produto": "Produto",
        "Categoria": "Categoria",
        "Evento": "Evento Relacionado",
        "Potencial": "Potencial",
        "📌 Pinterest": "Pins no Pinterest",
        "📈 Crescimento": "Crescimento",
        "📱 TikTok": "Visualizações TikTok",
        "Resultados": "Resultados",
        "Ação": st.column_config.Column(
            "Buscar na Shopee",
            help="Clique para abrir a busca"
        )
    },
    use_container_width=True,
    hide_index=True
)

# Status das consultas
status = controle_consultas.get_status()
st.caption(f"📊 {status['usadas']} de {status['limite']} consultas SerpApi usadas hoje")

st.markdown("---")

# ============================================================
# LEGENDA E INSIGHTS (COM DADOS DA TABELA)
# ============================================================
st.markdown("### 📌 Legenda de Potencial")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🟢 **Alto** - Baixa concorrência, alta demanda")
    st.caption("Menos de 50 resultados no Google Shopping")

with col2:
    st.markdown("🟡 **Médio** - Concorrência moderada")
    st.caption("50-200 resultados no Google Shopping")

with col3:
    st.markdown("🟠 **Baixo** - Mercado concorrido")
    st.caption("Mais de 200 resultados no Google Shopping")

st.markdown("---")

# ============================================================
# INSIGHTS ESTRATEGICOS COM DADOS DA TABELA
# ============================================================
st.markdown("### 💡 Insights Estratégicos")

# Encontra os melhores produtos
melhores = [p for p in sugestoes_atualizadas if p["potencial"] == "Alto" and p["total_resultados"] != "N/A"]
melhores_pins = sorted(sugestoes_atualizadas, key=lambda x: int(str(x["pins"]).replace("K", "000")) if isinstance(x["pins"], str) and "K" in str(x["pins"]) else 0, reverse=True)[:2]

# Gera insights baseados nos dados
col1, col2 = st.columns(2)

with col1:
    st.info(f"""
    **🔥 Produto com Maior Potencial**
    
    **{melhores[0]['produto'] if melhores else sugestoes_atualizadas[0]['produto']}**
    - Categoria: {melhores[0]['categoria'] if melhores else sugestoes_atualizadas[0]['categoria']}
    - Pinterest: {melhores[0]['pins'] if melhores else sugestoes_atualizadas[0]['pins']} pins
    - Crescimento: {melhores[0]['crescimento'] if melhores else sugestoes_atualizadas[0]['crescimento']}
    - TikTok: {melhores[0]['tiktok'] if melhores else sugestoes_atualizadas[0]['tiktok']} visualizações
    
    **Ação:** Crie conteúdo URGENTE sobre este produto!
    """)

with col2:
    st.success(f"""
    **📈 Tendência Mais Viral**
    
    **{melhores_pins[0]['produto'] if melhores_pins else sugestoes_atualizadas[0]['produto']}**
    - {melhores_pins[0]['pins'] if melhores_pins else sugestoes_atualizadas[0]['pins']} pins no Pinterest
    - Crescimento de {melhores_pins[0]['crescimento'] if melhores_pins else sugestoes_atualizadas[0]['crescimento']}
    
    **Dica:** Produto com alto engajamento nas redes sociais.
    Aproveite o momento para criar conteúdo patrocinado!
    """)

st.markdown("---")

# ============================================================
# INSIGHT GERAL DO MES
# ============================================================
st.markdown("### 📊 Visão Geral do Mês")

st.info(f"""
**📌 {dados_mes['insight']}**

**Destaques:**
- 🔥 Produto em alta: **{sugestoes_atualizadas[0]['produto']}** ({sugestoes_atualizadas[0]['categoria']})
- 📈 Crescimento médio: {sum([int(str(p['crescimento']).replace('+', '').replace('%', '')) for p in sugestoes_atualizadas if p['crescimento'] != 'N/A'])/len([p for p in sugestoes_atualizadas if p['crescimento'] != 'N/A']):.1f}%
- 🎯 Foco principal: {dados_mes['eventos'][0]}
- 🏆 Melhor oportunidade: Produtos com status 🟢 (Alto potencial)
""")

st.markdown("---")

# ============================================================
# RODAPE
# ============================================================
st.caption(f"🛒 Minerador de Produtos v2.0 | {status['usadas']}/3 consultas SerpApi hoje")
