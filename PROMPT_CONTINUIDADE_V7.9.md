# Prompt de continuidade — Minerador de Produtos v7.9

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v7.9 — TikTok Download Fix**.

## Estado atual

O Metadata Pro (v7.9) inclui uma correção para contornar bloqueios recentes de plataformas como o TikTok durante o download.

### Novidades da v7.9:
1.  **Headers de Navegador:** O `yt-dlp` agora utiliza cabeçalhos HTTP (`User-Agent`, `Accept`, etc.) que simulam um navegador real para reduzir a probabilidade de bloqueios automáticos ("Unexpected response").
2.  **Robustez no Download:** Melhora na extração de vídeos de redes sociais, mantendo o fluxo manual e a limpeza de metadados.

## Ficheiros alterados na v7.9

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Adição de `http_headers` nas opções do `yt_dlp.YoutubeDL`. |
| `marketplace.app.py` | Versão atualizada para `v7.9 - TikTok Download Fix`. |

## Validação

A alteração visa mitigar erros de resposta inesperada das páginas de vídeo. Em ambientes de produção, pode ser necessário atualizar periodicamente a biblioteca `yt-dlp` (`pip install -U yt-dlp`).

## Próximos passos

1.  Se o erro persistir, implementar o uso de cookies (`--cookies-from-browser`) ou integração com APIs de terceiros para download.
2.  Monitorizar a estabilidade do download para diferentes URLs do TikTok (mobile vs desktop).
