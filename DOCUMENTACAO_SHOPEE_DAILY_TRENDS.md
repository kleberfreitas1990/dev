# Documentação: Sistema de Coleta Diária de Tendências Shopee

**Versão**: 1.0.0  
**Data**: 11 de agosto de 2026  
**Autor**: Manus AI  
**Status**: Produção

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Componentes](#componentes)
4. [Instalação e Configuração](#instalação-e-configuração)
5. [Uso e Operação](#uso-e-operação)
6. [Monitoramento](#monitoramento)
7. [Troubleshooting](#troubleshooting)
8. [Roadmap Futuro](#roadmap-futuro)

---

## Visão Geral

O **Sistema de Coleta Diária de Tendências Shopee** é responsável por:

1. **Coletar** buscas em alta da Shopee diariamente através de múltiplas estratégias (Selenium, scraping, API)
2. **Filtrar** conteúdo adulto e sensível automaticamente
3. **Normalizar** termos (deduplicação, limpeza)
4. **Persistir** histórico em SQLite com timestamp diário
5. **Fornecer** fallback confiável com dados do dia anterior
6. **Agendar** execução automática em horário fixo

### Benefícios

- ✅ **Sem conteúdo adulto**: Filtro automático bloqueia termos sensíveis
- ✅ **Histórico completo**: Rastreia tendências ao longo do tempo
- ✅ **Fallback robusto**: Nunca falha completamente
- ✅ **Integração simples**: Funciona com o sistema existente
- ✅ **Sem alterações**: Limpador de metadados v10.0 intocado

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│         Coleta Diária de Tendências Shopee              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agendador (APScheduler / Cron / Manus)                │
│         ↓                                               │
│  scheduler_shopee_daily.py                             │
│         ↓                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ shopee_daily_trends.py (Orquestrador)           │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ 1. Coletar (Selenium → Scraping → API → FB)    │   │
│  │ 2. Normalizar (deduplica, limpa)               │   │
│  │ 3. Filtrar (adult_content_filter.py)           │   │
│  │ 4. Persistir (SQLite + JSON cache)             │   │
│  └─────────────────────────────────────────────────┘   │
│         ↓                                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Armazenamento                                    │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ • SQLite: minerador.db (histórico)              │  │
│  │ • JSON: shopee_daily_cache.json (cache diário)  │  │
│  │ • JSON: scheduler_execucoes.json (logs)         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Componentes

### 1. `modules/adult_content_filter.py`

**Responsabilidade**: Filtrar conteúdo adulto e sensível

**Funções principais**:
- `eh_termo_adulto(termo)` — Verifica se termo está na blacklist
- `filtrar_termo(termo)` — Filtra um termo individual
- `filtrar_lista_termos(termos)` — Filtra lista completa
- `obter_estatisticas_filtro(termos)` — Retorna estatísticas

**Blacklist incluída**:
- Produtos sexuais (consolo, vibrador, boneco sexual, etc.)
- Conteúdo sexual explícito (pornô, erótico, etc.)
- Drogas e substâncias ilícitas
- Armas e explosivos
- Falsificações
- Conteúdo de ódio e discriminação
- Violência extrema

**Exemplo de uso**:
```python
from modules.adult_content_filter import filtrar_lista_termos

termos = ["iPhone", "Consolo", "PS5"]
termos_filtrados = filtrar_lista_termos(termos)
# Resultado: ["iPhone", "PS5"]
```

### 2. `modules/shopee_daily_trends.py`

**Responsabilidade**: Orquestrar coleta, normalização e persistência

**Funções principais**:
- `coletar_tendencias_diarias()` — Coleta com fallback
- `normalizar_termos(termos)` — Deduplica e limpa
- `persistir_tendencias_sqlite()` — Salva em banco
- `obter_tendencias_historicas(dias)` — Consulta histórico
- `obter_termos_permanentes(dias)` — Termos que permaneceram
- `executar_coleta_diaria()` — Rotina completa

**Tabelas SQLite criadas**:
- `shopee_daily_trends` — Termos individuais por dia
- `shopee_daily_summary` — Resumo diário

**Exemplo de uso**:
```python
from modules.shopee_daily_trends import executar_coleta_diaria

resultado = executar_coleta_diaria(forcar_atualizacao=True)
print(f"Coletados {resultado['total_termos']} termos")
print(f"Bloqueados {resultado['termos_bloqueados']} adultos")
```

### 3. `scheduler_shopee_daily.py`

**Responsabilidade**: Agendar e executar coleta automaticamente

**Modos de operação**:
- `--execute` — Executar coleta imediatamente
- `--scheduler apscheduler` — Iniciar agendador (background)
- `--scheduler manus` — Gerar config para Manus
- `--scheduler cron` — Gerar entrada de crontab
- `--status` — Exibir histórico de execuções

**Exemplo de uso**:
```bash
# Executar imediatamente
python3 scheduler_shopee_daily.py --execute

# Iniciar agendador (executa diariamente às 08:00)
python3 scheduler_shopee_daily.py --scheduler apscheduler --hora 08:00

# Gerar config para Manus
python3 scheduler_shopee_daily.py --scheduler manus --hora 08:00

# Ver status
python3 scheduler_shopee_daily.py --status
```

---

## Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- SQLite3
- Módulos existentes do repositório (shopee.py, validation.py, etc.)

### Instalação

1. **Clonar/atualizar repositório**:
```bash
cd /home/ubuntu/dev
git pull origin main
```

2. **Instalar dependências** (se necessário):
```bash
pip3 install apscheduler  # Para agendador local
```

3. **Verificar instalação**:
```bash
python3 test_shopee_daily_trends.py
# Deve exibir: Total: 4/4 testes passaram
```

### Configuração Inicial

#### Opção 1: APScheduler (Local)

Ideal para desenvolvimento e testes:

```bash
cd /home/ubuntu/dev
python3 scheduler_shopee_daily.py --scheduler apscheduler --hora 08:00
```

#### Opção 2: Cron (Linux)

Ideal para produção em servidor:

```bash
# Gerar entrada de crontab
python3 scheduler_shopee_daily.py --scheduler cron --hora 08:00

# Adicionar ao crontab
(crontab -l 2>/dev/null; python3 scheduler_shopee_daily.py --scheduler cron --hora 08:00) | crontab -
```

#### Opção 3: Manus Scheduler

Ideal para integração com Manus:

```bash
# Gerar configuração
python3 scheduler_shopee_daily.py --scheduler manus --hora 08:00 > manus_config.json

# Registrar com manus-config
manus-config schedule --add manus_config.json
```

---

## Uso e Operação

### Execução Manual

```bash
# Executar coleta imediatamente
python3 scheduler_shopee_daily.py --execute

# Resultado esperado:
# {
#   "data": "2026-08-11",
#   "total_termos": 27,
#   "termos_bloqueados": 3,
#   "fonte": "fallback",
#   "timestamp": "2026-08-11T10:33:00.123456",
#   "termos": ["iPhone", "PS5", "Moto Elétrica Scooter", ...]
# }
```

### Consultar Histórico

```bash
# Ver últimas execuções
python3 scheduler_shopee_daily.py --status

# Ver histórico de 60 dias
python3 scheduler_shopee_daily.py --status --historico 60
```

### Consultar Dados em SQLite

```bash
# Conectar ao banco
sqlite3 minerador.db

# Ver termos de hoje
SELECT termo, posicao FROM shopee_daily_trends 
WHERE data_coleta = date('now') 
ORDER BY posicao;

# Ver resumo dos últimos 7 dias
SELECT data_coleta, total_termos, termos_filtrados, fonte_primaria 
FROM shopee_daily_summary 
WHERE data_coleta >= date('now', '-7 days') 
ORDER BY data_coleta DESC;

# Ver termos que permaneceram em alta (últimos 7 dias)
SELECT termo, COUNT(DISTINCT data_coleta) as dias 
FROM shopee_daily_trends 
WHERE data_coleta >= date('now', '-7 days') 
GROUP BY termo 
HAVING dias >= 4 
ORDER BY dias DESC;
```

### Integração com App Streamlit

```python
# Em app.py ou módulo de dashboard
from modules.shopee_daily_trends import (
    obter_tendencias_historicas,
    obter_termos_permanentes,
    obter_resumo_diario
)
from datetime import datetime

# Exibir tendências de hoje
hoje = datetime.now().strftime("%Y-%m-%d")
resumo = obter_resumo_diario(hoje)

st.metric("Termos em Alta", resumo['total_termos'])
st.metric("Bloqueados", resumo['termos_filtrados'])

# Gráfico de histórico
historico = obter_tendencias_historicas(dias=30)
# ... processar e exibir
```

---

## Monitoramento

### Logs

**Arquivo principal**: `scheduler_shopee_daily.log`

```bash
# Ver últimas linhas
tail -50 scheduler_shopee_daily.log

# Monitorar em tempo real
tail -f scheduler_shopee_daily.log
```

### Arquivo de Execuções

**Arquivo**: `scheduler_execucoes.json`

Contém histórico das últimas 90 execuções com:
- Timestamp
- Status (sucesso/erro)
- Total de termos
- Termos bloqueados
- Fonte utilizada

### Alertas Recomendados

| Evento | Ação |
|--------|------|
| Execução falha 3x consecutivas | Revisar logs e credenciais |
| Taxa de bloqueio > 50% | Revisar blacklist |
| Sem dados por 24h | Verificar conectividade |
| Arquivo log > 100MB | Rotacionar logs |

---

## Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'streamlit'"

**Solução**:
```bash
sudo pip3 install streamlit
```

### Problema: "Permission denied" ao escrever em banco

**Solução**:
```bash
# Verificar permissões
ls -la minerador.db

# Corrigir se necessário
chmod 644 minerador.db
```

### Problema: Coleta retorna 0 termos

**Verificar**:
1. Conectividade com Shopee
2. Arquivo de fallback `TERMOS_REAIS_SHOPEE` em `modules/shopee.py`
3. Logs em `scheduler_shopee_daily.log`

**Solução**:
```bash
# Forçar atualização com debug
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from modules.shopee_daily_trends import executar_coleta_diaria
executar_coleta_diaria(forcar_atualizacao=True)
"
```

### Problema: Termos adultos não estão sendo bloqueados

**Verificar**:
1. Blacklist em `modules/adult_content_filter.py`
2. Executar testes: `python3 test_shopee_daily_trends.py`

**Expandir blacklist**:
```python
from modules.adult_content_filter import expandir_blacklist

novos_termos = {"novo termo adulto", "outro termo"}
expandir_blacklist(novos_termos)
```

---

## Roadmap Futuro

### v1.1 (Próximas 2 semanas)

- [ ] Dashboard Streamlit com visualizações
- [ ] Alertas de termos novos/saídos
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] API REST para consultas

### v1.2 (Próximo mês)

- [ ] Integração com Google Trends
- [ ] Análise de sazonalidade
- [ ] Previsões de tendências
- [ ] Webhook para notificações

### v2.0 (Futuro)

- [ ] Multi-marketplace (Amazon, Mercado Livre, etc.)
- [ ] Machine Learning para categorização automática
- [ ] Dashboard em tempo real
- [ ] API pública

---

## Suporte e Contribuições

Para dúvidas, bugs ou sugestões:

1. Verificar documentação acima
2. Consultar logs: `scheduler_shopee_daily.log`
3. Executar testes: `python3 test_shopee_daily_trends.py`
4. Abrir issue no repositório GitHub

---

## Changelog

### v1.0.0 (11/08/2026)

- ✅ Coleta diária com múltiplas estratégias
- ✅ Filtro de conteúdo adulto
- ✅ Persistência em SQLite
- ✅ Cache JSON diário
- ✅ Agendador com APScheduler/Cron/Manus
- ✅ Testes unitários
- ✅ Documentação completa

---

**Última atualização**: 11 de agosto de 2026  
**Próxima revisão**: 25 de agosto de 2026
