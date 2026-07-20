# 🚀 Guia de Migração para AWS — Sistema de Tendências v9.8

Migrar para a AWS garantirá que o sistema tenha IPs limpos (evitando bloqueios da Shopee) e recursos dedicados. Abaixo estão as duas melhores opções para o seu projeto.

---

## Opção 1: AWS EC2 (Recomendado para o Dashboard + Selenium)
Esta é a opção mais simples e robusta. Você terá uma máquina virtual (VPS) rodando 24/7.

### Passo a Passo:
1. **Criar Instância:**
   - Escolha uma instância `t3.small` (ou `t2.micro` no Free Tier, mas pode ser lenta para o Selenium).
   - Use a imagem **Ubuntu 22.04 LTS**.
2. **Configurar Security Group:**
   - Libere as portas:
     - `8501` (Streamlit Dashboard)
     - `10000` (API Selenium Scraper)
     - `22` (SSH para acesso)
3. **Instalar Dependências:**
   ```bash
   sudo apt update && sudo apt install -y python3-pip chromium-browser chromium-chromedriver git
   git clone https://github.com/kleberfreitas1990/dev.git
   cd dev
   pip install -r requirements.txt
   ```
4. **Rodar o Sistema:**
   - Use o `pm2` ou `systemd` para manter os scripts rodando em background.

---

## Opção 2: AWS App Runner (Melhor para o Selenium Server)
O App Runner é um serviço gerenciado que roda o seu `Dockerfile` automaticamente.

### Passo a Passo:
1. Conecte seu repositório GitHub ao AWS App Runner.
2. Aponte para a pasta `selenium_server/`.
3. A AWS cuidará de escalar o servidor e fornecer uma URL HTTPS automática (substituindo o Render).

---

## Por que migrar ajuda no bloqueio da Shopee?
1. **IP Dedicado:** Diferente do Render/Manus, na AWS você pode ter um IP fixo (Elastic IP).
2. **Localização:** Você pode escolher a região `sa-east-1` (São Paulo), o que diminui a latência e parece mais "humano" para os servidores brasileiros da Shopee.
3. **Controle Total:** Você pode instalar bibliotecas como `undetected-chromedriver` que são muito mais eficazes contra o erro de tráfego.

---

### Próximos Passos:
- Assim que sua conta AWS estiver ativa, me avise para eu te ajudar com os comandos de instalação via SSH.
- Vou atualizar o `PROMPT_CONTINUIDADE.md` para incluir este plano de migração.
