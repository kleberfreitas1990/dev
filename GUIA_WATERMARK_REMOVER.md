# 🎥 Guia de Uso — Remoção de Marca d'Água para Vídeos Shopee

**Versão:** 1.0.0  
**Data:** Agosto 2026  
**Módulo:** `modules/watermark_remover.py`  
**Integração:** Aba "🎥 Remover Marca d'Água" no Marketplace v10.0

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação e Dependências](#instalação-e-dependências)
3. [Como Usar](#como-usar)
4. [Presets Disponíveis](#presets-disponíveis)
5. [Configurações Avançadas](#configurações-avançadas)
6. [Fluxo de Processamento](#fluxo-de-processamento)
7. [Troubleshooting](#troubleshooting)
8. [Integração com Metadados Pro](#integração-com-metadados-pro)

---

## Visão Geral

O módulo **Watermark Remover** foi desenvolvido para remover marcas d'água de vídeos Shopee utilizando técnicas avançadas de **inpainting com OpenCV**. A ferramenta oferece:

- **5 Presets Pré-configurados** para posições comuns de marca d'água Shopee
- **Ajustes Manuais** via sliders para casos customizados
- **Preservação Automática de Áudio** usando FFmpeg
- **Processamento Quadro a Quadro** com barra de progresso
- **2 Algoritmos de Inpainting** (TELEA para velocidade, NS para qualidade)

### Características Principais

| Recurso | Descrição |
|---------|-----------|
| **Presets** | 5 posições pré-configuradas + modo personalizado |
| **Algoritmos** | TELEA (rápido) e NS (qualidade) |
| **Áudio** | Preservação automática via FFmpeg |
| **Processamento** | Quadro a quadro com progresso em tempo real |
| **Formatos** | MP4, MOV, MKV |
| **Resolução** | Suporta qualquer resolução (testado até 4K) |

---

## Instalação e Dependências

### Dependências Python

O módulo requer as seguintes bibliotecas Python:

```bash
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0
pip install streamlit>=1.58.0
```

### Dependências do Sistema

O FFmpeg deve estar instalado no sistema:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS (com Homebrew)
brew install ffmpeg

# Windows (com Chocolatey)
choco install ffmpeg
```

### Verificar Instalação

```python
import cv2
import numpy as np
print(f"OpenCV: {cv2.__version__}")
print(f"NumPy: {np.__version__}")
```

---

## Como Usar

### Acesso via Interface Streamlit

1. **Abra a aplicação Marketplace** (v10.0 - SQLite)
2. **Clique na aba "🎥 Remover Marca d'Água"**
3. **Faça upload do vídeo** (MP4, MOV ou MKV)

### Fluxo de Uso Passo a Passo

#### 1️⃣ Upload do Vídeo

```
📤 Envie o vídeo Shopee
[Clique para selecionar arquivo]
```

O sistema exibirá automaticamente:
- Resolução do vídeo
- Duração em segundos
- FPS (frames por segundo)
- Primeiro frame como referência

#### 2️⃣ Selecione o Preset

```
🎯 Selecione o Preset da Marca d'Água
[Dropdown com 5 opções]
```

**Opções disponíveis:**
- 📍 Canto Inferior Direito (Padrão)
- 📍 Canto Superior Esquerdo
- 📍 Centro Inferior
- 📍 Canto Superior Direito
- ⚙️ Personalizado (Ajuste Manual)

#### 3️⃣ Ajuste Manual (Opcional)

Se escolher "Personalizado", ajuste as coordenadas:

```
⚙️ Ajuste Manual das Coordenadas
Posição X (% da largura): [slider 0-100%]
Posição Y (% da altura): [slider 0-100%]
Largura (% da largura): [slider 1-50%]
Altura (% da altura): [slider 1-50%]
```

#### 4️⃣ Configure o Processamento

```
🔧 Configurações de Processamento
Algoritmo de Inpainting: [TELEA (Rápido) / NS (Qualidade)]
Raio de Inpainting: [1-10 pixels]
```

#### 5️⃣ Processe o Vídeo

```
🚀 Processar e Remover Marca d'Água [Botão]
```

O sistema irá:
1. 🔊 Extrair o áudio original
2. 🎬 Remover a marca d'água quadro a quadro
3. 🔗 Mesclar o áudio de volta
4. 📥 Disponibilizar para download

---

## Presets Disponíveis

### 📍 Canto Inferior Direito (Padrão)

**Descrição:** Logo Shopee no canto inferior direito (posição mais comum)

| Parâmetro | Valor |
|-----------|-------|
| Posição X | 75% da largura |
| Posição Y | 85% da altura |
| Largura | 20% da largura |
| Altura | 12% da altura |

**Exemplo (1920×1080):**
- X = 1440 pixels
- Y = 918 pixels
- W = 384 pixels
- H = 129 pixels

### 📍 Canto Superior Esquerdo

**Descrição:** Logo Shopee no canto superior esquerdo

| Parâmetro | Valor |
|-----------|-------|
| Posição X | 2% da largura |
| Posição Y | 2% da altura |
| Largura | 18% da largura |
| Altura | 10% da altura |

### 📍 Centro Inferior

**Descrição:** Logo Shopee centralizada na parte inferior

| Parâmetro | Valor |
|-----------|-------|
| Posição X | 40% da largura |
| Posição Y | 80% da altura |
| Largura | 20% da largura |
| Altura | 15% da altura |

### 📍 Canto Superior Direito

**Descrição:** Logo Shopee no canto superior direito

| Parâmetro | Valor |
|-----------|-------|
| Posição X | 78% da largura |
| Posição Y | 2% da altura |
| Largura | 20% da largura |
| Altura | 10% da altura |

### ⚙️ Personalizado

**Descrição:** Defina manualmente as coordenadas da marca d'água

Use os sliders para ajustar a posição e tamanho da região a remover.

---

## Configurações Avançadas

### Algoritmos de Inpainting

#### TELEA (Rápido)

- **Velocidade:** Muito rápida
- **Qualidade:** Boa
- **Uso:** Recomendado para vídeos longos ou quando velocidade é prioridade
- **Tempo:** ~2-5 minutos para vídeo de 1 minuto (1920×1080)

#### NS (Qualidade)

- **Velocidade:** Mais lenta
- **Qualidade:** Excelente
- **Uso:** Recomendado para vídeos críticos ou quando qualidade é prioridade
- **Tempo:** ~5-15 minutos para vídeo de 1 minuto (1920×1080)

### Raio de Inpainting

O raio define o tamanho da área considerada para reconstrução:

- **Raio 1-3:** Melhor para marcas d'água pequenas e nítidas
- **Raio 4-6:** Padrão para a maioria dos casos
- **Raio 7-10:** Para marcas d'água grandes ou com bordas suaves

---

## Fluxo de Processamento

```
┌─────────────────────────────────────┐
│ 1. Upload do Vídeo                  │
│    (MP4, MOV, MKV)                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Extração de Informações          │
│    (Resolução, FPS, Duração)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Visualização do Primeiro Frame   │
│    (Referência para ajustes)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Seleção de Preset ou Ajuste      │
│    Manual de Coordenadas            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 5. Extração de Áudio                │
│    (FFmpeg)                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 6. Processamento de Vídeo           │
│    (Inpainting quadro a quadro)     │
│    [Barra de Progresso]             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 7. Mux de Áudio e Vídeo             │
│    (FFmpeg)                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 8. Download do Vídeo Processado     │
│    (Sem marca d'água)               │
└─────────────────────────────────────┘
```

---

## Troubleshooting

### ❌ "Não foi possível abrir o vídeo"

**Causa:** Arquivo corrompido ou formato não suportado

**Solução:**
1. Verifique se o arquivo é um vídeo válido
2. Tente converter para MP4: `ffmpeg -i input.mov -c:v libx264 output.mp4`
3. Verifique se o FFmpeg está instalado: `ffmpeg -version`

### ❌ "Erro ao extrair áudio"

**Causa:** Áudio em formato não suportado

**Solução:**
1. Verifique se o vídeo possui áudio: `ffprobe -v error -select_streams a:0 -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1:nounits=1 video.mp4`
2. Se não houver áudio, o processamento continuará sem áudio
3. Tente re-encodar o vídeo: `ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4`

### ❌ "Falha ao remover marca d'água"

**Causa:** Coordenadas incorretas ou vídeo muito grande

**Solução:**
1. Verifique as coordenadas usando o primeiro frame como referência
2. Reduza a resolução do vídeo: `ffmpeg -i input.mp4 -vf scale=1280:-1 output.mp4`
3. Tente com o algoritmo TELEA (mais rápido)

### ⚠️ Processamento muito lento

**Causa:** Vídeo de alta resolução ou algoritmo NS

**Solução:**
1. Reduza a resolução: `ffmpeg -i input.mp4 -vf scale=1280:-1 output.mp4`
2. Use o algoritmo TELEA em vez de NS
3. Reduza o raio de inpainting
4. Divida o vídeo em partes menores

### 📊 Qualidade ruim após remoção

**Causa:** Algoritmo ou raio de inpainting inadequados

**Solução:**
1. Tente o algoritmo NS (melhor qualidade)
2. Ajuste o raio de inpainting (teste valores entre 3-7)
3. Certifique-se de que as coordenadas estão corretas
4. Verifique se a marca d'água está completamente dentro da região selecionada

---

## Integração com Metadados Pro

Após remover a marca d'água, você pode usar o vídeo processado na aba **"🎬 Metadados Pro"** para:

1. **Aplicar Antiduplicação** — Alterar assinatura digital para evitar punição da Shopee
2. **Limpar Metadados** — Remover informações de origem
3. **Injetar Perfil de Câmera** — Simular captura de câmera real
4. **Gerar Coordenadas GPS** — Adicionar localização falsa

### Fluxo Recomendado

```
1. Remover Marca d'Água
   ↓
2. Baixar Vídeo Processado
   ↓
3. Ir para "🎬 Metadados Pro"
   ↓
4. Upload do Vídeo (sem marca d'água)
   ↓
5. Aplicar Antiduplicação
   ↓
6. Download do Vídeo Final
   ↓
7. Postar na Shopee
```

---

## 📝 Notas Importantes

- ✅ **Preservação de Áudio:** O áudio original é sempre preservado
- ✅ **Sem Re-encoding:** O vídeo não é re-encodado (apenas a região é processada)
- ✅ **Segurança:** Processamento 100% local, nenhum arquivo é enviado para servidores externos
- ⚠️ **Tempo:** Processamento pode levar vários minutos dependendo da resolução e duração
- ⚠️ **Qualidade:** Quanto maior a marca d'água, mais tempo leva o processamento
- ⚠️ **Memória:** Vídeos muito grandes podem consumir muita memória RAM

---

## 🔧 Referência Técnica

### Estrutura do Módulo

```
modules/watermark_remover.py
├── PRESETS_SHOPEE (dict)
├── ALGORITMOS_INPAINTING (dict)
├── calcular_coordenadas_reais()
├── extrair_primeiro_frame()
├── obter_informacoes_video()
├── extrair_audio()
├── remover_marca_dagua()
├── muxar_audio_video()
├── processar_video_completo()
└── render_watermark_remover()
```

### Funções Principais

#### `render_watermark_remover()`

Renderiza a interface Streamlit completa para remoção de marca d'água.

```python
from modules.watermark_remover import render_watermark_remover
render_watermark_remover()
```

#### `processar_video_completo()`

Processa um vídeo completo (extrai áudio, remove marca d'água, mescla).

```python
sucesso, caminho_saida, mensagem = processar_video_completo(
    caminho_video="/path/to/video.mp4",
    x=1440,
    y=918,
    width=384,
    height=129,
    algoritmo=cv2.INPAINT_TELEA,
    raio_inpainting=3
)
```

---

## 📞 Suporte

Para problemas ou sugestões, consulte os testes inclusos:

- `test_watermark_import.py` — Testa importação do módulo
- `test_watermark_video_processing.py` — Testa funções de processamento
- `test_regressao_metadados_pro.py` — Testa regressões

---

**Versão:** 1.0.0  
**Última Atualização:** Agosto 2026  
**Mantido por:** Manus AI
