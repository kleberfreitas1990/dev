import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)

# ============================================================
# VALIDAÇÃO DE TERMOS DE BUSCA
# ============================================================
def validar_termo_busca(termo: str) -> Optional[str]:
    if not termo:
        return None
    
    termo = termo.strip()
    termo = re.sub(r'[<>{}|\\^~\[\]`]', '', termo)
    termo = re.sub(r'\s+', ' ', termo)
    
    if len(termo) > 100:
        termo = termo[:100]
    
    if len(termo) < 2:
        return None
    
    return termo

def validar_lista_termos(termos: List[str]) -> List[str]:
    validos = []
    for termo in termos:
        termo_validado = validar_termo_busca(termo)
        if termo_validado:
            validos.append(termo_validado)
    
    vistos = set()
    validos_unicos = []
    for item in validos:
        if item.lower() not in vistos:
            vistos.add(item.lower())
            validos_unicos.append(item)
    
    return validos_unicos

# ============================================================
# VALIDAÇÃO DE PRODUTOS (SERPER)
# ============================================================
def validar_produto_serper(produto: Dict[str, Any]) -> Dict[str, Any]:
    if not produto or not isinstance(produto, dict):
        return None
    
    resultado = {}
    
    nome = produto.get("nome", "").strip()
    if not nome or len(nome) < 2:
        return None
    
    nome = re.sub(r'[<>{}|\\^~\[\]`]', '', nome)
    resultado["nome"] = nome[:200]
    
    preco = produto.get("preco", "R$ 0")
    if preco:
        preco_limpo = re.sub(r'[^0-9.,]', '', preco)
        if preco_limpo:
            try:
                preco_limpo = preco_limpo.replace(',', '.')
                preco_valor = float(preco_limpo)
                resultado["preco"] = f"R$ {preco_valor:.2f}"
            except ValueError:
                resultado["preco"] = preco
        else:
            resultado["preco"] = "R$ 0"
    else:
        resultado["preco"] = "R$ 0"
    
    loja = produto.get("loja", "").strip()
    if loja:
        loja = re.sub(r'[<>{}|\\^~\[\]`]', '', loja)
        resultado["loja"] = loja[:100]
    else:
        resultado["loja"] = "Desconhecido"
    
    link = produto.get("link", "")
    if link:
        if not link.startswith(('http://', 'https://')):
            link = f"https://{link}"
        link = re.sub(r'[<>{}|\\^~\[\]`]', '', link)
        resultado["link"] = link
    else:
        resultado["link"] = ""
    
    avaliacao = produto.get("avaliacao")
    if avaliacao is not None:
        try:
            avaliacao = float(avaliacao)
            if 0 <= avaliacao <= 5:
                resultado["avaliacao"] = round(avaliacao, 1)
            else:
                resultado["avaliacao"] = None
        except:
            resultado["avaliacao"] = None
    else:
        resultado["avaliacao"] = None
    
    return resultado

def validar_produtos_serper(produtos: List[Dict]) -> List[Dict]:
    validos = []
    for produto in produtos:
        produto_validado = validar_produto_serper(produto)
        if produto_validado:
            validos.append(produto_validado)
    return validos

# ============================================================
# VALIDAÇÃO DE APOIADORES
# ============================================================
def validar_apoiador(dados: Dict[str, Any]) -> Dict[str, Any]:
    if not dados or not isinstance(dados, dict):
        return None
    
    resultado = {}
    
    nome = dados.get("nome", "").strip()
    if not nome or len(nome) < 2:
        return None
    nome = re.sub(r'[<>{}|\\^~\[\]`]', '', nome)
    resultado["nome"] = nome[:100]
    
    email = dados.get("email", "").strip().lower()
    if email:
        padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(padrao_email, email):
            resultado["email"] = email[:100]
        else:
            return None
    else:
        return None
    
    ordem = dados.get("ordem")
    if ordem is not None:
        try:
            ordem = int(ordem)
            if ordem < 1:
                ordem = 1
            resultado["ordem"] = ordem
        except:
            resultado["ordem"] = 999
    else:
        resultado["ordem"] = 999
    
    coroinha = dados.get("coroinha", "👑")
    if not coroinha or len(coroinha) > 10:
        coroinha = "👑"
    resultado["coroinha"] = coroinha
    
    cor = dados.get("cor", "#FF6B6B")
    if cor and not re.match(r'^#[0-9A-Fa-f]{6}$', cor):
        cor = "#FF6B6B"
    resultado["cor"] = cor
    
    data_entrada = dados.get("data_entrada")
    if data_entrada:
        try:
            datetime.strptime(data_entrada, "%Y-%m-%d")
            resultado["data_entrada"] = data_entrada
        except:
            resultado["data_entrada"] = datetime.now().strftime("%Y-%m-%d")
    else:
        resultado["data_entrada"] = datetime.now().strftime("%Y-%m-%d")
    
    royalties = dados.get("royalties_recebidos", 0.0)
    try:
        royalties = float(royalties)
        if royalties < 0:
            royalties = 0.0
        resultado["royalties_recebidos"] = royalties
    except:
        resultado["royalties_recebidos"] = 0.0
    
    repasse_ativo = dados.get("repasse_ativo", True)
    if isinstance(repasse_ativo, str):
        repasse_ativo = repasse_ativo.lower() in ["true", "1", "yes", "sim", "ativo"]
    resultado["repasse_ativo"] = bool(repasse_ativo)
    
    plano = dados.get("plano", "Apoiador")
    planos_validos = ["Fundador", "Fundadora", "Apoiador", "Premium", "Trial"]
    if plano not in planos_validos:
        plano = "Apoiador"
    resultado["plano"] = plano
    
    return resultado

def validar_apoiadores(lista: Dict[str, Any]) -> Dict[str, Any]:
    validados = {}
    for key, dados in lista.items():
        dados_validados = validar_apoiador(dados)
        if dados_validados:
            validados[key] = dados_validados
    return validados

# ============================================================
# VALIDAÇÃO DE LICENÇAS
# ============================================================
def validar_codigo_licenca(codigo: str) -> bool:
    if not codigo:
        return False
    codigo = codigo.strip()
    if codigo == "ADMIN-2026-KLEBER":
        return True
    if codigo == "TESTE-AFILIADO-2026":
        return True
    if re.match(r'^LIC-[A-Z0-9]{8}$', codigo):
        return True
    return False

def validar_dados_licenca(dados: Dict[str, Any]) -> Dict[str, Any]:
    if not dados or not isinstance(dados, dict):
        return None
    
    resultado = {}
    
    tipo = dados.get("tipo", "basico")
    tipos_validos = ["trial", "admin", "apoiador", "basico"]
    if tipo not in tipos_validos:
        tipo = "basico"
    resultado["tipo"] = tipo
    
    status = dados.get("status", "ativo")
    status_validos = ["ativo", "inativo", "revogado", "expirado"]
    if status not in status_validos:
        status = "ativo"
    resultado["status"] = status
    
    usuario = dados.get("usuario", "").strip()
    if usuario:
        usuario = re.sub(r'[<>{}|\\^~\[\]`]', '', usuario)
        resultado["usuario"] = usuario[:100]
    else:
        resultado["usuario"] = "Usuário"
    
    email = dados.get("email", "").strip().lower()
    if email:
        padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(padrao_email, email):
            resultado["email"] = email[:100]
        else:
            resultado["email"] = ""
    else:
        resultado["email"] = ""
    
    resultado["plano"] = dados.get("plano", "Básico")[:50]
    resultado["is_admin"] = bool(dados.get("is_admin", False))
    resultado["is_apoiador"] = bool(dados.get("is_apoiador", False))
    
    data_criacao = dados.get("data_criacao")
    if data_criacao:
        try:
            datetime.strptime(data_criacao, "%Y-%m-%d")
            resultado["data_criacao"] = data_criacao
        except:
            resultado["data_criacao"] = datetime.now().strftime("%Y-%m-%d")
    else:
        resultado["data_criacao"] = datetime.now().strftime("%Y-%m-%d")
    
    return resultado

# ============================================================
# VALIDAÇÃO DE CACHE
# ============================================================
def validar_cache_dados(dados: Dict[str, Any], chave: str = None) -> bool:
    if not dados or not isinstance(dados, dict):
        return False
    
    data_cache = dados.get("data")
    if data_cache:
        try:
            data_cache_dt = datetime.strptime(data_cache, "%Y-%m-%d").date()
            hoje = datetime.now().date()
            if (hoje - data_cache_dt).days > 7:
                return False
        except:
            return False
    else:
        return False
    
    resultados = dados.get("resultados", dados.get("termos", []))
    if not resultados:
        return False
    
    if not isinstance(resultados, list):
        return False
    
    if len(resultados) < 1:
        return False
    
    return True

# ============================================================
# SANITIZAÇÃO
# ============================================================
def sanitizar_texto(texto: str, max_len: int = 500) -> str:
    if not texto:
        return ""
    texto = texto.strip()
    texto = re.sub(r'[<>{}|\\^~\[\]`]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    if len(texto) > max_len:
        texto = texto[:max_len]
    return texto

def sanitizar_json(dados: Dict) -> Dict:
    if not dados:
        return {}
    
    resultado = {}
    for key, value in dados.items():
        key = sanitizar_texto(key, max_len=50)
        if isinstance(value, str):
            resultado[key] = sanitizar_texto(value)
        elif isinstance(value, (int, float, bool)):
            resultado[key] = value
        elif isinstance(value, list):
            resultado[key] = [
                sanitizar_texto(item) if isinstance(item, str) else item
                for item in value
            ]
        elif isinstance(value, dict):
            resultado[key] = sanitizar_json(value)
        else:
            resultado[key] = str(value)
    
    return resultado

__all__ = [
    'validar_termo_busca',
    'validar_lista_termos',
    'validar_produto_serper',
    'validar_produtos_serper',
    'validar_apoiador',
    'validar_apoiadores',
    'validar_codigo_licenca',
    'validar_dados_licenca',
    'validar_cache_dados',
    'sanitizar_texto',
    'sanitizar_json'
]
