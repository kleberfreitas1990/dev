# 🏗️ Prompt de Continuidade — Sistema v9.9 (Pedreira Flow)

**CONTEXTO PARA O MANUS:**
Olá! Você está assumindo o projeto **Minerador de Produtos v9.9**. O foco principal deste projeto é um dashboard de tendências de mercado (Shopee, Amazon, Mercado Livre) e um sistema de higienização de metadados. Acabamos de implementar um novo módulo de fluxo de pedidos para uma Pedreira.

**ESTADO ATUAL DO PROJETO:**
- **Versão:** v9.9 - Pedreira Flow
- **Shopee:** Buscas em alta atualizadas manualmente com 30 novos termos reais (Tênis, Alexa, Chopeira, etc.).
- **Amazon/ML:** Scrapers funcionais com estratégia de retry para evitar bloqueios.
- **Nova Tela (Pedreira):** Implementada aba "🏗️ Pedreira" com fluxo completo:
    1. **Solicitante:** Cria pedidos (Produto, Qtd, Empresa).
    2. **Atendente:** Libera acesso via senha (`1234`) ou Admin, e direciona para Almoxarifado ou Compras.
    3. **Almoxarifado/Compras:** Painéis de status para gerenciar o estoque e aquisição.
- **Dashboard:** Coluna "Categoria" removida para simplificação.

**ARQUIVOS CHAVE MODIFICADOS:**
- `marketplace.app.py`: Integração da nova aba e atualização de versão.
- `modules/pedreira.py`: Lógica do fluxo de pedidos.
- `shopee_trends.json`: Cache atualizado com os novos termos.
- `modules/google_shopee_trends.py`: Fallback atualizado.
- `GUIA_MIGRACAO_AWS.md`: Guia para migração futura.

**PRÓXIMOS PASSOS:**
1. **Migração AWS:** O usuário possui conta AWS e o próximo grande passo é o deploy na EC2/App Runner.
2. **Refinamento Pedreira:** Ajustar campos ou permissões conforme o feedback do usuário após teste da tela.
3. **Persistência:** O arquivo `pedidos_pedreira.json` armazena os dados localmente; pode ser necessário migrar para um banco de dados na AWS futuramente.

**COMO CONTINUAR:**
"Manus, analise o arquivo `modules/pedreira.py` e o `marketplace.app.py`. O usuário deseja [descreva a nova solicitação aqui]."
