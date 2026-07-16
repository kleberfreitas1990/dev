# Prompt de continuidade — Minerador de Produtos v8.9

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.9 — Camera Pattern Naming**.

## Estado atual

O Metadata Pro (v8.9) agora disfarça a origem dos ficheiros utilizando padrões de nomenclatura de câmaras reais.

### Novidades da v8.9:
1.  **Camera Pattern Generator:** O sistema sorteia aleatoriamente um padrão de nome de ficheiro de fabricantes conhecidos:
    *   **Apple (iPhone):** `IMG_XXXX.MP4`
    *   **Android/Samsung:** `VID_YYYYMMDD_HHMMSS.mp4`
    *   **Sony/Nikon:** `DSC_XXXX.MP4`
    *   **Genérico:** `CIMGXXXX.mp4`
2.  **Disfarce de Software:** Removido qualquer rasto de termos como "limpo", "processado" ou "minerador" no nome do ficheiro final, tornando-o visualmente idêntico a um ficheiro bruto de câmara.
3.  **Forensic Deep Clean (v8.8):** Mantém a remoção profunda de GPS e data streams, garantindo que o conteúdo interno também seja anónimo.

## Ficheiros alterados na v8.9

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Implementação de `gerar_nome_arquivo_limpo` com lógica de padrões de fabricantes. |
| `marketplace.app.py` | Versão atualizada para `v8.9 - Camera Pattern Naming`. |

## Validação

O ficheiro final agora apresenta-se como um conteúdo original capturado por um dispositivo móvel ou câmara digital, tanto nos metadados internos quanto no nome externo.

## Próximos passos

1.  Avaliar se a ordem numérica dos nomes (ex: `IMG_4829`) deve ser sequencial na sessão ou se o aleatório é suficiente.
2.  Considerar a adição de padrões de câmaras de ação (GoPro: `GHXXXXXX.mp4`).
