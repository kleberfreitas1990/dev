# Prompt de continuidade — Minerador de Produtos v8.1

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.1 — Fast Download Strategy**.

## Estado atual

O Metadata Pro (v8.1) foi otimizado para acelerar tanto o download quanto o processamento.

### Novidades da v8.1:
1.  **Download de Fluxo Único:** O `yt-dlp` agora prefere o melhor formato MP4 já fundido (`best[ext=mp4]/best`). Isso elimina o tempo de fusão de áudio e vídeo após o download.
2.  **Parâmetros de Rede:** Adicionados `socket_timeout` e `retries` para evitar que o download fique travado em conexões lentas ou instáveis.
3.  **Performance (v8.0):** Mantém o uso de `ultrafast` e multi-threading no FFmpeg para a limpeza de metadados.

## Ficheiros alterados na v8.1

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Mudança na estratégia de seleção de formato do `yt-dlp`. |
| `marketplace.app.py` | Versão atualizada para `v8.1 - Fast Download Strategy`. |

## Validação

O tempo total (Download + Limpeza) foi otimizado. Ao evitar a fusão (muxing) de streams separados, economizamos vários segundos de processamento inicial.

## Próximos passos

1.  Testar em URLs do Instagram e YouTube, onde a fusão de streams é mais comum, para garantir que a qualidade continua satisfatória com o formato único.
2.  Considerar o uso de `aria2c` como downloader externo se a velocidade de rede for o gargalo principal.
