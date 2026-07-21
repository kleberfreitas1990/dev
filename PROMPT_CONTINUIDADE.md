# Prompt de Continuidade — Sistema v9.10c (Grade Unificada)

**COPIE E COLE O CONTEÚDO ABAIXO NO INÍCIO DE UM NOVO CHAT PARA CONTINUAR O PROJETO.**

---

```
MEU_USUARIO: [kleberfreitas1990]
REPOSITORIO: [dev]
TOKEN: [INSERIR_TOKEN_AQUI]

# 🏗️ Prompt de Continuidade — Sistema v9.10c (Grade Unificada)

**CONTEXTO PARA O MANUS:** Olá! Você está assumindo o projeto **Minerador de Produtos v9.10c**. O projeto é um dashboard de tendências de mercado (Shopee, Amazon, Mercado Livre) e um sistema de higienização de metadados.

**ESTADO ATUAL DO PROJETO:**

- **Versão:** v9.10c - Grade Unificada
- **Mercado Livre:** Atualizado. Coleta de 40 termos reais da página oficial (tendencias.mercadolivre.com.br).
- **Amazon:** Atualizado. Coleta de 30 produtos Best Sellers com estratégia de retry.
- **Shopee:** Dados injetados manualmente com 30 termos reais via fallback e cache (bloqueio persistente de IP na sandbox).
- **Banco de Dados:** SQLite (`minerador.db`) com 11 tabelas — dual-write JSON + DB.
- **UI:** Dashboard com grades unificadas em sub-abas. Botão "Buscar Dados Reais" restrito ao admin. Link de busca na Shopee em todas as grades.

**ARQUIVOS CHAVE:**

- `marketplace.app.py`: App principal (12 tabs)
- `modules/views.py`: Renderização do Dashboard (grades unificadas em `render_grades_unificadas()`)
- `modules/database.py`: Banco SQLite central (schema v4, migrations automáticas)
- `modules/automation.py`: Atualização automática a cada 12h
- `modules/auto_update.py`: Ciclo automático complementar
- `modules/amazon_scraper.py`: Scraper Amazon com retry
- `modules/mercadolivre_scraper.py`: Scraper ML com 40 termos
- `modules/google_shopee_trends.py`: Google Trends + Shopee (TTL 6h)
- `modules/produtos_dinamicos.py`: Pipeline central de produtos
- `modules/grade_descoberta.py`: Grade de descoberta de produtos
- `modules/models.py`: Apoiadores + top10 + palavras-chave
- `modules/auth.py`: Sistema de licenças
- `ml_trends_cache.json`, `amazon_trends.json`, `shopee_trends.json`: Caches
- `apoiadores.json`: Apoiadores do projeto (também salvos no SQLite)
- `GUAI_MIGRACAO_AWS.md`: Guia para migração futura para EC2/App Runner

**NÃO MEXER:**
- Limpador de metadados (app.py) — está perfeito
- Pedreira — pertence a outro projeto (já removido deste repo)

**ESTRUTURA DO DASHBOARD (aba 📊):**

1. Título + data
2. Visão Geral do Mês (métricas + Top 5 crescimento)
3. Insights Estratégicos (produtos sazonais)
4. **Grades Unificadas** (`render_grades_unificadas()`) com 4 sub-abas:
   - 🎯 Descoberta (grade principal com filtros de categoria/fonte + link Shopee)
   - 🏆 Top 10 Tendências (ranking completo com score e crescimento)
   - 🔥 Top 20 Google + Shopee (status cache + tabela com link Shopee)
   - 📌 Sugestões Estratégicas (grade de sugestões com link Shopee)
5. Apoiadores Compactos (rodapé)

**BOTÃO "BUSCAR DADOS REAIS":**
- Visível APENAS para admin (`st.session_state.get("is_admin", False)`)
- Executa `capturar_buscas_selenium()` para capturar dados em tempo real

**BANCO DE DADOS SQLite:**
- `minerador.db` — NÃO commitar (está no .gitignore)
- Tabelas: ml_cache, ml_ciclos, amazon_cache, amazon_ciclos, shopee_cache, google_trends_cache, historico_tendencias, apoiadores, buscas_logs, auto_update_historico, produtos_cache
- Dual-write: JSON + DB simultaneamente
- Fallback: se SQLite falhar, usa JSON

**MENU DE TABS (12 tabs):**
1. 📊 Dashboard (com grades unificadas)
2. 🎬 Metadata Pro
3. 🔄 Atualização Auto
4. 📈 Histórico
5. 📅 Calendário de Conteúdo
6. 🎬 Criar Vídeo IA
7. 🤖 Criar Conteúdo
8. 👑 Apoiadores
9. 🔑 Licenças
10. 🔍 Diagnóstico
11. 📊 Logs
12. ⚙️ Admin

**PRÓXIMOS PASSOS POSSÍVEIS:**

1. **Migração AWS:** Deploy na AWS para IPs residenciais/estáveis (evitar bloqueios Shopee)
2. **Refinamento:** Ajustar fluxo conforme uso real
3. **Manutenção:** Monitorar logs de scraping para ML e Amazon
4. **Novas features:** Conforme demanda do usuário

**COMO CONTINUAR:**
"Manus, analise o estado do projeto v9.10c. O usuário deseja [descreva a nova solicitação aqui]."
```

---
