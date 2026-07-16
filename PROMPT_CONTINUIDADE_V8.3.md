# Prompt de continuidade — Minerador de Produtos v8.3

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.3 — Compatibility & Fallback**.

## Estado atual

O Metadata Pro (v8.3) equilibra velocidade com compatibilidade máxima para garantir que o download funcione em todos os casos.

### Novidades da v8.3:
1.  **Estratégia de Fallback:** O `yt-dlp` agora tenta descarregar o melhor formato MP4 disponível, mas tem a capacidade de fundir vídeo e áudio se o formato único falhar.
2.  **Redução de Agressividade:** Reduzido para 2 conexões simultâneas (`concurrent_fragment_downloads: 2`) para evitar bloqueios de IP e garantir que a página do TikTok responda corretamente.
3.  **Resiliência Aumentada:** Aumentado o `socket_timeout` para 20s e as tentativas para 10, permitindo que o sistema recupere de instabilidades severas de rede.

## Ficheiros alterados na v8.3

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Ajuste nos parâmetros do `yt-dlp` para garantir compatibilidade e fallback. |
| `marketplace.app.py` | Versão atualizada para `v8.3 - Compatibility & Fallback`. |

## Validação

O sistema prioriza a funcionalidade sobre a velocidade extrema, garantindo que o vídeo seja descarregado mesmo em condições adversas.

## Próximos passos

1.  Monitorizar se a redução de conexões resolveu os erros de "Unexpected response".
2.  Avaliar se o tempo de fusão (muxing) está aceitável para o utilizador final.
3.  Se falhas persistirem, considerar o uso de instâncias de download dedicadas.
