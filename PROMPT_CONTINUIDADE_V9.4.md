# Prompt de Continuidade — Minerador de Produtos v9.4

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.4 — ML & Amazon Real-Time Scraper + KeyFix**.

## Estado Actual

O sistema foi estabilizado com a correção de erros críticos de UI e a implementação de raspagem real para a Amazon Brasil.

## Novidades da v9.4

1. **Correção de Chave Duplicada (Streamlit):** Resolvido o erro `StreamlitDuplicateElementKey` ao adicionar o parâmetro `key_suffix` nas funções `render_sidebar_categorias` e `render_grade_descoberta`. Agora cada aba e contexto possui chaves únicas para os widgets.

2. **Módulo `modules/amazon_scraper.py` (novo):** Raspagem real da página de Best Sellers da Amazon Brasil (`amazon.com.br/gp/bestsellers`). Inclui lógica de inferência de categoria e um **fallback curado de julho/2026** caso o site retorne erro 503 (proteção contra bot).

3. **Refinamento do Scraper ML:** Seletores CSS atualizados para a página de tendências do Mercado Livre (`tendencias.mercadolivre.com.br`) e aumento do limite para **40 termos reais**.

4. **Integração no Pipeline:** O ficheiro `modules/produtos_dinamicos.py` agora integra nativamente os dois novos scrapers reais (ML e Amazon) no seu fluxo de dados principal.

5. **Layout Estabilizado:** O ranking de crescimento compacto v9.3 foi validado e agora coexiste sem erros com a grade de descoberta.

## Ficheiros Alterados na v9.4

| Ficheiro | Alteração |
| --- | --- |
| `modules/amazon_scraper.py` | **NOVO** — Scraper real da Amazon com fallback de segurança. |
| `modules/views.py` | Adicionado `key_suffix` para evitar chaves duplicadas no Streamlit. |
| `modules/produtos_dinamicos.py` | Integração dos scrapers reais ML e Amazon no pipeline principal. |
| `marketplace.app.py` | Versão actualizada para `v9.4` e chaves únicas nas tabs. |
| `amazon_trends.json` | Actualizado com dados reais/fallback v9.4. |
| `ml_trends_cache.json` | Actualizado com 40 termos reais do ML. |

## Validação da v9.4

- **UI:** Sem erros de `DuplicateElementKey` ao navegar entre as abas Dashboard e Sugestões.
- **Amazon:** Cache gerado com sucesso (real ou fallback v9.4).
- **ML:** 40 termos capturados via scraper.
- **Versão:** Exibida correctamente como v9.4 no header.

## Próximos Passos Sugeridos

1. **Dashboard de Análise de Concorrência:** Criar uma nova aba que compare o preço de um mesmo termo entre Amazon e Mercado Livre usando os dados capturados.
2. **Histórico de Tendências:** Implementar uma base de dados simples (SQLite ou CSV acumulado) para permitir ver quais produtos estão no Top 10 há mais de 3 ciclos.
3. **Melhoria no Scraper Amazon:** Implementar rotação de User-Agents ou pequenos delays para contornar o erro 503 frequente da Amazon.
4. **Filtro de Preço:** Adicionar um slider na grade de descoberta para filtrar produtos por faixa de preço (quando disponível nos dados da Shopee/Amazon).
