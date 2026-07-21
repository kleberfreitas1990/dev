# Notas de Migração SQLite

## Status
- `database.py` criado com schema completo e migrations automáticas
- `mercadolivre_scraper.py` integrado (dual-write: JSON + SQLite)
- `amazon_scraper.py` integrado (dual-write: JSON + SQLite)
- `pedreira.py` integrado (SQLite primário, JSON fallback)

## Pendente
- `logger.py`: integrar `registrar_busca()` com SQLite
- `auto_update.py`: integrar `registrar_execucao()` e `carregar_historico()` com SQLite
- `historico_tendencias.py`: já usa SQLite próprio (`historico_tendencias.db`) — unificar para `minerador.db`
- `produtos_dinamicos.py`: integrar `salvar_cache_produtos()` com SQLite
- `google_shopee_trends.py`: integrar caches com SQLite
- `shopee_trends.json` (legacy): integrar via `shopee_cache` table

## Decisão
- `historico_tendencias.db` já é sofisticado e isolado. Manter separado.
- Unificar apenas os caches de tendências (ML, Amazon, Shopee, Google) e logs/histórico auto no `minerador.db`.
