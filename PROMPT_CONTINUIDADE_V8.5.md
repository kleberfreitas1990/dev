# Prompt de continuidade — Minerador de Produtos v8.5

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.5 — Pure Metadata Injection**.

## Estado atual

O Metadata Pro (v8.5) foca-se exclusivamente na limpeza e injeção de metadados, sem alterar a qualidade original do vídeo.

### Novidades da v8.5:
1.  **Pure Stream Copy:** O sistema utiliza `-c:v copy` e `-c:a copy` para vídeo e áudio. Isto significa que **não há reencodificação**. O processo é instantâneo e mantém a qualidade 100% original.
2.  **Injeção de Metadados:** O foco total é na remoção de metadados antigos (`-map_metadata -1`) e na injeção da nova localização e tempo de criação.
3.  **Velocidade Máxima:** Como o FFmpeg apenas reescreve o contentor (container swap), o processamento demora apenas o tempo necessário para gravar o ficheiro em disco.

## Ficheiros alterados na v8.5

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Substituição de `libx264` e `aac` por `copy` em ambos os streams. Remoção de filtros de vídeo e redimensionamento. |
| `marketplace.app.py` | Versão atualizada para `v8.5 - Pure Metadata Injection`. |

## Validação

O processo é agora puramente administrativo (metadados). O vídeo de saída é binariamente idêntico ao de entrada no que toca aos pixels, mas com o cabeçalho de metadados limpo e atualizado.

## Próximos passos

1.  Confirmar se a injeção de metadados via `copy` é aceite por todas as plataformas (algumas exigem reencodificação para "esconder" a origem do codec, mas o `copy` é mais fiel ao pedido atual).
2.  Avaliar se o `faststart` continua a ser necessário para visualização rápida em browsers.
