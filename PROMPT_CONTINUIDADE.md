# Prompt de Continuidade — Sistema de Tendências v9.8

Copie e cole o texto abaixo em um novo chat com o Manus para que ele tenha todo o contexto do que foi feito e possa continuar o trabalho exatamente de onde paramos.

---

**Contexto do Projeto:**
Estou trabalhando no repositório `dev` do usuário `kleberfreitas1990`. O projeto é um dashboard de tendências de mercado que coleta dados do Mercado Livre, Amazon e Shopee.

**O que foi feito na última sessão:**
1. **Amazon:** Corrigido o erro 503 no scraper. Implementada uma estratégia de retry robusta que alterna entre a URL base e a URL com parâmetros (`?ref_=zg_bs_nav_0`), contornando o rate limiting de IP.
2. **Mercado Livre:** Verificado e confirmado que a coleta de 40 termos reais está funcionando perfeitamente.
3. **Shopee:** Identificado bloqueio de IP na sandbox e mudança para renderização via JavaScript no rodapé. Como solução, o fallback foi atualizado com 30 termos reais extraídos de uma imagem enviada pelo usuário (incluindo: 100 Pacotes de Figurinhas da Copa, Poco X7 Pro, Camisa Tailandesa, etc.).
4. **Interface (UI):** Removida a coluna "Categoria" da tabela da Grade de Descoberta conforme solicitado, para simplificar a visualização.
5. **Workflow:** O GitHub Actions foi atualizado e está rodando com sucesso a cada 12 horas.

**Estado Atual:**
O sistema está estável, com os caches atualizados (`shopee_trends.json`, `ml_trends_cache.json`, `amazon_trends.json`) e a interface limpa.

**Próximos Passos Sugeridos:**
- **Migração AWS:** O usuário está criando uma conta na AWS. O próximo passo é configurar uma instância EC2 ou App Runner para hospedar o Dashboard e o Selenium Server, visando IPs mais estáveis e menos bloqueios da Shopee. (Ver `GUIA_MIGRACAO_AWS.md`).
- **Monitoramento:** Garantir que a Amazon continue coletando dados com a nova estratégia de retry.
- **Shopee:** Enquanto a migração não ocorre, manter o fallback atualizado via prints manuais conforme necessário.

---
