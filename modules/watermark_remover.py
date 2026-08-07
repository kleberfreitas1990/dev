"""
Módulo de Remoção de Marca d'Água para Vídeos Shopee
======================================================
Ferramenta especializada em remover marcas d'água de vídeos Shopee
utilizando OpenCV inpainting, preservando o áudio original com FFmpeg.

Características:
- Presets de posição para padrões fixos de layout Shopee
- Ajuste manual via sliders para casos customizados
- Preservação de áudio original via FFmpeg mux
- Processamento quadro a quadro com barra de progresso
- Suporte a múltiplos algoritmos de inpainting (TELEA, NS)

Autor: Manus AI
Versão: 1.0.0
"""

import os
import cv2
import numpy as np
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import streamlit as st


# ============================================================
# PRESETS SHOPEE - POSIÇÕES DE MARCA D'ÁGUA
# ============================================================
PRESETS_SHOPEE = {
    "Canto Inferior Direito (Padrão)": {
        "descricao": "Logo Shopee no canto inferior direito (posição mais comum)",
        "x_percent": 0.75,  # Percentual da largura
        "y_percent": 0.85,  # Percentual da altura
        "width_percent": 0.20,  # Percentual da largura
        "height_percent": 0.12,  # Percentual da altura
        "icone": "📍"
    },
    "Canto Superior Esquerdo": {
        "descricao": "Logo Shopee no canto superior esquerdo",
        "x_percent": 0.02,
        "y_percent": 0.02,
        "width_percent": 0.18,
        "height_percent": 0.10,
        "icone": "📍"
    },
    "Centro Inferior": {
        "descricao": "Logo Shopee centralizada na parte inferior",
        "x_percent": 0.40,
        "y_percent": 0.80,
        "width_percent": 0.20,
        "height_percent": 0.15,
        "icone": "📍"
    },
    "Canto Superior Direito": {
        "descricao": "Logo Shopee no canto superior direito",
        "x_percent": 0.78,
        "y_percent": 0.02,
        "width_percent": 0.20,
        "height_percent": 0.10,
        "icone": "📍"
    },
    "Personalizado (Ajuste Manual)": {
        "descricao": "Defina manualmente as coordenadas da marca d'água",
        "x_percent": 0.75,
        "y_percent": 0.85,
        "width_percent": 0.20,
        "height_percent": 0.12,
        "icone": "⚙️"
    }
}


# ============================================================
# ALGORITMOS DE INPAINTING
# ============================================================
ALGORITMOS_INPAINTING = {
    "TELEA (Rápido)": cv2.INPAINT_TELEA,
    "NS (Qualidade)": cv2.INPAINT_NS,
}


def calcular_coordenadas_reais(
    altura_frame: int,
    largura_frame: int,
    x_percent: float,
    y_percent: float,
    width_percent: float,
    height_percent: float
) -> tuple:
    """
    Converte percentuais em coordenadas reais do frame.
    
    Args:
        altura_frame: Altura do frame em pixels
        largura_frame: Largura do frame em pixels
        x_percent: Posição X em percentual (0.0 a 1.0)
        y_percent: Posição Y em percentual (0.0 a 1.0)
        width_percent: Largura em percentual (0.0 a 1.0)
        height_percent: Altura em percentual (0.0 a 1.0)
    
    Returns:
        Tupla (x, y, width, height) em pixels
    """
    x = int(largura_frame * x_percent)
    y = int(altura_frame * y_percent)
    width = int(largura_frame * width_percent)
    height = int(altura_frame * height_percent)
    
    # Garante que as coordenadas não saem do frame
    x = max(0, min(x, largura_frame - 1))
    y = max(0, min(y, altura_frame - 1))
    width = min(width, largura_frame - x)
    height = min(height, altura_frame - y)
    
    return (x, y, width, height)


def extrair_primeiro_frame(caminho_video: str) -> np.ndarray:
    """
    Extrai o primeiro frame do vídeo para visualização.
    
    Args:
        caminho_video: Caminho do arquivo de vídeo
    
    Returns:
        Array NumPy com o primeiro frame em BGR
    """
    cap = cv2.VideoCapture(caminho_video)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError("Não foi possível ler o primeiro frame do vídeo")
    
    return frame


def obter_informacoes_video(caminho_video: str) -> dict:
    """
    Extrai informações técnicas do vídeo.
    
    Args:
        caminho_video: Caminho do arquivo de vídeo
    
    Returns:
        Dicionário com informações do vídeo
    """
    cap = cv2.VideoCapture(caminho_video)
    
    info = {
        "largura": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "altura": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duracao_segundos": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
    }
    
    cap.release()
    return info


def extrair_audio(caminho_video: str, caminho_audio: str) -> bool:
    """
    Extrai o áudio do vídeo usando FFmpeg.
    
    Args:
        caminho_video: Caminho do vídeo de entrada
        caminho_audio: Caminho do arquivo de áudio de saída
    
    Returns:
        True se bem-sucedido, False caso contrário
    """
    try:
        cmd = [
            "ffmpeg",
            "-i", caminho_video,
            "-q:a", "9",  # Qualidade máxima de áudio
            "-y",  # Sobrescrever sem perguntar
            caminho_audio
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return result.returncode == 0 and os.path.exists(caminho_audio)
    
    except Exception as e:
        st.error(f"❌ Erro ao extrair áudio: {str(e)}")
        return False


def remover_marca_dagua(
    caminho_video: str,
    caminho_saida: str,
    x: int,
    y: int,
    width: int,
    height: int,
    algoritmo: int = cv2.INPAINT_TELEA,
    raio_inpainting: int = 3,
    callback_progresso=None
) -> bool:
    """
    Remove marca d'água do vídeo usando inpainting.
    
    Args:
        caminho_video: Caminho do vídeo de entrada
        caminho_saida: Caminho do vídeo de saída
        x, y, width, height: Coordenadas da região a remover
        algoritmo: Algoritmo de inpainting (TELEA ou NS)
        raio_inpainting: Raio do kernel de inpainting
        callback_progresso: Função para atualizar progresso
    
    Returns:
        True se bem-sucedido, False caso contrário
    """
    try:
        cap = cv2.VideoCapture(caminho_video)
        
        if not cap.isOpened():
            st.error("❌ Não foi possível abrir o vídeo")
            return False
        
        # Informações do vídeo
        largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Codec e writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(caminho_saida, fourcc, fps, (largura, altura))
        
        if not out.isOpened():
            st.error("❌ Não foi possível criar o vídeo de saída")
            cap.release()
            return False
        
        # Cria máscara para inpainting
        mascara = np.zeros((altura, largura), dtype=np.uint8)
        mascara[y:y+height, x:x+width] = 255
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Aplica inpainting
            frame_processado = cv2.inpaint(
                frame,
                mascara,
                raio_inpainting,
                algoritmo
            )
            
            out.write(frame_processado)
            
            frame_count += 1
            
            # Callback de progresso
            if callback_progresso:
                progresso_percent = (frame_count / total_frames) * 100
                callback_progresso(progresso_percent)
        
        cap.release()
        out.release()
        
        return os.path.exists(caminho_saida) and os.path.getsize(caminho_saida) > 0
    
    except Exception as e:
        st.error(f"❌ Erro ao remover marca d'água: {str(e)}")
        return False


def muxar_audio_video(
    caminho_video_sem_audio: str,
    caminho_audio: str,
    caminho_saida_final: str
) -> bool:
    """
    Mescla o vídeo processado com o áudio original usando FFmpeg.
    
    Args:
        caminho_video_sem_audio: Vídeo processado (sem áudio)
        caminho_audio: Arquivo de áudio extraído
        caminho_saida_final: Caminho do vídeo final com áudio
    
    Returns:
        True se bem-sucedido, False caso contrário
    """
    try:
        cmd = [
            "ffmpeg",
            "-i", caminho_video_sem_audio,
            "-i", caminho_audio,
            "-c:v", "copy",  # Copia vídeo sem re-encodar
            "-c:a", "aac",   # Codifica áudio em AAC
            "-map", "0:v:0",  # Mapeia vídeo do primeiro arquivo
            "-map", "1:a:0",  # Mapeia áudio do segundo arquivo
            "-shortest",      # Usa a duração mais curta
            "-y",             # Sobrescrever sem perguntar
            caminho_saida_final
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        sucesso = result.returncode == 0 and os.path.exists(caminho_saida_final)
        
        if not sucesso:
            st.error(f"❌ Erro ao muxar áudio: {result.stderr[-200:]}")
        
        return sucesso
    
    except Exception as e:
        st.error(f"❌ Erro ao muxar áudio e vídeo: {str(e)}")
        return False


def processar_video_completo(
    caminho_video: str,
    x: int,
    y: int,
    width: int,
    height: int,
    algoritmo: int = cv2.INPAINT_TELEA,
    raio_inpainting: int = 3
) -> tuple:
    """
    Processa o vídeo completo: extrai áudio, remove marca d'água e mescla.
    
    Args:
        caminho_video: Caminho do vídeo de entrada
        x, y, width, height: Coordenadas da marca d'água
        algoritmo: Algoritmo de inpainting
        raio_inpainting: Raio do kernel
    
    Returns:
        Tupla (sucesso: bool, caminho_saida: str, mensagem: str)
    """
    caminho_temp_audio = None
    caminho_temp_video = None
    
    try:
        # 1. Extrai áudio
        with tempfile.NamedTemporaryFile(suffix=".aac", delete=False) as tmp_audio:
            caminho_temp_audio = tmp_audio.name
        
        st.info("🔊 Extraindo áudio original...")
        if not extrair_audio(caminho_video, caminho_temp_audio):
            return False, None, "Falha ao extrair áudio"
        
        # 2. Processa vídeo (remove marca d'água)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
            caminho_temp_video = tmp_video.name
        
        st.info("🎬 Removendo marca d'água...")
        
        def callback_prog(percent):
            st.session_state['watermark_progress'] = percent
        
        if not remover_marca_dagua(
            caminho_video,
            caminho_temp_video,
            x, y, width, height,
            algoritmo,
            raio_inpainting,
            callback_prog
        ):
            return False, None, "Falha ao remover marca d'água"
        
        # 3. Mescla vídeo com áudio
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_final:
            caminho_saida_final = tmp_final.name
        
        st.info("🔗 Mesclando áudio e vídeo...")
        if not muxar_audio_video(caminho_temp_video, caminho_temp_audio, caminho_saida_final):
            return False, None, "Falha ao mesclar áudio e vídeo"
        
        return True, caminho_saida_final, "✅ Vídeo processado com sucesso!"
    
    except Exception as e:
        return False, None, f"❌ Erro durante processamento: {str(e)}"
    
    finally:
        # Limpeza de arquivos temporários
        for caminho in [caminho_temp_audio, caminho_temp_video]:
            if caminho and os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except:
                    pass


def render_watermark_remover():
    """
    Renderiza a interface Streamlit para remoção de marca d'água.
    """
    st.markdown("## 🎥 Remoção de Marca d'Água — Vídeos Shopee")
    st.caption(
        "Remova marcas d'água de vídeos Shopee usando IA inpainting. "
        "O áudio original é preservado automaticamente."
    )
    
    # ============================================================
    # UPLOAD DO VÍDEO
    # ============================================================
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "📤 Envie o vídeo Shopee",
            type=["mp4", "mov", "mkv"],
            key="watermark_uploader"
        )
    
    if not uploaded_file:
        st.info("⏳ Aguardando upload de vídeo para processamento.")
        return
    
    # ============================================================
    # INFORMAÇÕES DO VÍDEO
    # ============================================================
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_upload:
        caminho_temp_upload = tmp_upload.name
        tmp_upload.write(uploaded_file.getbuffer())
    
    try:
        info_video = obter_informacoes_video(caminho_temp_upload)
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("📐 Resolução", f"{info_video['largura']}×{info_video['altura']}")
        with col_info2:
            st.metric("⏱️ Duração", f"{info_video['duracao_segundos']}s")
        with col_info3:
            st.metric("🎞️ FPS", f"{info_video['fps']:.1f}")
        
        # ============================================================
        # VISUALIZAÇÃO DO PRIMEIRO FRAME
        # ============================================================
        primeiro_frame = extrair_primeiro_frame(caminho_temp_upload)
        
        # Redimensiona para visualização
        altura_display = 400
        proporcao = altura_display / primeiro_frame.shape[0]
        largura_display = int(primeiro_frame.shape[1] * proporcao)
        frame_display = cv2.resize(primeiro_frame, (largura_display, altura_display))
        
        st.image(
            cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB),
            caption="📸 Primeiro frame do vídeo",
            use_column_width=True
        )
        
        # ============================================================
        # SELEÇÃO DE PRESET
        # ============================================================
        st.markdown("### 🎯 Selecione o Preset da Marca d'Água")
        
        preset_selecionado = st.selectbox(
            "Escolha a posição da marca d'água:",
            list(PRESETS_SHOPEE.keys()),
            key="watermark_preset"
        )
        
        preset_info = PRESETS_SHOPEE[preset_selecionado]
        st.markdown(f"**{preset_info['icone']} {preset_info['descricao']}**")
        
        # ============================================================
        # AJUSTES MANUAIS (se personalizado)
        # ============================================================
        if "Personalizado" in preset_selecionado:
            st.markdown("### ⚙️ Ajuste Manual das Coordenadas")
            
            col_x, col_y = st.columns(2)
            with col_x:
                x_percent = st.slider(
                    "Posição X (% da largura)",
                    0.0, 1.0, preset_info['x_percent'],
                    step=0.01,
                    key="watermark_x"
                )
            with col_y:
                y_percent = st.slider(
                    "Posição Y (% da altura)",
                    0.0, 1.0, preset_info['y_percent'],
                    step=0.01,
                    key="watermark_y"
                )
            
            col_w, col_h = st.columns(2)
            with col_w:
                width_percent = st.slider(
                    "Largura (% da largura)",
                    0.01, 0.5, preset_info['width_percent'],
                    step=0.01,
                    key="watermark_w"
                )
            with col_h:
                height_percent = st.slider(
                    "Altura (% da altura)",
                    0.01, 0.5, preset_info['height_percent'],
                    step=0.01,
                    key="watermark_h"
                )
        else:
            x_percent = preset_info['x_percent']
            y_percent = preset_info['y_percent']
            width_percent = preset_info['width_percent']
            height_percent = preset_info['height_percent']
        
        # ============================================================
        # CONFIGURAÇÕES DE PROCESSAMENTO
        # ============================================================
        st.markdown("### 🔧 Configurações de Processamento")
        
        col_algo, col_raio = st.columns(2)
        with col_algo:
            algoritmo_nome = st.selectbox(
                "Algoritmo de Inpainting:",
                list(ALGORITMOS_INPAINTING.keys()),
                key="watermark_algo"
            )
            algoritmo = ALGORITMOS_INPAINTING[algoritmo_nome]
        
        with col_raio:
            raio_inpainting = st.slider(
                "Raio de Inpainting (pixels):",
                1, 10, 3,
                key="watermark_raio"
            )
        
        # ============================================================
        # BOTÃO DE PROCESSAMENTO
        # ============================================================
        if st.button(
            "🚀 Processar e Remover Marca d'Água",
            type="primary",
            use_container_width=True,
            key="watermark_process"
        ):
            # Calcula coordenadas reais
            x, y, w, h = calcular_coordenadas_reais(
                info_video['altura'],
                info_video['largura'],
                x_percent, y_percent,
                width_percent, height_percent
            )
            
            st.info(f"🔍 Coordenadas: X={x}, Y={y}, W={w}, H={h}")
            
            # Processa vídeo
            sucesso, caminho_saida, mensagem = processar_video_completo(
                caminho_temp_upload,
                x, y, w, h,
                algoritmo,
                raio_inpainting
            )
            
            if sucesso:
                st.success(mensagem)
                
                # Informações do arquivo processado
                tamanho_original = os.path.getsize(caminho_temp_upload) / (1024 * 1024)
                tamanho_processado = os.path.getsize(caminho_saida) / (1024 * 1024)
                
                col_tam1, col_tam2 = st.columns(2)
                with col_tam1:
                    st.metric("📥 Tamanho Original", f"{tamanho_original:.2f} MB")
                with col_tam2:
                    st.metric("📤 Tamanho Processado", f"{tamanho_processado:.2f} MB")
                
                # Botão de download
                with open(caminho_saida, "rb") as f:
                    dados_saida = f.read()
                
                nome_arquivo = f"shopee_sem_marca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                
                st.download_button(
                    label=f"📥 Baixar Vídeo Processado ({nome_arquivo})",
                    data=dados_saida,
                    file_name=nome_arquivo,
                    mime="video/mp4",
                    use_container_width=True,
                    key="watermark_download"
                )
                
                st.info(
                    "💡 **Dica:** Você pode usar este vídeo processado na aba "
                    "'🎬 Metadados Pro' para aplicar antiduplicação e limpeza de metadados!"
                )
                
                # Limpeza
                try:
                    os.remove(caminho_saida)
                except:
                    pass
            
            else:
                st.error(mensagem)
    
    finally:
        # Limpeza do arquivo temporário de upload
        if os.path.exists(caminho_temp_upload):
            try:
                os.remove(caminho_temp_upload)
            except:
                pass


__all__ = ["render_watermark_remover"]
