# Proposta de Estratégia de Dados Reais para Afiliados

## 1. O Problema Atual
O sistema atual utiliza dados simulados (`random.randint`, `random.uniform`) para gerar métricas como "pins", "crescimento", "views_tiktok", "buscas_mes", etc. Além disso, quando as APIs falham, ele recorre a uma "Grade de Descoberta" estática com produtos pré-definidos. Isso não reflete o mercado real e não ajuda os afiliados a encontrar produtos em alta.

## 2. A Nova Estratégia: Dados 100% Reais

Para fornecer valor real aos afiliados, o sistema deve focar em métricas que podem ser extraídas ou inferidas de fontes reais.

### 2.1. Fontes de Dados
1.  **Shopee Trends (via Selenium no Render):**
    *   Capturar os termos de busca mais populares diretamente da página inicial da Shopee.
    *   Capturar as categorias em destaque.
    *   Isso garante que os produtos sugeridos estão sendo ativamente buscados pelos consumidores na plataforma.
2.  **Google Shopping (via Serper API):**
    *   Para cada termo em alta na Shopee, buscar os produtos correspondentes no Google Shopping.
    *   Extrair dados reais: Preço médio, número de lojas vendendo o produto (indicador de concorrência/demanda), e avaliações (se disponíveis).

### 2.2. Novas Métricas Reais para o Dashboard
Em vez de métricas falsas de redes sociais, o dashboard exibirá:
*   **Termo em Alta (Shopee):** O que as pessoas estão digitando na busca.
*   **Preço Médio (Google Shopping):** Para o afiliado saber a faixa de preço do produto.
*   **Volume de Ofertas (Google Shopping):** Quantos resultados a busca retornou (indicador de popularidade do produto no mercado).
*   **Lojas Principais:** Quais lojas estão vendendo (Shopee, Mercado Livre, Amazon, etc.).

### 2.3. Fluxo de Atualização
1.  O Streamlit solicita tendências ao servidor Selenium (Render).
2.  O servidor Selenium acessa a Shopee e retorna os termos reais em alta no momento.
3.  O Streamlit pega esses termos e consulta a Serper API para obter detalhes dos produtos no Google Shopping.
4.  Os dados são consolidados e exibidos no dashboard.
5.  Se o Selenium falhar, o sistema tenta a raspagem direta (BeautifulSoup) como fallback, mas **nunca** usa dados inventados.

## 3. Benefícios para os Afiliados
*   **Confiança:** Os afiliados saberão que estão promovendo produtos que as pessoas realmente querem comprar hoje.
*   **Estratégia:** Com o preço médio e o volume de ofertas, o afiliado pode decidir se vale a pena focar em um produto de nicho (poucas ofertas) ou de massa (muitas ofertas).
*   **Conteúdo Direcionado:** O assistente de IA usará esses termos reais para gerar roteiros e títulos mais assertivos.
