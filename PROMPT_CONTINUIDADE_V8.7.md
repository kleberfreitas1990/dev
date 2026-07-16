# Prompt de continuidade — Minerador de Produtos v8.7

Continue o desenvolvimento do projeto **Minerador de Produtos** a partir da versão **v8.7 — Stealth Download Fix**.

## Estado atual

O Metadata Pro (v8.7) foi ajustado para lidar com bloqueios de IP agressivos do TikTok detetados na versão anterior.

### Diagnóstico Técnico:
Na v8.6, o erro `ERROR: [TikTok] Your IP address is blocked from accessing this post` foi identificado. O uso do `aria2c` com 16 conexões simultâneas pode ter sido interpretado como um ataque DDoS ou atividade de bot agressiva, resultando no bloqueio do IP do servidor.

### Novidades da v8.7:
1.  **Stealth Mode:** Removido o `aria2c` para voltar a um padrão de download mais humano e menos agressivo.
2.  **Impersonation:** Adicionado `web_impersonate: chrome` e cabeçalhos brasileiros (`pt-BR`) para simular um utilizador real a aceder ao TikTok a partir do Brasil.
3.  **Referer & Origin:** Adicionados cabeçalhos de origem para validar o pedido como se viesse da própria plataforma.

## Ficheiros alterados na v8.7

| Ficheiro | Alteração |
|---|---|
| `modules/metadados_pro.py` | Remoção do `aria2c` e implementação de cabeçalhos stealth. |
| `marketplace.app.py` | Versão atualizada para `v8.7 - Stealth Download Fix`. |

## Validação

O sistema agora prioriza passar despercebido pelos sistemas de segurança das redes sociais. A velocidade será ligeiramente menor que a "turbo", mas a taxa de sucesso será muito maior.

## Próximos passos

1.  Se o erro de "IP blocked" persistir, será necessário utilizar **proxies residenciais** ou **cookies de uma sessão real** (`--cookies-from-browser`).
2.  Monitorizar se o TikTok exige CAPTCHA (se sim, o download automático por servidor pode ser impossível sem serviços de bypass).
