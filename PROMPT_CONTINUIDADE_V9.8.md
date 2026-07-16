# Prompt de Continuidade — Minerador de Produtos v9.8

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.8 — Proteção Sonora**.

## Novidades da v9.8 (Metadata Pro)

Esta versão atinge o nível máximo de originalização ao incluir a quebra da assinatura digital do áudio (**Audio Morphing**).

### 🔊 Proteção Sonora (Audio Morphing)

| Técnica | Descrição | Objetivo |
| --- | --- | --- |
| **Micro Pitch Shift** | Alteração do tom do áudio em ±0.005 (0.5%) usando o filtro `rubberband`. | Muda a frequência da onda sonora, quebrando a detecção por "impressão digital" (fingerprint). |
| **Tempo Adjustment** | Ajuste fino da velocidade do áudio em 0.1% usando o filtro `atempo`. | Altera a duração total do áudio em milissegundos para evitar sincronia com o original. |
| **Encoder Scrubbing** | Remoção de rastros do FFmpeg e injeção de `encoder=Camera`. | Mantém o anonimato de software conquistado na v9.7. |
| **UI de Controle** | Novos controles deslizantes no Streamlit para Pitch e Tempo. | Permite ao usuário ajustar o nível de proteção sonora. |

### Arquivos alterados

- `modules/metadados_pro.py`: Implementação dos filtros de áudio e nova interface de controle sonoro.
- `marketplace.app.py`: Versão atualizada para v9.8.
- `test_metadados_v98.py`: Teste de validação para garantir que o áudio não é perdido durante o morphing.

## Validação

- **Audio Integrity**: Confirmado que o áudio é preservado e reencodificado em AAC com as novas propriedades.
- **Visual Integrity**: Mantida a proteção visual da v9.6/v9.7 (micro-zoom, cor, FPS).
- **Silent Processing**: Os filtros são aplicados de forma imperceptível ao ouvido humano.

## Próximos passos sugeridos

1.  **AI Voiceover Integration**: Adicionar opção para substituir o áudio original por uma narração gerada por IA (TTS).
2.  **Background Music Layering**: Inserir uma trilha sonora de fundo em volume baixo (3%) para poluir ainda mais o fingerprint sonoro original.

**Sistema atualizado para v9.8 — Originalização Total (Visual + Sonora).**
