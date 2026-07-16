# Prompt de continuidade — Minerador de Produtos v8.0

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.0 — High Performance Processing**.

## Estado atual

O Metadata Pro (v8.0) foi otimizado para velocidade extrema sem comprometer a limpeza de metadados.

### Novidades da v8.0:
1.  **Processamento Ultrafast:** O FFmpeg agora utiliza o preset `ultrafast` e o parâmetro `-threads 0` para processar os vídeos o mais rápido possível.
2.  **Eficiência:** Ajuste no CRF para equilibrar a velocidade do encoder com a qualidade visual, garantindo que o download fique disponível quase instantaneamente após o processamento.

## Ficheiros alterados na v8.0

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Alteração do preset do FFmpeg para `ultrafast` e ativação de multi-threading. |
| `marketplace.app.py` | Versão atualizada para `v8.0 - High Performance Processing`. |

## Validação

O tempo de processamento foi reduzido significativamente. Em testes com vídeos curtos (Reels/TikTok), a limpeza de metadados ocorre em poucos segundos.

## Próximos passos

1.  Avaliar o impacto visual do preset `ultrafast` em vídeos de alta resolução.
2.  Considerar o uso de aceleração por hardware (GPU) se o ambiente de produção o suportar.
