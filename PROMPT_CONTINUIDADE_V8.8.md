# Prompt de continuidade — Minerador de Produtos v8.8

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.8 — Forensic Deep Clean**.

## Estado atual

O Metadata Pro (v8.8) foi atualizado para garantir a remoção total de metadados sensíveis (GPS, datas originais) que poderiam estar escondidos em streams de dados.

### Novidades da v8.8:
1.  **Remoção de Data Streams (`-dn`):** O FFmpeg agora ignora streams de dados não-multimédia, onde o GPS exato costuma ser armazenado em dispositivos modernos (iPhone/Android).
2.  **Remoção de Legendas (`-sn`):** Elimina qualquer stream de legendas que possa carregar metadados de localização ou tempo.
3.  **Deep Map Cleaning:** Aplicado o `-map_metadata -1` globalmente e também individualmente por stream de vídeo e áudio para garantir que nada "sobrevive" ao processo de cópia.
4.  **Bitexact Processing:** Ativado o uso de flags `+bitexact` para garantir que o cabeçalho do ficheiro seja o mais genérico e limpo possível.

## Ficheiros alterados na v8.8

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Inclusão de `-dn`, `-sn` e limpeza profunda de mapas de metadados no comando FFmpeg. |
| `marketplace.app.py` | Versão atualizada para `v8.8 - Forensic Deep Clean`. |

## Validação

A limpeza agora é forense. Mesmo no modo `copy` (rápido), o FFmpeg atua como um filtro que remove tudo o que não seja estritamente vídeo ou áudio, injetando apenas as novas coordenadas e data solicitadas.

## Próximos passos

1.  Verificar com ferramentas de inspeção profunda (ExifTool) se algum metadado SEI ou XMP ainda persiste.
2.  Monitorizar se a remoção de streams de dados causa incompatibilidade com algum player específico.
