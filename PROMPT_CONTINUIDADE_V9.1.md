# Prompt de continuidade — Minerador de Produtos v9.1

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.1 — Auto Grid Sync + Hardware Mimicry**.

## Estado atual

A tela inicial voltou a consumir os produtos do ciclo automático. A correção preserva integralmente o Metadata Pro v9.0 e liga o cache `shopee_live_cache.json` à consolidação utilizada pelo dashboard e pela Grade de Descoberta.

## Causa da falha

A rotina automática renovava `shopee_live_cache.json`, mas a Grade de Descoberta lia apenas `shopee_trends.json`, `amazon_trends.json` e os fallbacks do Mercado Livre. Além disso, o parâmetro `forcar_atualizacao=True` de `obter_produtos_dinamicos` não acionava a atualização das fontes.

## Novidades da v9.1

1. **Sincronização da fonte automática:** `produtos_dinamicos.py` converte o cache Shopee Live para o esquema esperado pelo dashboard.
2. **Atualização forçada funcional:** o ciclo automático renova Google/Shopee antes de consolidar os produtos.
3. **Grelha com prioridade automática:** as primeiras 10 posições são reservadas à fonte Shopee Live; Amazon, Shopee legada e Mercado Livre completam as 20 posições.
4. **Caminhos de cache estáveis:** os caches Google/Shopee são gravados na raiz do projeto independentemente do diretório de arranque.
5. **Execução sem duplicidade:** os marcadores das duas rotinas Streamlit são sincronizados para evitar duas atualizações no mesmo rerun.
6. **Compatibilidade restaurada:** `TERMOS_PRINT` e `iPhone 17` voltaram ao contrato público esperado pelos testes existentes.

## Ficheiros alterados na v9.1

| Ficheiro | Alteração |
| --- | --- |
| `modules/produtos_dinamicos.py` | Leitura e normalização do cache Shopee Live, atualização forçada e fallbacks compatíveis. |
| `modules/grade_descoberta.py` | Priorização de 10 produtos automáticos na grelha de 20 itens. |
| `modules/automation.py` | Atualização real das fontes e sincronização dos marcadores de sessão. |
| `modules/google_shopee_trends.py` | Caminhos absolutos e consistentes para os caches. |
| `marketplace.app.py` | Versão atualizada para `v9.1 - Auto Grid Sync + Hardware Mimicry`. |
| `test_grade_auto_update.py` | Testes de integração do cache, atualização forçada e prioridade da grelha. |

## Validação

A suíte completa apresenta **12 testes aprovados**. O diagnóstico funcional confirma uma grelha de 20 itens composta por 10 produtos Shopee Live, 3 Amazon Bestsellers, 3 Shopee Real-Time e 4 Mercado Livre.

## Próximos passos

1. Monitorizar o tempo da primeira atualização em produção.
2. Substituir gradualmente os fallbacks por integrações de marketplace verificáveis.
3. Exibir no dashboard o horário e a origem da última atualização da grelha.
