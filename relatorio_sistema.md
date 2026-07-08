# Relatório de Análise do Sistema: Minerador de Produtos - Afiliados

**Autor:** Manus AI
**Data:** 08 de Julho de 2026

Este documento apresenta uma análise detalhada da arquitetura, funcionalidades e fluxo de dados do repositório `dev` pertencente ao usuário `kleberfreitas1990`. O sistema consiste em uma aplicação web desenvolvida em Python com Streamlit, voltada para afiliados que buscam identificar produtos em alta para promover.

## 1. Visão Geral da Arquitetura

O sistema é composto por duas partes principais:

1.  **Frontend/Dashboard (Streamlit):** O aplicativo principal (`marketplace.app.py`), hospedado na nuvem (provavelmente Streamlit Cloud), que fornece a interface do usuário com diversas abas (Dashboard, Sugestões, Calendário, Criação de Conteúdo IA, etc.).
2.  **Microserviço de Coleta (Flask/Selenium):** Um servidor backend independente (`selenium_server/app.py`), hospedado no Render, responsável por raspar dados reais de tendências e produtos diretamente do site da Shopee usando o navegador headless (Chromium).

### Tecnologias Utilizadas

| Componente | Tecnologia | Propósito |
| :--- | :--- | :--- |
| **Frontend** | Streamlit, Pandas | Renderização da interface, tabelas e gráficos |
| **Backend (Coleta)** | Flask, Selenium, BeautifulSoup | API para raspagem de dados da Shopee |
| **Integrações Externas** | Serper API | Busca de produtos no Google Shopping |
| **Cache Local** | Arquivos JSON | Armazenamento temporário de produtos, tendências e logs para evitar limites de API |

## 2. Fluxo de Dados e Coleta

O coração do sistema reside em como ele descobre e ranqueia produtos. A estratégia proposta (`PROPOSTA_DADOS_REAIS.md`) visa substituir dados totalmente aleatórios por informações do mercado real. O fluxo atual implementado em `modules/produtos_dinamicos.py` é o seguinte:

1.  **Captura de Tendências (Shopee):** O sistema tenta primeiro obter os termos mais buscados na Shopee através do microserviço Selenium (`modules/shopee.py` e `selenium_client.py`).
2.  **Enriquecimento (Google Shopping):** Para os termos válidos encontrados, o sistema consulta a API do Serper (`modules/serper.py`) para encontrar produtos reais no Google Shopping, extraindo dados como volume de resultados.
3.  **Simulação de Métricas:** Apesar da coleta real de termos e alguns dados do Serper, várias métricas cruciais exibidas no dashboard (como `pins`, `crescimento`, `views_tiktok`, `buscas_mes`, `variacao`) ainda são geradas aleatoriamente usando a biblioteca `random` do Python, como visto no trecho final de `produtos_dinamicos.py`.
4.  **Fallback (Grade de Descoberta):** Se a coleta falhar (ex: servidor Render dormindo, limite da API Serper atingido), o sistema aciona a `Grade de Descoberta` (`modules/grade_descoberta.py`). Este módulo possui um dicionário estático de produtos por categoria e injeta motivos de busca e horários ideais baseados em regras sazonais.

## 3. Principais Funcionalidades do Dashboard

O arquivo principal `marketplace.app.py` orquestra a exibição de várias abas:

*   **Dashboard & Sugestões:** Exibe o "Top 10" de produtos ranqueados com base no score calculado, permitindo buscas diretas na Shopee.
*   **Calendário de Conteúdo:** Sugere produtos baseados em datas comemorativas mensais.
*   **Criador de Conteúdo IA:** Gera scripts de vídeo, dicas de gravação e títulos usando templates estáticos baseados na categoria do produto e duração desejada (`modules/conteudo_ia.py`).
*   **Gestão de Licenças e Apoiadores:** Sistema de autenticação próprio (`modules/auth.py`) que valida códigos de acesso e gerencia "apoiadores" que recebem royalties simulados.
*   **Diagnóstico e Logs:** Áreas administrativas para monitorar a saúde das APIs, status do servidor Selenium, consumo de cotas do Serper e logs de busca (`modules/diagnostico.py`, `modules/logger.py` e `modules/admin_dashboard.py`).

## 4. Pontos de Atenção e Oportunidades de Melhoria

1.  **Métricas Simuladas:** O sistema ainda depende fortemente da função `random` para gerar métricas de engajamento (Pinterest, TikTok). Para entregar valor real aos afiliados, seria ideal integrar APIs dessas redes ou remover métricas que não podem ser comprovadas.
2.  **Servidor Selenium no Render (Free Tier):** O código já prevê timeouts longos (35s) porque servidores gratuitos no Render "dormem" após inatividade. Isso pode causar falhas frequentes na primeira tentativa de busca do dia.
3.  **Gestão de Estado:** O sistema usa arquivos `.json` locais (`produtos_cache.json`, `licencas.json`, etc.) para persistência. Em ambientes serverless como o Streamlit Cloud, o sistema de arquivos é efêmero, o que significa que os dados de cache, licenças e apoiadores podem ser perdidos a cada reinicialização da aplicação. Recomenda-se a migração para um banco de dados real (ex: PostgreSQL, Supabase, Firebase).

## 5. Conclusão

O "Minerador de Produtos" é uma ferramenta bem estruturada e modularizada, com uma proposta de valor clara para afiliados. A transição de dados simulados para dados reais via Selenium e Serper está implementada, embora ainda misture métricas aleatórias. A arquitetura de fallback garante que a interface nunca fique vazia, proporcionando uma boa experiência ao usuário. O próximo passo lógico seria consolidar a persistência de dados em um banco de dados em nuvem para garantir a estabilidade das licenças e do cache.
