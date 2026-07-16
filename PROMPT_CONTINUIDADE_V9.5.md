# Prompt de Continuidade — Minerador de Produtos v9.5

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.5 — Histórico de Tendências**.

## Estado atual

A aplicação mantém o pipeline dinâmico da v9.4.4 e agora registra snapshots do **Top 10** em uma base SQLite local. O histórico é integrado ao ciclo automático, evita duplicações causadas por reruns do Streamlit e permite identificar produtos que permanecem no ranking durante três ou mais ciclos consecutivos.

## Novidades da v9.5

| Componente | Evolução |
| --- | --- |
| Persistência | Nova base `historico_tendencias.db`, criada automaticamente em execução. |
| Idempotência | Rankings idênticos recebem a mesma assinatura SHA-256 e não criam ciclos duplicados. |
| Análise de permanência | Produtos do ciclo atual são avaliados pela sequência consecutiva no Top 10 e pelo total de aparições. |
| Interface | Nova aba **Histórico**, com métricas, filtro de permanência, tabela de produtos persistentes e evolução de score. |
| Automação | Cada atualização automática bem-sucedida tenta registrar o Top 10; falhas no histórico não interrompem os scrapers. |
| Registro manual | A aba permite registrar o ranking atual, respeitando a proteção contra snapshots duplicados. |
| Compatibilidade | O teste antigo que exigia “iPhone 17” foi atualizado para validar a estrutura dinâmica dos produtos. |

## Arquivos alterados

| Arquivo | Alteração |
| --- | --- |
| `modules/historico_tendencias.py` | **Novo** — banco SQLite, snapshots, permanência consecutiva, evolução e painel Streamlit. |
| `modules/auto_update.py` | Integração do registro histórico ao fim do ciclo automático. |
| `marketplace.app.py` | Versão atualizada para v9.5 e nova aba **Histórico**. |
| `test_historico_tendencias.py` | **Novo** — testes de idempotência, sequência, normalização, resumo e smoke test Streamlit. |
| `test_import_produtos_dinamicos.py` | Remoção da dependência de um termo fixo em dados que agora são dinâmicos. |
| `.gitignore` | Exclusão do banco SQLite e dos arquivos auxiliares WAL/SHM gerados em execução. |

## Regras do histórico

Um ciclo contém no máximo os dez primeiros itens recebidos de `gerar_top10_produtos`. Nomes são normalizados sem acentos, caixa ou pontuação para reconhecer variações como “Cafeteira Elétrica” e “cafeteira eletrica” como o mesmo produto.

A permanência consecutiva é calculada a partir do ciclo mais recente. A contagem é interrompida na primeira ausência do produto. Portanto, um produto com muitas aparições antigas, mas ausente em um ciclo recente, não é classificado como persistente até reconstruir sua sequência.

> O banco não é versionado no Git. Ele é criado automaticamente no diretório raiz da aplicação e acumula dados durante a vida útil do ambiente de execução.

## Validação da v9.5

| Validação | Resultado |
| --- | --- |
| Compilação de todos os módulos | Aprovada |
| Testes unitários e de regressão | **15 testes aprovados** |
| Smoke test do dashboard | Aprovado |
| Smoke test do painel de histórico com três ciclos | Aprovado em processo isolado |
| Verificação de whitespace do Git | Aprovada |
| Fallback Amazon em HTTP 503 | Preservado e testado |

## Próximos passos sugeridos

A próxima versão pode persistir o banco em armazenamento externo para sobreviver a recriações completas do ambiente. Outra evolução recomendada é capturar preços normalizados nos scrapers da Amazon e do Mercado Livre; somente depois disso o dashboard de comparação de concorrência terá base real e consistente. Também é recomendável substituir gradualmente `use_container_width` por `width="stretch"` nas telas legadas, pois o Streamlit já sinaliza a descontinuação do parâmetro antigo.

## Versão

**Sistema atualizado para v9.5 — Histórico de Tendências.**
