# ============================================================
# FUNÇÕES DE BUSCA (COM SERPER.DEV)
# ============================================================
from modules.serper import buscar_produtos_serper, buscar_total_resultados_serper

def buscar_produtos(termo, limite=3):
    """Busca produtos via Serper.dev"""
    return buscar_produtos_serper(termo, limite)

def buscar_total_resultados(termo):
    """Busca total de resultados via Serper.dev"""
    return buscar_total_resultados_serper(termo)

# E na função gerar_top10_produtos, substitua:
def gerar_top10_produtos():
    dados_completos = get_dados_completos()
    resultados = []
    
    for produto, dados in dados_completos.items():
        # Usa Serper.dev
        produtos_encontrados = buscar_produtos_serper(produto, 2)
        
        # ... resto do código

import json
import os
from datetime import datetime, timedelta
import uuid

# ============================================================
# ARQUIVOS DE DADOS
# ============================================================
ARQUIVO_LICENCAS = "licencas.json"
ARQUIVO_APOIADORES = "apoiadores.json"

# ============================================================
# CONFIGURAÇÃO DE ADMIN
# ============================================================
ADMIN_LICENCA = "ADMIN-2026-KLEBER"
LICENCA_TRIAL = "TESTE-AFILIADO-2026"

# ============================================================
# CLASSE SISTEMA DE LICENÇAS
# ============================================================
class SistemaLicencas:
    def __init__(self):
        self.arquivo = ARQUIVO_LICENCAS
        self.dados = self.carregar()
        self.validar_licencas_expiradas()
    
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
        # Licença Trial (pública)
        licencas = {
            LICENCA_TRIAL: {
                "tipo": "trial",
                "status": "ativo",
                "data_criacao": datetime.now().strftime("%Y-%m-%d"),
                "data_expiracao": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),  # 7 DIAS
                "usuario": "Usuário Trial",
                "email": "trial@email.com",
                "plano": "Trial 7 dias",
                "acessos": 0,
                "ultimo_acesso": None,
                "royalties": False,
                "repasse": False,
                "is_admin": False,
                "is_apoiador": False,
                "preco": 0
            }
        }
        
        # Licença Admin (apenas se não existir)
        admin_existe = False
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    dados_existentes = json.load(f)
                    if ADMIN_LICENCA in dados_existentes.get("licencas", {}):
                        admin_existe = True
            except:
                pass
        
        if not admin_existe:
            licencas[ADMIN_LICENCA] = {
                "tipo": "admin",
                "status": "ativo",
                "data_criacao": datetime.now().strftime("%Y-%m-%d"),
                "data_expiracao": (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d"),
                "usuario": "Administrador",
                "email": "admin@pechinchasblack.com",
                "plano": "Administrador",
                "acessos": 0,
                "ultimo_acesso": None,
                "royalties": False,
                "repasse": False,
                "is_admin": True,
                "is_apoiador": False,
                "preco": 0
            }
        
        return {
            "licencas": licencas,
            "config": {
                "proximo_id": 1001,
                "planos": {
                    "trial": {
                        "dias": 7,
                        "preco": 0,
                        "royalties": False,
                        "repasse": False,
                        "nome": "Trial 7 dias",
                        "admin_only": False,
                        "descricao": "Teste grátis por 7 dias"
                    },
                    "apoiador": {
                        "dias": 30,
                        "preco": 59.90,
                        "royalties": True,
                        "repasse": True,
                        "nome": "Apoiador",
                        "admin_only": False,
                        "descricao": "Acesso completo + royalties sobre novos membros"
                    }
                },
                "royalties": {
                    "porcentagem": 5,
                    "niveis": 3
                }
            }
        }
    
    def _admin_existe(self):
        """Verifica se a licença admin já existe"""
        return ADMIN_LICENCA in self.dados.get("licencas", {})
    
    def validar_licencas_expiradas(self):
        hoje = datetime.now().date()
        for chave, licenca in self.dados.get("licencas", {}).items():
            if licenca.get("status") == "ativo":
                try:
                    data_exp = datetime.strptime(licenca["data_expiracao"], "%Y-%m-%d").date()
                    if data_exp < hoje:
                        licenca["status"] = "expirado"
                except:
                    pass
        self.salvar()
    
    def is_admin(self, codigo):
        """Verifica se uma licença é de administrador"""
        licenca = self.dados["licencas"].get(codigo)
        if not licenca:
            return False
        return licenca.get("is_admin", False)
    
    def pode_criar_licencas(self, codigo):
        """Verifica se o usuário pode criar licenças"""
        return self.is_admin(codigo) or codigo == ADMIN_LICENCA
    
    def gerar_licenca(self, usuario, email, plano, cpf="", is_apoiador=False, criado_por=""):
        """Gera uma nova licença (apenas admin)"""
        
        config = self.dados["config"]
        plano_dados = config["planos"].get(plano)
        if not plano_dados:
            return {"erro": "Plano inválido"}
        
        # Verifica se já existe uma licença ativa para este email
        for codigo, licenca in self.dados["licencas"].items():
            if licenca.get("email") == email and licenca.get("status") == "ativo":
                return {"erro": f"Já existe uma licença ativa para {email}"}
        
        codigo = f"LIC-{config['proximo_id']}-{datetime.now().year}"
        config["proximo_id"] += 1
        
        dias = plano_dados["dias"]
        data_exp = datetime.now() + timedelta(days=dias)
        
        nova_licenca = {
            "tipo": plano,
            "status": "ativo",
            "data_criacao": datetime.now().strftime("%Y-%m-%d"),
            "data_expiracao": data_exp.strftime("%Y-%m-%d"),
            "usuario": usuario,
            "email": email,
            "plano": plano_dados["nome"],
            "acessos": 0,
            "ultimo_acesso": None,
            "royalties": plano_dados["royalties"],
            "repasse": plano_dados["repasse"],
            "cpf": cpf,
            "is_admin": False,
            "is_apoiador": is_apoiador or plano_dados["royalties"],
            "criado_por": criado_por,
            "criado_em": datetime.now().isoformat(),
            "preco": plano_dados["preco"]
        }
        
        self.dados["licencas"][codigo] = nova_licenca
        self.salvar()
        
        # Atualiza apoiadores se for plano com royalties
        if is_apoiador or plano_dados["royalties"]:
            self._atualizar_apoiadores()
        
        return {
            "codigo": codigo,
            "plano": plano_dados["nome"],
            "validade": dias,
            "data_expiracao": data_exp.strftime("%d/%m/%Y"),
            "royalties": plano_dados["royalties"],
            "repasse": plano_dados["repasse"],
            "is_apoiador": is_apoiador or plano_dados["royalties"],
            "preco": plano_dados["preco"]
        }
    
    def _atualizar_apoiadores(self):
        """Atualiza a lista de apoiadores baseado nas licenças ativas com royalties"""
        APOIADORES = {}
        
        ordem = 1
        for codigo, licenca in self.dados["licencas"].items():
            if licenca.get("status") == "ativo" and licenca.get("is_apoiador", False):
                APOIADORES[codigo] = {
                    "nome": licenca.get("usuario", "Apoiador"),
                    "ordem": ordem,
                    "email": licenca.get("email", ""),
                    "coroinha": "👑",
                    "cor": "#FFD700" if ordem == 1 else "#C0C0C0" if ordem == 2 else "#CD7F32",
                    "data_entrada": licenca.get("data_criacao", datetime.now().strftime("%Y-%m-%d")),
                    "royalties_recebidos": 0.0,
                    "repasse_ativo": True,
                    "licenca": codigo,
                    "plano": licenca.get("plano", "Apoiador")
                }
                ordem += 1
        
        with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
            json.dump(APOIADORES, f, ensure_ascii=False, indent=2)
    
    def validar_licenca(self, codigo):
        """Valida uma licença no login"""
        licenca = self.dados["licencas"].get(codigo)
        
        if not licenca:
            return {"valido": False, "motivo": "Licença não encontrada"}
        
        if licenca.get("status") != "ativo":
            return {"valido": False, "motivo": f"Licença {licenca.get('status')}"}
        
        hoje = datetime.now().date()
        try:
            data_exp = datetime.strptime(licenca["data_expiracao"], "%Y-%m-%d").date()
            if data_exp < hoje:
                licenca["status"] = "expirado"
                self.salvar()
                return {"valido": False, "motivo": "Licença expirada"}
        except:
            pass
        
        licenca["acessos"] = licenca.get("acessos", 0) + 1
        licenca["ultimo_acesso"] = datetime.now().isoformat()
        self.salvar()
        
        return {
            "valido": True,
            "usuario": licenca.get("usuario"),
            "plano": licenca.get("plano"),
            "data_expiracao": licenca["data_expiracao"],
            "royalties": licenca.get("royalties", False),
            "repasse": licenca.get("repasse", False),
            "acessos": licenca.get("acessos", 0),
            "is_apoiador": licenca.get("is_apoiador", False),
            "is_admin": licenca.get("is_admin", False),
            "preco": licenca.get("preco", 0)
        }
    
    def listar_licencas(self, apenas_ativas=False):
        """Lista todas as licenças"""
        licencas = []
        for codigo, dados in self.dados["licencas"].items():
            if apenas_ativas and dados.get("status") != "ativo":
                continue
            licencas.append({
                "codigo": codigo,
                "usuario": dados.get("usuario", ""),
                "email": dados.get("email", ""),
                "plano": dados.get("plano", ""),
                "status": dados.get("status", ""),
                "criacao": dados.get("data_criacao", ""),
                "expiracao": dados.get("data_expiracao", ""),
                "acessos": dados.get("acessos", 0),
                "royalties": dados.get("royalties", False),
                "is_apoiador": dados.get("is_apoiador", False),
                "is_admin": dados.get("is_admin", False),
                "preco": dados.get("preco", 0)
            })
        return sorted(licencas, key=lambda x: x["criacao"], reverse=True)
    
    def renovar_licenca(self, codigo, dias=30):
        """Renova uma licença existente"""
        licenca = self.dados["licencas"].get(codigo)
        if not licenca:
            return {"erro": "Licença não encontrada"}
        
        try:
            data_atual = datetime.strptime(licenca["data_expiracao"], "%Y-%m-%d").date()
            nova_data = data_atual + timedelta(days=dias)
            licenca["data_expiracao"] = nova_data.strftime("%Y-%m-%d")
            licenca["status"] = "ativo"
            
            self.salvar()
            return {
                "nova_expiracao": nova_data.strftime("%d/%m/%Y"),
                "dias_adicionados": dias
            }
        except:
            return {"erro": "Erro ao renovar licença"}
    
    def revogar_licenca(self, codigo):
        """Revoga uma licença"""
        licenca = self.dados["licencas"].get(codigo)
        if not licenca:
            return {"erro": "Licença não encontrada"}
        
        # Não permite revogar a licença admin
        if codigo == ADMIN_LICENCA:
            return {"erro": "Não é possível revogar a licença de administrador"}
        
        licenca["status"] = "revogado"
        self.salvar()
        self._atualizar_apoiadores()
        return {"sucesso": True, "codigo": codigo}
    
    def obter_estatisticas(self):
        """Retorna estatísticas do sistema de licenças"""
        licencas = self.dados["licencas"]
        total = len(licencas)
        ativas = sum(1 for l in licencas.values() if l.get("status") == "ativo")
        expiradas = sum(1 for l in licencas.values() if l.get("status") == "expirado")
        revogadas = sum(1 for l in licencas.values() if l.get("status") == "revogado")
        
        receita = 0
        for l in licencas.values():
            if l.get("status") == "ativo":
                receita += l.get("preco", 0)
        
        return {
            "total": total,
            "ativas": ativas,
            "expiradas": expiradas,
            "revogadas": revogadas,
            "receita_mensal": receita,
            "royalties_pagos": 0
        }


# ============================================================
# CARREGAR APOIADORES
# ============================================================
def carregar_apoiadores():
    """Carrega a lista de apoiadores do arquivo"""
    if os.path.exists(ARQUIVO_APOIADORES):
        try:
            with open(ARQUIVO_APOIADORES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Se não existir, cria a partir do sistema de licenças
    sistema = SistemaLicencas()
    sistema._atualizar_apoiadores()
    
    if os.path.exists(ARQUIVO_APOIADORES):
        try:
            with open(ARQUIVO_APOIADORES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    return {}

# ============================================================
# EXPORTAÇÕES
# ============================================================
__all__ = [
    'SistemaLicencas',
    'carregar_apoiadores',
    'ADMIN_LICENCA',
    'LICENCA_TRIAL',
    'ARQUIVO_LICENCAS',
    'ARQUIVO_APOIADORES'
]
