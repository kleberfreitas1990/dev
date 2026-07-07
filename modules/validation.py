"""
Módulo de Validação e Sanitização de Dados
Responsável por validar entradas, saídas e dados de APIs
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================
logger = logging.getLogger(__name__)

# ============================================================
# VALIDAÇÃO DE TERMOS DE BUSCA
# ============================================================
def validar_termo_busca(termo: str) -> Optional[str]:
    """
    Valida e sanitiza um termo de busca
    
    Args:
        termo (str): Termo de busca bruto
        
    Returns:
        Optional[str]: Termo sanitizado ou None se inválido
    """
    if not termo:
        return None
    
    # Remove espaços extras
    termo = termo.strip()
    
    # Remove caracteres especiais perigosos
    termo = re.sub(r'[<>{}|\\^~\[\]`]', '', termo)
    
    # Remove múltiplos espaços
    termo = re.sub(r'\s+', ' ', termo)
    
    # Limita tamanho (evita termos muito longos)
    if len(termo) > 100:
        termo = termo[:100]
        logger.warning(f"Termo de busca truncado para 100 caracteres")
    
    # Verifica se tem pelo menos 2 caracteres válidos
    if len(termo) < 2:
        return None
    
    # Verifica se não é apenas números
    if termo.isdigit():
        logger.warning(f"Termo de busca contém apenas números: {termo}")
        return termo  # Pode ser um código de produto
    
    return termo

def validar_lista_termos(termos: List[str]) -> List[str]:
    """
    Valida uma lista de termos de busca
    
    Args:
        termos (List[str]): Lista de termos brutos
        
    Returns:
        List[str]: Lista de termos válidos
    """
    validos = []
    for termo in termos:
        termo_validado = validar_termo_busca(termo)
        if termo_validado:
            validos.append(termo_validado)
    
    # Remove duplicatas mantendo ordem
    vistos = set()
    validos_unicos = []
    for item in validos:
        if item.lower() not in vistos:
            vistos.add(item.lower())
            validos_unicos.append(item)
    
    logger.info(f"Validação de termos: {len(termos)} → {len(validos_unicos)} válidos")
    return validos_unicos

# ============================================================
# VALIDAÇÃO DE PRODUTOS (SERPER/API)
# ============================================================
def validar_produto_serper(produto: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida e sanitiza dados de produto do Serper.dev
    
    Args:
        produto (Dict): Dados brutos do produto
        
    Returns:
        Dict: Dados validados e sanitizados
    """
    if not produto or not isinstance(produto, dict):
        return None
    
    resultado = {}
    
    # Nome do produto (obrigatório)
    nome = produto.get("nome", "").strip()
    if not nome or len(nome) < 2:
        logger.warning(f"Produto com nome inválido: {nome}")
        return None
    
    # Remove caracteres especiais do nome
    nome = re.sub(r'[<>{}|\\^~\[\]`]', '', nome)
    resultado["nome"] = nome[:200]  # Limita tamanho
    
    # Preço (pode vir em vários formatos)
    preco = produto.get("preco", "R$ 0")
    if preco:
        # Tenta extrair valor numérico do preço
        preco_limpo = re.sub(r'[^0-9.,]', '', preco)
        if preco_limpo:
            try:
                # Converte para float se possível
                preco_limpo = preco_limpo.replace(',', '.')
                preco_valor = float(preco_limpo)
                resultado["preco"] = f"R$ {preco_valor:.2f}"
            except ValueError:
                resultado["preco"] = preco
        else:
            resultado["preco"] = "R$ 0"
    else:
        resultado["preco"] = "R$ 0"
    
    # Loja/Fornecedor
    loja = produto.get("loja", "").strip()
    if loja:
        loja = re.sub(r'[<>{}|\\^~\[\]`]', '', loja)
        resultado["loja"] = loja[:100]
    else:
        resultado["loja"] = "Desconhecido"
    
    # Link (URL)
    link = produto.get("link", "")
    if link:
        # Verifica se é uma URL válida
        if not link.startswith(('http://', 'https://')):
            link = f"https://{link}"
        
        # Remove caracteres perigosos
        link = re.sub(r'[<>{}|\\^~\[\]`]', '', link)
        
        # Verifica se contém domínio válido
        if re.match(r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}', link):
            resultado["link"] = link
        else:
            logger.warning(f"Link inválido: {link}")
            resultado["link"] = ""
    else:
        resultado["link"] = ""
    
    # Avaliação (rating)
    avaliacao = produto.get("avaliacao")
    if avaliacao is not None:
        try:
            avaliacao = float(avaliacao)
            if 0 <= avaliacao <= 5:
                resultado["avaliacao"] = round(avaliacao, 1)
            else:
                logger.warning(f"Avaliação fora do range: {avaliacao}")
                resultado["avaliacao"] = None
        except (ValueError, TypeError):
            resultado["avaliacao"] = None
    else:
        resultado["avaliacao"] = None
    
    return resultado

def validar_produtos_serper(produtos: List[Dict]) -> List[Dict]:
    """
    Valida lista de produtos do Serper
    
    Args:
        produtos (List[Dict]): Lista de produtos brutos
        
    Returns:
        List[Dict]: Lista de produtos validados
    """
    validos = []
    for produto in produtos:
        produto_validado = validar_produto_serper(produto)
        if produto_validado:
            validos.append(produto_validado)
    
    logger.info(f"Validação de produtos: {len(produtos)} → {len(validos)} válidos")
    return validos

# ============================================================
# VALIDAÇÃO DE APOIADORES
# ============================================================
def validar_apoiador(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida dados de um apoiador
    
    Args:
        dados (Dict): Dados do apoiador
        
    Returns:
        Dict: Dados validados ou None se inválido
    """
    if not dados or not isinstance(dados, dict):
        return None
    
    resultado = {}
    
    # Nome (obrigatório)
    nome = dados.get("nome", "").strip()
    if not nome or len(nome) < 2:
        logger.warning(f"Nome de apoiador inválido: {nome}")
        return None
    
    # Remove caracteres especiais
    nome = re.sub(r'[<>{}|\\^~\[\]`]', '', nome)
    resultado["nome"] = nome[:100]
    
    # Email (obrigatório)
    email = dados.get("email", "").strip().lower()
    if email:
        # Valida formato de email
        padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(padrao_email, email):
            resultado["email"] = email[:100]
        else:
            logger.warning(f"Email inválido: {email}")
            return None
    else:
        logger.warning("Email do apoiador não informado")
        return None
    
    # Ordem (número)
    ordem = dados.get("ordem")
    if ordem is not None:
        try:
            ordem = int(ordem)
            if ordem < 1:
                logger.warning(f"Ordem inválida: {ordem}, ajustando para 1")
                ordem = 1
            resultado["ordem"] = ordem
        except (ValueError, TypeError):
            resultado["ordem"] = 999
    else:
        resultado["ordem"] = 999
    
    # Coroinha (emote)
    coroinha = dados.get("coroinha", "👑")
    if not coroinha or len(coroinha) > 10:
        coroinha = "👑"
    resultado["coroinha"] = coroinha
    
    # Cor (hexadecimal)
    cor = dados.get("cor", "#FF6B6B")
    if cor and not re.match(r'^#[0-9A-Fa-f]{6}$', cor):
        logger.warning(f"Cor inválida: {cor}, usando padrão")
        cor = "#FF6B6B"
    resultado["cor"] = cor
    
    # Data de entrada
    data_entrada = dados.get("data_entrada")
    if data_entrada:
        try:
            datetime.strptime(data_entrada, "%Y-%m-%d")
            resultado["data_entrada"] = data_entrada
        except ValueError:
            logger.warning(f"Data inválida: {data_entrada}, usando hoje")
            resultado["data_entrada"] = datetime.now().strftime("%Y-%m-%d")
    else:
        resultado["data_entrada"] = datetime.now().strftime("%Y-%m-%d")
    
    # Royalties
    royalties = dados.get("royalties_recebidos", 0.0)
    try:
        royalties = float(royalties)
        if royalties < 0:
            royalties = 0.0
        resultado["royalties_recebidos"] = royalties
    except (ValueError, TypeError):
        resultado["royalties_recebidos"] = 0.0
    
    # Repasse ativo (boolean)
    repasse_ativo = dados.get("repasse_ativo", True)
    if isinstance(repasse_ativo, str):
        repasse_ativo = repasse_ativo.lower() in ["true", "1", "yes", "sim", "ativo"]
    resultado["repasse_ativo"] = bool(repasse_ativo)
    
    # Plano
    plano = dados.get("plano", "Apoiador")
    planos_validos = ["Fundador", "Fundadora", "Apoiador", "Premium", "Trial"]
    if plano not in planos_validos:
        logger.warning(f"Plano inválido: {plano}, usando 'Apoiador'")
        plano = "Apoiador"
    resultado["plano"] = plano
    
    return resultado

def validar_apoiadores(lista: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida todos os apoiadores
    
    Args:
        lista (Dict): Dicionário de apoiadores
        
    Returns:
        Dict: Dicionário de apoiadores validados
    """
    validados = {}
    for key, dados in lista.items():
        dados_validados = validar_apoiador(dados)
        if dados_validados:
            validados[key] = dados_validados
    
    logger.info(f"Validação de apoiadores: {len(lista)} → {len(validados)} válidos")
    return validados

# ============================================================
# VALIDAÇÃO DE LICENÇAS
# ============================================================
def validar_codigo_licenca(codigo: str) -> bool:
    """
    Valida o formato de um código de licença
    
    Args:
        codigo (str): Código da licença
        
    Returns:
        bool: True se válido
    """
    if not codigo:
        return False
    
    codigo = codigo.strip()
    
    # Admin license
    if codigo == "ADMIN-2026-KLEBER":
        return True
    
    # Trial license
    if codigo == "TESTE-AFILIADO-2026":
        return True
    
    # Licenças geradas (formato: LIC-XXXXXXXX)
    if re.match(r'^LIC-[A-Z0-9]{8}$', codigo):
        return True
    
    logger.warning(f"Código de licença com formato inválido: {codigo[:10]}...")
    return False

def validar_dados_licenca(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida dados de uma licença
    
    Args:
        dados (Dict): Dados da licença
        
    Returns:
        Dict: Dados validados
    """
    if not dados or not isinstance(dados, dict):
        return None
    
    resultado = {}
    
    # Tipo
    tipo = dados.get("tipo", "basico")
    tipos_validos = ["trial", "admin", "apoiador", "basico"]
    if tipo not in tipos_validos:
        logger.warning(f"Tipo inválido: {tipo}, usando 'basico'")
        tipo = "basico"
    resultado["tipo"] = tipo
    
    # Status
    status = dados.get("status", "ativo")
    status_validos = ["ativo", "inativo", "revogado", "expirado"]
    if status not in status_validos:
        logger.warning(f"Status inválido: {status}, usando 'ativo'")
        status = "ativo"
    resultado["status"] = status
    
    # Usuário
    usuario = dados.get("usuario", "").strip()
    if usuario:
        usuario = re.sub(r'[<>{}|\\^~\[\]`]', '', usuario)
        resultado["usuario"] = usuario[:100]
    else:
        resultado["usuario"] = "Usuário"
    
    # Email
    email = dados.get("email", "").strip().lower()
    if email:
        padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(padrao_email, email):
            resultado["email"] = email[:100]
        else:
            logger.warning(f"Email inválido na licença: {email}")
            resultado["email"] = ""
    else:
        resultado["email"] = ""
    
    # Plano
    plano = dados.get("plano", "Básico")
    resultado["plano"] = plano[:50]
    
    # Flags
    resultado["is_admin"] = bool(dados.get("is_admin", False))
    resultado["is_apoiador"] = bool(dados.get("is_apoiador", False))
    
    # Data de criação
    data_criacao = dados.get("data_criacao")
    if data_criacao:
        try:
            datetime.strptime(data_criacao, "%Y-%m-%d")
            resultado["data_criacao"] = data_criacao
        except ValueError:
            resultado["data_criacao"] = datetime.now().strftime("%Y-%m-%d")
    else:
        resultado["data_criacao"] = datetime.now().strftime("%Y-%m-%d")
    
    return resultado

# ============================================================
# VALIDAÇÃO DE CACHE
# ============================================================
def validar_cache_dados(dados: Dict[str, Any], chave: str = None) -> bool:
    """
    Valida se os dados do cache estão íntegros
    
    Args:
        dados (Dict): Dados do cache
        chave (str): Chave opcional para verificar
        
    Returns:
        bool: True se o cache é válido
    """
    if not dados or not isinstance(dados, dict):
        return False
    
    # Verifica data do cache
    data_cache = dados.get("data")
    if data_cache:
        try:
            data_cache_dt = datetime.strptime(data_cache, "%Y-%m-%d").date()
            hoje = datetime.now().date()
            
            # Se o cache tem mais de 7 dias, considera inválido
            if (hoje - data_cache_dt).days > 7:
                logger.info(f"Cache expirado: {data_cache} (há {(hoje - data_cache_dt).days} dias)")
                return False
        except ValueError:
            logger.warning("Data do cache em formato inválido")
            return False
    else:
        logger.warning("Cache sem data")
        return False
    
    # Verifica se tem resultados
    resultados = dados.get("resultados", dados.get("termos", []))
    if not resultados:
        logger.info("Cache vazio")
        return False
    
    # Verifica se é uma lista
    if not isinstance(resultados, list):
        logger.warning("Cache com formato inválido (não é lista)")
        return False
    
    # Verifica se tem pelo menos 1 item
    if len(resultados) < 1:
        logger.info("Cache com menos de 1 item")
        return False
    
    return True

# ============================================================
# SANITIZAÇÃO GERAL
# ============================================================
def sanitizar_texto(texto: str, max_len: int = 500) -> str:
    """
    Sanitiza texto removendo caracteres especiais
    
    Args:
        texto (str): Texto bruto
        max_len (int): Tamanho máximo
        
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    texto = texto.strip()
    texto = re.sub(r'[<>{}|\\^~\[\]`]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    
    if len(texto) > max_len:
        texto = texto[:max_len]
    
    return texto

def sanitizar_json(dados: Dict) -> Dict:
    """
    Sanitiza um dicionário para JSON seguro
    
    Args:
        dados (Dict): Dicionário bruto
        
    Returns:
        Dict: Dicionário sanitizado
    """
    if not dados:
        return {}
    
    resultado = {}
    for key, value in dados.items():
        # Sanitiza chave
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

# ============================================================
# EXPORTAÇÕES
# ============================================================
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
