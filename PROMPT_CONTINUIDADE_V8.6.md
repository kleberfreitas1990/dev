# Prompt de continuidade — Minerador de Produtos v8.6

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.6 — Turbo Download Engine**.

## Estado atual

O Metadata Pro (v8.6) utiliza um motor de download ultra-rápido baseado no `aria2c` para igualar a performance de bots profissionais.

### Novidades da v8.6:
1.  **Turbo Download Engine:** Integração com o `aria2c` como motor de download externo. Ele abre até 16 conexões simultâneas por servidor para descarregar os fragmentos do vídeo em tempo recorde.
2.  **Fragmentação de Dados:** O vídeo é dividido em partes menores descarregadas em paralelo, o que contorna limites de banda impostos pelas plataformas.
3.  **Pure Metadata Injection (v8.5):** Mantém a limpeza instantânea de metadados via `stream copy`, garantindo que o tempo total (Download + Limpeza) seja o mínimo possível.

## Ficheiros alterados na v8.6

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Configuração do `aria2c` nas opções do `yt-dlp`. |
| `packages.txt` | Adição do pacote `aria2` para instalação no ambiente de produção. |
| `marketplace.app.py` | Versão atualizada para `v8.6 - Turbo Download Engine`. |

## Validação

A velocidade de download foi multiplicada ao utilizar o `aria2c`, uma ferramenta especializada em downloads multi-threaded que supera as capacidades nativas do Python.

## Próximos passos

1.  Garantir que o servidor de produção tem o `aria2` instalado (incluído no `packages.txt`).
2.  Monitorizar se o uso de 16 conexões simultâneas causa bloqueios de IP (se sim, reduzir para 8 ou 4).
