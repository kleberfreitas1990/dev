# Adicione estas funções ao final do arquivo, antes dos exports

def remover_apoiador(id_apoiador):
    """Remove um apoiador pelo ID e reorganiza as ordens"""
    apoiadores = carregar_apoiadores()
    
    if id_apoiador not in apoiadores:
        return False
    
    # Remove o apoiador
    del apoiadores[id_apoiador]
    
    # Reorganiza as ordens
    ordem = 1
    for key in sorted(apoiadores.keys(), key=lambda x: apoiadores[x].get("ordem", 999)):
        apoiadores[key]["ordem"] = ordem
        ordem += 1
    
    with open(ARQUIVO_APOIADORES, 'w', encoding='utf-8') as f:
        json.dump(apoiadores, f, ensure_ascii=False, indent=2)
    
    return True

# No SistemaLicencas, adicione o método:
def revogar_licenca_por_usuario(self, nome_usuario):
    """Revoga todas as licenças de um usuário pelo nome"""
    licencas_revogadas = []
    for codigo, dados in self.dados["licencas"].items():
        if dados.get("usuario") == nome_usuario and dados.get("status") == "ativo":
            dados["status"] = "revogado"
            licencas_revogadas.append(codigo)
    
    if licencas_revogadas:
        self.salvar()
    
    return licencas_revogadas

# Atualize os exports
__all__ = [
    'DADOS_COMPLETOS',
    'PALAVRAS_CHAVE_CAUDA_LONGA',
    'calcular_score',
    'gerar_top10_produtos',
    'gerar_sugestoes_diarias',
    'SistemaLicencas',
    'carregar_apoiadores',
    'adicionar_apoiador',
    'remover_apoiador',
    'BUSCAS_DIARIAS',
    'LICENCA_TRIAL',
    'ADMIN_LICENCA'
]
