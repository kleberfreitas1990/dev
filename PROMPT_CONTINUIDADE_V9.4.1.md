# Prompt de Continuidade — Minerador de Produtos v9.4.1

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.4.1 — Top 10 Dinâmico + KeyFix Completo**.

## Estado atual

A versão v9.4.1 corrige dois defeitos de produção observados no Streamlit Cloud: a colisão de chaves dos widgets quando as grades do Dashboard e de Sugestões são executadas no mesmo ciclo, e a estabilidade artificial do Top 10, que exibia repetidamente os primeiros itens do cache Shopee apesar da renovação das métricas.

## Causas raiz corrigidas

| Defeito | Causa raiz | Correção |
| --- | --- | --- |
| `StreamlitDuplicateElementKey` | Apenas o seletor de categoria incorporava `key_suffix`; o botão lateral, o seletor de quantidade, o filtro de fonte e o botão de recarga mantinham chaves globais. | Todas as chaves da grade e da barra lateral passaram a incorporar o contexto `dashboard` ou `sugestoes`. |
| Top 10 sem alteração visível | Muitos produtos tinham `score=10`; a ordenação considerava somente o score e preservava a ordem de inserção, fazendo os primeiros dez itens Shopee vencerem todos os empates. | O ranking passou a desempatar por confiança da fonte, crescimento, variação e buscas, com limite de quatro itens por marketplace antes do preenchimento final. |
| Atualização parcial | O botão lateral renovava somente o Mercado Livre, embora o Top 10 dependesse de várias fontes. | O botão e a central de atualização passaram a chamar o pipeline consolidado de Google, Shopee, Mercado Livre e Amazon. |
| Amazon vazia em HTTP 503 | O scraper devolvia `{}` antes de alcançar o fallback documentado e o contentor local não existia quando a exceção ocorria cedo. | Respostas não-200 acionam o fallback; o dicionário é inicializado antes da requisição e o cache de segurança é gravado. |

## Ficheiros alterados

| Ficheiro | Alteração |
| --- | --- |
| `modules/views.py` | Chaves únicas completas; atualização consolidada; coluna `Atualizado` no Top 10. |
| `modules/models.py` | Ranking dinâmico com desempate por métricas e diversidade por fonte. |
| `modules/auto_update.py` | Ciclo manual e automático unificado para todas as fontes do ranking. |
| `modules/amazon_scraper.py` | Fallback efetivo para HTTP 503 e outros erros precoces. |
| `marketplace.app.py` | Identificação atualizada para v9.4.1. |
| `test_regressoes_v95.py` | Regressões para chaves, ranking, atualização de métricas e fallback Amazon. |

## Validação

A aplicação compila sem erros e a suíte automatizada conclui com **16 testes aprovados**. Os testes novos confirmam que todas as chaves incorporam o contexto de renderização, que uma única fonte não ocupa todo o Top 10 em empates, que o primeiro colocado responde à alteração das métricas e que um HTTP 503 da Amazon produz e persiste o fallback.

## Próximos passos sugeridos

A próxima versão pode substituir gradualmente as métricas aleatórias ainda presentes nos fallbacks por métricas observáveis, acrescentar histórico de posições por ciclo em SQLite e exibir indicadores de entrada, subida, descida e permanência no Top 10.
