# Prompt de Continuidade — Minerador de Produtos v9.6

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.6 — Antiduplicação Shopee**.

## Novidades da v9.6 (Metadata Pro)

Esta versão foca em proteger os afiliados da Shopee contra punições por conteúdo duplicado. O módulo **Metadata Pro** foi transformado em uma ferramenta de "originalização" de vídeo.

### 🛡️ Estratégia de Antiduplicação

| Técnica | Descrição | Objetivo |
| --- | --- | --- |
| **Reencodificação Profunda** | Uso de `libx264` com preset `medium` e CRF `20`. | Altera completamente o hash (assinatura digital) do arquivo. |
| **Micro Zoom** | Zoom de 1% com recorte automático. | Muda o enquadramento em pixels, quebrando algoritmos de comparação visual. |
| **Ajustes Cromáticos** | Variação de +2% em brilho/contraste e +5% em saturação. | Altera os valores RGB/YUV de cada frame de forma imperceptível. |
| **Timing de Frames** | Ajuste do FPS para valores como `30.01`. | Quebra a detecção por duração exata e sincronia de quadros. |
| **Limpeza de Software** | Remoção de tags `Lavc`, `Apple` e rastros de TikTok/Instagram. | Elimina a prova de que o vídeo foi editado ou baixado de redes sociais. |

### Arquivos alterados

- `modules/metadados_pro.py`: Implementação completa dos filtros de antiduplicação e nova UI Streamlit com controles deslizantes.
- `marketplace.app.py`: Versão atualizada para v9.6.
- `test_metadados_v96.py`: Teste de validação de mudança de hash e limpeza de metadados.

## Validação

- **Hash Check**: Confirmado que o arquivo de saída possui hash SHA-256 diferente do original em 100% dos casos.
- **Metadata Scrubbing**: Verificado via `ffprobe` que tags de software de edição são removidas.
- **Visual Integrity**: Micro-ajustes configurados para serem imperceptíveis ao olho humano, preservando a qualidade para o comprador final.

## Próximos passos

1.  **Watermark Removal**: Adicionar detecção e remoção (ou desfoque) de marcas d'água de redes sociais.
2.  **Audio Pitch Shift**: Aplicar uma mudança mínima no tom do áudio (±0.1 semitom) para evitar detecção por assinatura sonora.
3.  **Frame Dropping**: Opcionalmente remover 1 frame aleatório a cada 5 segundos para mudar a estrutura temporal do vídeo.

**Sistema atualizado para v9.6 — Foco em Segurança de Afiliado.**
