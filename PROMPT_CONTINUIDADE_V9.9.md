# 🏗️ Prompt de Continuidade — Sistema v9.9 (Pedreira Flow)

**CONTEXTO PARA O MANUS:**
Olá! Você está assumindo o projeto **Minerador de Produtos v9.9**. O projeto é um dashboard de tendências de mercado (Shopee, Amazon, Mercado Livre) e um sistema de higienização de metadados.

**ESTADO ATUAL DO PROJETO:**
- **Versão:** v9.9 - Pedreira Flow
- **Mercado Livre:** Atualizado em **20/07/2026 10:25**. Coleta de 40 termos reais da página oficial (Apple Watch, Ar Condicionado, etc.). Em caso de erro 403 (bloqueio), o sistema preserva o último cache válido.
- **Amazon:** Atualizado em **20/07/2026 03:25**. Coleta de 30 produtos Best Sellers. Scraper robusto com estratégia de retry.
- **Shopee:** Dados injetados manualmente com 30 termos reais de hoje (Tênis, Alexa, Chopeira, etc.) via fallback e cache, devido ao bloqueio persistente de IP na Shopee.
- **Nova Tela (Pedreira):** Implementada aba "🏗️ Pedreira" com fluxo completo de pedidos (Solicitante, Atendente, Almoxarifado e Compras). Senha do fluxo: `1234`.
- **UI:** Coluna "Categoria" removida da grade de produtos principal.

**ARQUIVOS CHAVE:**
- `marketplace.app.py`: Integração da nova aba e atualização de versão.
- `modules/pedreira.py`: Lógica do fluxo de pedidos.
- `ml_trends_cache.json` & `amazon_trends.json`: Caches de tendências oficiais.
- `shopee_trends.json`: Cache injetado com novos termos da Shopee.
- `GUIA_MIGRACAO_AWS.md`: Guia para migração futura para EC2/App Runner.

**PRÓXIMOS PASSOS:**
1. **Migração AWS:** Realizar o deploy na AWS para obter IPs residenciais/estáveis e evitar bloqueios da Shopee.
2. **Refinamento Pedreira:** Ajustar o fluxo conforme o uso real.
3. **Manutenção:** Monitorar os logs de scraping para garantir a continuidade dos dados de ML e Amazon.

**COMO CONTINUAR:**
"Manus, analise o estado do projeto v9.9. O usuário deseja [descreva a nova solicitação aqui]."
