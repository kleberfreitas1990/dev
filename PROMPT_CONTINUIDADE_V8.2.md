# Prompt de continuidade — Minerador de Produtos v8.2

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.2 — Bot-Level Speed**.

## Estado atual

O Metadata Pro (v8.2) foi otimizado para atingir velocidades de download comparáveis a bots profissionais do Telegram.

### Novidades da v8.2:
1.  **Download Multi-threaded:** O `yt-dlp` agora descarrega fragmentos do vídeo em paralelo (`concurrent_fragment_downloads: 5`), acelerando significativamente o tempo de recepção de dados.
2.  **Buffer Otimizado:** Aumentado o `buffersize` para 1MB para lidar melhor com streams de alta resolução e reduzir a latência de escrita em disco.
3.  **Resiliência:** Aumentado o número de tentativas (`retries: 5`) com timeouts mais curtos para garantir que o download recupere instantaneamente de pequenas falhas de rede.

## Ficheiros alterados na v8.2

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Implementação de `concurrent_fragment_downloads` e `buffersize` no `yt-dlp`. |
| `marketplace.app.py` | Versão atualizada para `v8.2 - Bot-Level Speed`. |

## Validação

A velocidade de download foi otimizada ao utilizar múltiplas conexões simultâneas para o mesmo ficheiro, técnica comum em bots de alta performance.

## Próximos passos

1.  Monitorizar o consumo de largura de banda do servidor.
2.  Se a velocidade ainda for um problema, considerar o uso de instâncias proxy ou rotação de IPs para evitar o "throttling" das plataformas.
