# Prompt de Continuidade — Minerador de Produtos v9.3

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.3 — ML Real-Time Scraper + Dynamic Sidebar + Score Viz**.

## Estado Actual

A aplicação foi significativamente expandida com raspagem real do Mercado Livre, categorias dinâmicas na barra lateral e visualização avançada de scores e crescimento percentual.

## Novidades da v9.3

1. **Módulo `modules/mercadolivre_scraper.py` (novo):** Raspagem automática real do Mercado Livre Brasil com três estratégias em cascata: página de tendências oficial (`tendencias.mercadolivre.com.br`), API de autocomplete (`mlstatic.com/autosuggest`) e fallback curado de julho/2026. Cache JSON de 6 horas (`ml_trends_cache.json`) com persistência atómica.

2. **Integração no Pipeline de Produtos:** O módulo `modules/produtos_dinamicos.py` foi actualizado para consumir o cache real do ML (passo 5 do pipeline), substituindo a geração aleatória anterior. O fallback estático `TERMOS_ML` permanece como contingência (passo 5b).

3. **Sidebar de Categorias Dinâmicas (`render_sidebar_categorias`):** Nova função em `modules/views.py` que extrai categorias reais dos dados dinâmicos, exibe contagem de produtos por categoria, mostra o status de validade das fontes (ML, Google, Shopee) e oferece botão de actualização rápida.

4. **Filtros na Grade de Descoberta:** A função `render_grade_descoberta` foi expandida com `select_slider` de quantidade (10–30), `selectbox` de fonte e integração com a sidebar de categorias.

5. **Visualização de Scores e Crescimento:**
   - `ProgressColumn` para Score (0–10) e Crescimento % (0–200%) na tabela Top 10.
   - Ranking visual de Crescimento Percentual — Top 5 com barras de progresso e medalhas (🥇🥈🥉).
   - Métricas com `delta` comparativo (crescimento vs. base e vs. média da lista).

6. **Mapeamento de Fontes no `models.py`:** A função `gerar_top10_produtos` agora exibe correctamente `Mercado Livre`, `Mercado Livre ✅`, `Amazon`, `Shopee Live` e `Shopee` em vez de reduzir tudo a "Shopee".

7. **Workflow GitHub Actions actualizado:** O ficheiro `.github/workflows/update_ml_trends.yml` inclui o passo de execução do `mercadolivre_scraper.py` e adiciona `ml_trends_cache.json` ao commit automático.

## Ficheiros Alterados na v9.3

| Ficheiro | Alteração |
| --- | --- |
| `modules/mercadolivre_scraper.py` | **NOVO** — Módulo completo de raspagem ML com cache e fallback. |
| `modules/produtos_dinamicos.py` | Integração do scraper ML no pipeline (passos 5 e 5b) e actualização de `_atualizar_fontes_automaticas`. |
| `modules/views.py` | `render_sidebar_categorias` (nova), `render_grade_descoberta` expandida, `render_dashboard` com ranking de crescimento e `ProgressColumn`. |
| `modules/models.py` | Mapeamento completo de fontes em `gerar_top10_produtos`. |
| `marketplace.app.py` | Versão actualizada para `v9.3`. |
| `.github/workflows/update_ml_trends.yml` | Adicionado passo ML Real-Time Scraper e `ml_trends_cache.json` no commit. |

## Validação da v9.3

- `modules/mercadolivre_scraper.py`: 25 produtos capturados (real + fallback), cache válido com timestamp.
- `obter_produtos_dinamicos`: 80 produtos totais — 30 Shopee Live, 25 ML Real, 17 ML Fallback, 5 Amazon, 3 Shopee.
- `gerar_top10_produtos`: fontes correctas (Amazon, Shopee, Mercado Livre ✅).
- Todas as validações de ficheiro passaram.

## Próximos Passos Sugeridos

1. **Raspagem real da Amazon Brasil:** Substituir os dados estáticos de `amazon_trends.json` por scraping real da página de best-sellers da Amazon Brasil (similar ao que foi feito para o ML).
2. **Persistência do filtro de categoria na sessão:** Guardar a categoria seleccionada na sidebar em `st.session_state` para que o filtro persista entre recarregamentos de tab.
3. **Gráfico de evolução temporal:** Adicionar um gráfico de linha (Plotly ou Altair) mostrando a evolução do crescimento dos Top 5 produtos ao longo das últimas actualizações do cache.
4. **Alertas de tendência explosiva:** Notificação visual (banner ou `st.toast`) quando um produto ultrapassa 150% de crescimento ou score 10.
5. **Exportação CSV/Excel:** Botão de download da grade de descoberta e do Top 10 em formato CSV ou XLSX.
