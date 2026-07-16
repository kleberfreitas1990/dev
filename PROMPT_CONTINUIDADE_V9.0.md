# Prompt de continuidade — Minerador de Produtos v9.0

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v9.0 — Hardware Mimicry (iPhone Pro)**.

## Estado atual

O Metadata Pro (v9.0) foi elevado a um nível de mimetismo de hardware profissional para passar em análises forenses detalhadas.

### Novidades da v9.0:
1.  **iPhone Technical Fingerprint:**
    *   **Handler Name:** Alterado para `Core Media Video/Audio`, o padrão nativo do iOS.
    *   **Bitrate Pro:** Forçado um bitrate de até 25 Mbps com CRF 18 para simular a densidade de dados de uma gravação original de iPhone.
    *   **Hardware Metadata:** Injeção direta de `make=Apple` e `model=iPhone 15 Pro`.
2.  **Sintaxe de GPS Nativa:** Removida a duplicação suspeita de tags. Agora utiliza exclusivamente `com.apple.quicktime.location.ISO6709`, eliminando rastos de softwares de edição.
3.  **Reencodificação de Alta Fidelidade:** Voltámos a usar `libx264` (em modo ultra-rápido) para "esconder" a compressão original do TikTok/Instagram sob uma nova camada de dados densos compatível com hardware real.

## Ficheiros alterados na v9.0

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Reintrodução de reencodificação com parâmetros de alta fidelidade e ajuste fino de tags Apple. |
| `marketplace.app.py` | Versão atualizada para `v9.0 - Hardware Mimicry (iPhone Pro)`. |

## Validação

O ficheiro final agora apresenta características técnicas (bitrate, handlers, metadados) que condizem com um dispositivo Apple real, dificultando a deteção de processamento por software.

## Próximos passos

1.  Monitorizar o tempo de processamento, já que a reencodificação de alto bitrate é mais exigente que o `copy`.
2.  Avaliar se a resolução deve ser forçada para padrões nativos (ex: 1080x1920) se a entrada for exótica.
