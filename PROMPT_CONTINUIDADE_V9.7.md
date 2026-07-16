# Prompt de Continuidade — Minerador de Produtos v9.7

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.7 — Disfarce de Encoder**.

## Novidades da v9.7 (Metadata Pro)

Esta versão aprimora a "originalização" de vídeos ao remover os rastros técnicos das bibliotecas de codificação (FFmpeg).

### 🎭 Disfarce de Encoder

| Técnica | Descrição | Resultado |
| --- | --- | --- |
| **Stripping de Lavc/Lavf** | Uso de `-fflags +bitexact` e `-flags:v +bitexact` para forçar a remoção das tags automáticas do FFmpeg. | O vídeo não contém mais os termos `Lavc` ou `Lavf` nos metadados. |
| **Identidade Nativa** | Injeção da tag `encoder=Camera` em nível de stream e global. | O software de análise identifica o vídeo como gerado por uma "Câmera" genérica. |
| **Muxer Branding** | Uso da flag `-brand mp42` para mascarar o rastro do container MP4. | O container do arquivo simula padrões de gravação de dispositivos móveis. |
| **Hardware Apple** | Preservação das tags `make=Apple` e `model=iPhone 15 Pro` como metadados informativos. | Reforça a aparência de conteúdo gravado em smartphone de alta performance. |

### Arquivos alterados

- `modules/metadados_pro.py`: Comando FFmpeg atualizado com as novas flags de disfarce.
- `marketplace.app.py`: Versão atualizada para v9.7.
- `test_metadados_v97.py`: Novo teste para validar a ausência de tags `lavc`/`lavf`.

## Validação

- **FFmpeg Scrubbing**: Validado via `ffprobe` que as tags de software foram 100% removidas.
- **Assinatura Visual**: Mantida a estratégia da v9.6 (micro-zoom, ajuste cromático e FPS 30.01).
- **Compatibilidade**: O arquivo resultante é um MP4 padrão compatível com Shopee, TikTok e Instagram.

## Próximos passos sugeridos

1.  **Audio Fingerprint**: Implementar micro-ajustes no áudio (mudança de volume em 0.1% ou pitch shift imperceptível) para quebrar detecção por áudio idêntico.
2.  **Exif Inserter**: Integrar uma biblioteca para injetar metadados EXIF mais complexos (abertura de lente, ISO, tempo de exposição) para simular fotos/vídeos brutos.

**Sistema atualizado para v9.7 — Foco em Anonimato de Software.**
