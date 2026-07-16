# Prompt de continuidade — Minerador de Produtos v9.2

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.2 — Real-Time Data Injection (ML/AMZ/SHP)**.

## Estado atual

A grade de produtos foi renovada com dados reais extraídos de capturas de tela ("Buscas em alta") e tendências de mercado de julho de 2026 para Mercado Livre e Amazon Brasil.

## Novidades da v9.2

1. **Injeção de Termos da Imagem:** Os 30 termos da imagem fornecida (Papel de Parede, Nintendo Switch, etc.) foram injetados como prioridade máxima via `shopee_live_cache.json`.
2. **Tendências Reais ML/Amazon:** Atualização dos módulos de fallback e arquivos de cache com produtos best-sellers de julho de 2026 (iPhone 16, PS5, LEGO Classic, Echo Dot 5ª Geração).
3. **Sincronização de Grade:** A lógica de priorização foi validada, garantindo que os novos produtos automáticos ocupem as primeiras posições da tela inicial.
4. **Consistência de Dados:** Removidos termos obsoletos (iPhone 17, Figurinhas da Copa) para refletir o mercado atual.

## Ficheiros alterados na v9.2

| Ficheiro | Alteração |
| --- | --- |
| `modules/produtos_dinamicos.py` | Atualização das listas `TERMOS_PRINT` e `TERMOS_ML` com dados de julho/2026. |
| `amazon_trends.json` | Injeção de novos best-sellers da Amazon Brasil. |
| `shopee_live_cache.json` | Injeção dos termos extraídos da imagem do usuário. |
| `marketplace.app.py` | Versão atualizada para `v9.2`. |

## Validação

A validação via `validar_v9.2.py` confirmou que os 10 primeiros produtos da grade são os novos termos injetados (Papel de Parede, Prateleira, etc.), seguidos pelas tendências reais da Amazon e Mercado Livre.

## Próximos passos

1. Implementar raspagem automática real para Mercado Livre (similar ao Shopee Live).
2. Adicionar suporte a categorias dinâmicas na barra lateral baseadas nos termos em alta.
3. Melhorar a visualização dos scores para destacar o crescimento percentual real.
