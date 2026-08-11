# Análise: Coleta Diária de Buscas em Alta da Shopee

## Situação Atual (v10.0)

### Estrutura Existente
- **Módulo Principal**: `modules/shopee.py` com função `capturar_buscas_shopee()`
- **Fallback Hardcoded**: Lista `TERMOS_REAIS_SHOPEE` (30 termos) com **conteúdo adulto incluído** ("Consolo", "Boneco Sexual")
- **Cache**: `shopee_trends_cache.json` com TTL de 6 horas
- **Persistência**: SQLite em `minerador.db` com tabelas `shopee_cache` e histórico
- **Limpador de Metadados**: `modules/metadados_pro.py` v10.2 — **INTOCÁVEL**

### Estratégias de Coleta (Prioridade)
1. **Selenium Real** (servidor render) → captura dinâmica
2. **Raspagem Direta** (BeautifulSoup) → HTML parsing
3. **API de Sugestões** → autocomplete da Shopee
4. **Fallback** → `TERMOS_REAIS_SHOPEE` (lista hardcoded)

### Problema Identificado
- Conteúdo adulto não é filtrado em nenhuma estratégia
- Validação atual (`validar_termo_busca`) só limpa caracteres, não faz blacklist temática
- Sem histórico de tendências diárias em SQLite (apenas snapshots do Top 10)

---

## Investigação: APIs Oficiais da Shopee

### Shopee Open Platform (open.shopee.com)
- **Escopo**: APIs para sellers (pedidos, produtos, logística, marketing)
- **Não possui**: Endpoint oficial de "trending searches" ou "hot searches"
- **Conclusão**: Não há API pública oficial para tendências

### Alternativas Viáveis
1. **Scraping Web** (atual) — funciona mas frágil
2. **Selenium/Render** (atual) — mais robusto, requer servidor
3. **APIs Não-Oficiais** (Parse.bot, Charted Sea, Apify) — requerem integração externa

---

## Estratégia Recomendada

### Fase 1: Filtro de Conteúdo Adulto (Imediato)
- Criar `modules/adult_content_filter.py` com blacklist expandida
- Aplicar filtro em **todas as estratégias** de coleta (Selenium, raspagem, API, fallback)
- Remover termos adultos da lista `TERMOS_REAIS_SHOPEE`

### Fase 2: Coleta Diária com Histórico (Curto Prazo)
- Criar `modules/shopee_daily_trends.py` com:
  - Função `coletar_tendencias_diarias()` que executa todas as estratégias
  - Normalização de termos (lowercase, trim, deduplicação)
  - Filtro adulto aplicado
  - Persistência em SQLite com timestamp diário
  - Fallback confiável com dados do dia anterior

### Fase 3: Agendamento Automático (Médio Prazo)
- Integrar com `modules/auto_update.py`
- Disparar coleta diária em horário fixo (ex: 08:00 AM)
- Usar `manus-config schedule` para agendamento persistente

### Fase 4: Dashboard e Relatórios (Futuro)
- Visualizar histórico de tendências em Streamlit
- Gráficos de permanência, entrada/saída de termos
- Exportar relatórios JSON/CSV

---

## Estrutura do Banco de Dados

### Tabela: `shopee_daily_trends` (NOVA)
```sql
CREATE TABLE shopee_daily_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta TEXT NOT NULL,  -- YYYY-MM-DD
    termo TEXT NOT NULL,
    posicao INTEGER,  -- 1-30
    fonte TEXT,  -- 'selenium', 'scraping', 'api', 'fallback'
    filtrado_adulto BOOLEAN DEFAULT 0,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(data_coleta, termo)
);
```

### Tabela: `shopee_daily_summary` (NOVA)
```sql
CREATE TABLE shopee_daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta TEXT UNIQUE NOT NULL,
    total_termos INTEGER,
    termos_filtrados INTEGER,
    fonte_primaria TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementação: Estrutura de Arquivos

```
modules/
├── shopee.py (existente, sem alterações)
├── shopee_api.py (existente, sem alterações)
├── adult_content_filter.py (NOVO)
│   ├── BLACKLIST_ADULTO (set expandida)
│   ├── filtrar_termo()
│   └── filtrar_lista_termos()
├── shopee_daily_trends.py (NOVO)
│   ├── coletar_tendencias_diarias()
│   ├── normalizar_termos()
│   ├── aplicar_filtro_adulto()
│   ├── persistir_em_sqlite()
│   └── obter_tendencias_historicas()
└── database.py (existente, com novas tabelas)

scripts/
├── scheduler_shopee_daily.py (NOVO)
│   └── Agendador para execução diária
```

---

## Blacklist de Conteúdo Adulto (Inicial)

Termos a remover de `TERMOS_REAIS_SHOPEE`:
- Consolo
- Boneco Sexual

Blacklist expandida (para filtro geral):
- Consolo, Dildo, Vibrador, Boneco Sexual, Pênis de borracha
- Conteúdo NSFW, Pornô, Sexo, Erótico
- Drogas, Cocaína, Maconha, Heroína
- Armas ilegais, Explosivos
- Falsificações, Réplicas não-autorizadas

---

## Próximos Passos

1. ✅ Análise concluída
2. ⏳ Implementar filtro adulto
3. ⏳ Criar coleta diária com persistência
4. ⏳ Integrar agendamento
5. ⏳ Testes e validação
6. ⏳ Commit no repositório

