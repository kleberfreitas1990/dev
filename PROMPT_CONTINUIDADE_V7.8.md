# Prompt de continuidade — Minerador de Produtos v7.8

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v7.8 — Fixed Original Resolution**.

## Estado atual

O Metadata Pro (v7.8) agora está mais automatizado e simplificado.

### Novidades da v7.8:
1.  **Resolução Fixa:** A resolução de saída foi fixada em "Proporção Original". O seletor manual foi removido para agilizar o fluxo.
2.  **Interface Limpa:** A interface agora exibe apenas informações relevantes (Localização automática e Resolução original) antes do botão de processamento.
3.  **Localização Automática (v7.7):** Mantém a rotação aleatória de cidades brasileiras a cada geração.

## Ficheiros alterados na v7.8

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Remoção do `selectbox` de resolução e fixação de `resolucao_alvo = None`. |
| `marketplace.app.py` | Versão atualizada para `v7.8 - Fixed Original Resolution`. |

## Validação

O fluxo foi simplificado e a lógica de processamento continua a usar FFmpeg para reencodificar preservando a qualidade original sem deformações.

## Próximos passos

1.  Confirmar se a fixação da resolução atende a todos os formatos de entrada (TikTok, Reels, Shorts).
2.  Avaliar se novos metadados técnicos (além da localização) devem ser automatizados.
