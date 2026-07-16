# Prompt de continuidade — Minerador de Produtos v8.4

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.4 — Pipeline Streamlining**.

## Estado atual

O Metadata Pro (v8.4) utiliza uma arquitetura de pipeline otimizada para reduzir o tempo total de processamento.

### Novidades da v8.4:
1.  **Audio Stream Copy:** O FFmpeg agora tenta copiar o áudio original (`-c:a copy`) sem reencodificar, o que elimina o tempo de processamento de áudio na maioria dos casos.
2.  **Fallback de Áudio Inteligente:** Se o codec de áudio original for incompatível com o contentor MP4, o sistema deteta a falha e reencodifica automaticamente para AAC em milissegundos.
3.  **Eficiência de Pipeline:** O fluxo de trabalho foi desenhado para minimizar etapas redundantes, focando a CPU apenas na reencodificação de vídeo `ultrafast`.

## Ficheiros alterados na v8.4

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Implementação de `stream copy` para áudio e lógica de fallback automático. |
| `marketplace.app.py` | Versão atualizada para `v8.4 - Pipeline Streamlining`. |

## Validação

A remoção da reencodificação de áudio reduz o uso de CPU e acelera a finalização do ficheiro MP4. A lógica de fallback garante que vídeos com áudio em formatos exóticos (como Opus ou Vorbis) continuem a ser processados corretamente.

## Próximos passos

1.  Monitorizar se o `stream copy` de áudio causa problemas de sincronização em plataformas específicas.
2.  Avaliar a implementação de `threaded downloads` em conjunto com este pipeline para máxima performance.
