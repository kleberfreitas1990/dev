"""
adult_content_filter.py — Filtro de Conteúdo Adulto para Tendências
=====================================================================

Módulo responsável por filtrar termos de conteúdo adulto, sensível ou NSFW
de todas as fontes de tendências (Shopee, Google Trends, etc).

Versão: 1.0.0
Autor: Manus AI
Data: 2026-08-11
"""

import logging
import unicodedata
from typing import List, Set, Optional

logger = logging.getLogger(__name__)

# ============================================================
# BLACKLIST DE CONTEÚDO ADULTO E SENSÍVEL
# ============================================================
# Expandida progressivamente conforme necessário
BLACKLIST_ADULTO = {
    # Produtos sexuais
    "consolo", "dildo", "vibrador", "boneco sexual", "pênis de borracha",
    "penis de borracha", "extensor peniano", "extensor penis", "pênis", "penis",
    "órgão sexual", "orgao sexual", "masturbador", "masturbação", "masturbacao",
    "vibrador feminino", "vibrador masculino", "plug anal", "vibrador anal",
    "vibrador de próstata", "strap-on", "cinto de castidade", "vibrador de língua",
    
    # Conteúdo sexual explícito
    "pornô", "pornografia", "conteúdo adulto", "conteúdo sexual",
    "filme adulto", "vídeo adulto", "sexo", "erótico", "erótica",
    "nudez", "nua", "nu", "pelada", "pelado",
    
    # Drogas e substâncias ilícitas
    "cocaína", "maconha", "heroína", "crack", "metanfetamina",
    "lsd", "ecstasy", "mdma", "anfetamina", "drogas",
    "substância controlada", "entorpecente",
    
    # Armas e explosivos
    "arma de fogo", "pistola", "revólver", "metralhadora",
    "explosivo", "bomba", "dinamite", "artefato explosivo",
    "arma branca", "faca de combate", "arma ilegal",
    
    # Falsificações e contrabando
    "falsificado", "réplica não-autorizada", "contrabando",
    "produto roubado", "mercadoria ilegal",
    
    # Conteúdo de ódio e discriminação
    "racismo", "racista", "nazismo", "nazista",
    "homofobia", "homofóbico", "transfobia", "transfóbico",
    "xenofobia", "xenofóbico", "antissemita", "antissemitismo",
    
    # Violência extrema
    "snuff", "gore", "violência extrema", "tortura",
    
    # Outros (conforme necessário)
    "serviço sexual", "prostituição", "acompanhante",
}

# Variações e aliases comuns
BLACKLIST_VARIAÇÕES = {
    # Consolo
    "consolador", "consoladores",
    # Boneco
    "boneca sexual", "boneco de silicone", "boneca de silicone",
    # Vibrador
    "vibrador de clitóris", "vibrador externo",
    # Genérico
    "brinquedo sexual", "brinquedos sexuais", "brinquedo sexual masculino",
    "brinquedo sexual feminino", "masturbador masculino", "masturbador feminino",
    "sex toy", "sex toys", "artigo adulto", "artigos adultos",
}

# Combinar ambas as listas
BLACKLIST_COMPLETA = BLACKLIST_ADULTO | BLACKLIST_VARIAÇÕES

# ============================================================
# FUNÇÕES DE FILTRO
# ============================================================

def normalizar_termo(termo: str) -> str:
    """
    Normaliza um termo para comparação com blacklist.
    - Lowercase
    - Remove espaços extras
    - Remove acentos (opcional, para compatibilidade)
    """
    if not termo:
        return ""
    
    termo = termo.lower().strip()
    termo = "".join(
        caractere for caractere in unicodedata.normalize("NFKD", termo)
        if not unicodedata.combining(caractere)
    )
    
    # Remover múltiplos espaços
    while "  " in termo:
        termo = termo.replace("  ", " ")
    
    return termo


def eh_termo_adulto(termo: str) -> bool:
    """
    Verifica se um termo está na blacklist de conteúdo adulto.
    
    Retorna True se o termo deve ser filtrado.
    """
    if not termo:
        return False
    
    termo_normalizado = normalizar_termo(termo)
    blacklist_normalizada = {normalizar_termo(item) for item in BLACKLIST_COMPLETA}

    # Verificação exata
    if termo_normalizado in blacklist_normalizada:
        return True

    # Verificação parcial (substring)
    for termo_bloqueado in blacklist_normalizada:
        if termo_bloqueado in termo_normalizado or termo_normalizado in termo_bloqueado:
            # Evitar falsos positivos: só bloquear se for match significativo
            if len(termo_normalizado) > 3 and len(termo_bloqueado) > 3:
                if termo_bloqueado in termo_normalizado:
                    return True
    
    return False


def filtrar_termo(termo: str) -> Optional[str]:
    """
    Filtra um termo individual.
    
    Retorna:
    - O termo se for válido
    - None se for conteúdo adulto
    """
    if not termo or not isinstance(termo, str):
        return None
    
    termo = termo.strip()
    
    if eh_termo_adulto(termo):
        logger.warning(f"🚫 Termo bloqueado (adulto): {termo}")
        return None
    
    return termo


def filtrar_lista_termos(termos: List[str]) -> List[str]:
    """
    Filtra uma lista de termos removendo conteúdo adulto.
    
    Retorna lista de termos válidos.
    """
    if not termos:
        return []
    
    termos_filtrados = []
    termos_bloqueados = []
    
    for termo in termos:
        termo_limpo = filtrar_termo(termo)
        if termo_limpo:
            termos_filtrados.append(termo_limpo)
        else:
            termos_bloqueados.append(termo)
    
    if termos_bloqueados:
        logger.info(f"🚫 {len(termos_bloqueados)} termo(s) bloqueado(s): {termos_bloqueados}")
    
    logger.info(f"✅ {len(termos_filtrados)} termo(s) válido(s) após filtro")
    
    return termos_filtrados


def obter_estatisticas_filtro(termos_originais: List[str]) -> dict:
    """
    Retorna estatísticas sobre o filtro aplicado.
    """
    termos_filtrados = filtrar_lista_termos(termos_originais)
    termos_bloqueados = [t for t in termos_originais if t not in termos_filtrados]
    
    return {
        "total_original": len(termos_originais),
        "total_filtrado": len(termos_filtrados),
        "total_bloqueado": len(termos_bloqueados),
        "taxa_bloqueio": round(len(termos_bloqueados) / len(termos_originais) * 100, 2) if termos_originais else 0,
        "termos_bloqueados": termos_bloqueados,
    }


def expandir_blacklist(novos_termos: Set[str]) -> None:
    """
    Expande a blacklist com novos termos.
    
    NOTA: Modifica o estado global. Use com cuidado.
    """
    global BLACKLIST_COMPLETA
    
    novos_termos_normalizados = {normalizar_termo(t) for t in novos_termos if t}
    BLACKLIST_COMPLETA.update(novos_termos_normalizados)
    
    logger.info(f"📝 Blacklist expandida com {len(novos_termos_normalizados)} novo(s) termo(s)")


# ============================================================
# TESTES BÁSICOS
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Teste 1: Termos adultos
    print("=== Teste 1: Detecção de Termos Adultos ===")
    termos_teste = ["Consolo", "iPhone", "Boneco Sexual", "PS5", "Vibrador"]
    for termo in termos_teste:
        bloqueado = eh_termo_adulto(termo)
        print(f"  {termo}: {'🚫 BLOQUEADO' if bloqueado else '✅ OK'}")
    
    # Teste 2: Filtro de lista
    print("\n=== Teste 2: Filtro de Lista ===")
    lista_teste = ["Consolo", "Moto Elétrica Scooter", "Boneco Sexual", "iPhone", "Vibrador"]
    resultado = filtrar_lista_termos(lista_teste)
    print(f"  Original: {lista_teste}")
    print(f"  Filtrado: {resultado}")
    
    # Teste 3: Estatísticas
    print("\n=== Teste 3: Estatísticas ===")
    stats = obter_estatisticas_filtro(lista_teste)
    print(f"  Total original: {stats['total_original']}")
    print(f"  Total filtrado: {stats['total_filtrado']}")
    print(f"  Total bloqueado: {stats['total_bloqueado']}")
    print(f"  Taxa de bloqueio: {stats['taxa_bloqueio']}%")
