"""
Módulo Metadados Pro v10.0 + Download TikTok/Instagram + Antiduplicação
=====================================================================
Interface Streamlit unificada para:
1. Upload manual de arquivo ou download direto via link (TikTok / Instagram / YouTube)
2. Antiduplicação visual e sonora (micro-zoom, espelhamento, áudio morphing)
3. Limpeza cirúrgica de metadados, remoção de GPS e injeção de perfil de câmera realista

Autor: Manus AI
Versão: 10.1.0
"""

import random
import subprocess
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import streamlit as st
import yt_dlp
import cv2
import numpy as np

LOCALIZACOES_REAIS = [
    {"cidade": "São Paulo, SP", "lat": -23.5505, "lon": -46.6333, "alt": 760},
    {"cidade": "Rio de Janeiro, RJ", "lat": -22.9068, "lon": -43.1729, "alt": 20},
    {"cidade": "Belo Horizonte, MG", "lat": -19.9167, "lon": -43.9345, "alt": 850},
    {"cidade": "Curitiba, PR", "lat": -25.4284, "lon": -49.2733, "alt": 930},
    {"cidade": "Porto Alegre, RS", "lat": -30.0346, "lon": -51.2177, "alt": 10},
    {"cidade": "Salvador, BA", "lat": -12.9714, "lon": -38.5014, "alt": 50},
    {"cidade": "Fortaleza, CE", "lat": -3.7172, "lon": -38.5433, "alt": 20},
    {"cidade": "Recife, PE", "lat": -8.0476, "lon": -34.8770, "alt": 10},
    {"cidade": "Manaus, AM", "lat": -3.1190, "lon": -60.0217, "alt": 90},
    {"cidade": "Brasília, DF", "lat": -15.7801, "lon": -47.9292, "alt": 1170},
]


def gerar_nome_arquivo_limpo(extensao: str = ".mp4") -> str:
    """Gera um nome que simula o padrão de uma câmara real."""
    agora = datetime.now()
    padroes = [
        lambda: f"IMG_{random.randint(1000, 9999)}.MP4",
        lambda: f"VID_{agora.strftime('%Y%m%d_%H%M%S')}.mp4",
        lambda: f"DSC_{random.randint(1000, 9999)}.MP4",
        lambda: f"CIMG{random.randint(1000, 9999)}.mp4",
    ]
    return random.choice(padroes)()


def validar_url_video(url: str) -> bool:
    """Aceita apenas URLs HTTP(S) completas."""
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def baixar_video_yt_dlp(url: str, caminho_destino: str) -> bool:
    """Baixa vídeo de TikTok, Instagram, YouTube ou outras plataformas usando yt-dlp."""
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': caminho_destino,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return os.path.exists(caminho_destino) and os.path.getsize(caminho_destino) > 0
    except Exception as e:
        print(f"Erro ao baixar via yt-dlp: {e}")
        return False


def construir_comando_ffmpeg(
    input_path: str,
    output_path: str,
    coordenadas: tuple,
    altitude: float,
    config: dict
) -> bool:
    """Constrói e executa o comando FFmpeg para antiduplicação e limpeza de metadados."""
    try:
        lat, lon = coordenadas
        alt = altitude
        
        # Construção da cadeia de filtros vídeo (vf)
        filtros = []
        
        # 1. Micro Zoom
        zoom = config.get("zoom", 1.01)
        if zoom != 1.0:
            h = f"ih*{zoom}"
            w = f"iw*{zoom}"
            filtros.append(f"scale={w}:{h},crop=iw/({zoom}):ih/({zoom})")
        
        # 2. Espelhamento horizontal
        if config.get("hflip", False):
            filtros.append("hflip")
        
        # 3. Ajuste de cor/brilho/contraste/saturação
        brilho = config.get("brilho", 0.02)
        contraste = config.get("contraste", 1.02)
        saturacao = config.get("saturacao", 1.05)
        if brilho != 0.0 or contraste != 1.0 or saturacao != 1.0:
            filtros.append(f"eq=brightness={brilho}:contrast={contraste}:saturation={saturacao}")
        
        # 4. Modificação de FPS
        fps_mod = config.get("fps", 30.01)
        filtros.append(f"fps={fps_mod}")
        
        filter_complex_str = ",".join(filtros) if filtros else "null"
        
        # Construção da cadeia de áudio (afiltros) se protection sonora ativa
        audio_args = []
        if config.get("audio_morph", True):
            pitch = config.get("pitch", 1.005)
            tempo = config.get("tempo", 1.001)
            sample_rate = int(44100 * pitch)
            audio_args = [
                "-af", f"atempo={tempo},aresample={sample_rate}"
            ]
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", filter_complex_str,
        ]
        
        if audio_args:
            cmd.extend(audio_args)
            
        # Injeção cirúrgica de metadados limpos e geolocalização real
        iso6709 = f"{'+' if lat>=0 else ''}{lat:.4f}{'+' if lon>=0 else ''}{lon:.4f}{'+' if alt>=0 else ''}{alt:.1f}/"
        
        cmd.extend([
            "-map_metadata", "-1",
            "-metadata", "make=Apple",
            "-metadata", "model=iPhone 15 Pro Max",
            "-metadata", "software=17.4.1",
            "-metadata", "encoder=com.apple.avfoundation.avcapturesession",
            f"-metadata", f"creation_time={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000000Z')}",
            f"-metadata", f"location={iso6709}",
            f"-metadata", f"location-eng={iso6709}",
            f"-metadata", f"com.apple.quicktime.location.ISO6709={iso6709}",
            "-metadata", "comment=",
            "-metadata", "VidMd5=",
            "-c:v", "libx264",
            "-crf", "22",
            "-preset", "medium",
            "-y",
            output_path
        ])
        
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return resultado.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"Exception em construir_comando_ffmpeg: {e}")
        return False


def limpar_metadados_ffmpeg(
    input_path: str,
    output_path: str,
    coordenadas: tuple,
    altitude: float,
    config: dict
) -> bool:
    """Wrapper para execução do FFmpeg."""
    return construir_comando_ffmpeg(input_path, output_path, coordenadas, altitude, config)


def render_metadados_pro():
    st.markdown("## 🎬 Metadata Pro v10.0 — Antiduplicação & Limpeza")
    st.caption(
        "Envie um arquivo de vídeo ou cole o link do **TikTok / Instagram / YouTube**. "
        "O sistema altera a assinatura digital (hash), aplica micro-ajustes visuais/sonoros e injeta metadados de câmera realistas."
    )

    # ============================================================
    # ESCOLHA DE ENTRADA: UPLOAD OU LINK
    # ============================================================
    tipo_entrada = st.radio(
        "Selecione a forma de envio do vídeo:",
        ["📁 Upload de Arquivo (MP4, MOV, MKV)", "🔗 Colar Link (TikTok / Instagram / YouTube)"],
        horizontal=True,
        key="radio_tipo_entrada"
    )

    caminho_video_origem = None
    uploaded_file = None
    video_url = ""

    if "Upload" in tipo_entrada:
        with st.container(border=True):
            uploaded_file = st.file_uploader("Envie o vídeo", type=["mp4", "mov", "mkv"], key="uploader_meta_pro")
    else:
        with st.container(border=True):
            video_url = st.text_input(
                "Cole o link do vídeo (TikTok, Instagram Reels, YouTube Shorts, etc.):",
                placeholder="https://www.tiktok.com/@usuario/video/...",
                key="input_url_video"
            )

    # ============================================================
    # PAINEL DE ANTIDUPLICAÇÃO
    # ============================================================
    with st.expander("🛡️ Configurações Antiduplicação v9.8 & Câmera", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Visual**")
            zoom_val = st.slider("Micro Zoom", 1.0, 1.05, 1.01, format="%.2f", key="meta_zoom")
            hflip = st.checkbox("Inversão Horizontal (Espelhar)", value=False, key="meta_hflip")
            ajuste_cor = st.checkbox("Micro-ajuste de cor/brilho", value=True, key="meta_cor")
            fps_mod = st.selectbox("Variação de FPS", [29.97, 30.01, 60.01], index=1, key="meta_fps")
        with col2:
            st.markdown("**Sonoro (Audio Morphing)**")
            audio_morph = st.checkbox("Ativar Proteção Sonora", value=True, help="Altera levemente o tom e tempo para quebrar o rastro de áudio.", key="meta_audio")
            pitch_val = st.slider("Ajuste de Tom (Pitch)", 0.98, 1.02, 1.005, format="%.3f", disabled=not audio_morph, key="meta_pitch")
            tempo_val = st.slider("Ajuste de Tempo", 0.99, 1.01, 1.001, format="%.3f", disabled=not audio_morph, key="meta_tempo")

    antidup_config = {
        "zoom": zoom_val,
        "brilho": 0.02 if ajuste_cor else 0.0,
        "contraste": 1.02 if ajuste_cor else 1.0,
        "saturacao": 1.05 if ajuste_cor else 1.0,
        "hflip": hflip,
        "fps": fps_mod,
        "audio_morph": audio_morph,
        "pitch": pitch_val,
        "tempo": tempo_val,
    }

    # Validação de prontidão para processar
    pronto = False
    if "Upload" in tipo_entrada and uploaded_file is not None:
        pronto = True
    elif "Link" in tipo_entrada and video_url and validar_url_video(video_url):
        pronto = True

    if not pronto:
        st.info("Aguardando o envio do arquivo ou inserção de um link válido para prosseguir.")
        return

    if st.button("🚀 Processar e Limpar Metadados", type="primary", use_container_width=True):
        barra_status = st.progress(0, text="Iniciando processamento...")
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_in:
            caminho_in = temp_in.name
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_out:
            caminho_out = temp_out.name
        
        try:
            # 1. Obtenção do vídeo (Upload ou Download via Link)
            if "Upload" in tipo_entrada:
                barra_status.progress(20, text="Salvando arquivo enviado...")
                with open(caminho_in, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            else:
                barra_status.progress(10, text="Baixando vídeo da plataforma (TikTok/Instagram)...")
                if not baixar_video_yt_dlp(video_url, caminho_in):
                    st.error("❌ Falha ao baixar o vídeo do link fornecido. Verifique se o link é público e válido.")
                    return
                barra_status.progress(40, text="Download concluído com sucesso!")
            
            # 2. Processamento FFmpeg (Antiduplicação e Limpeza)
            barra_status.progress(60, text="Aplicando Antiduplicação e Limpando Metadados...")
            loc = random.choice(LOCALIZACOES_REAIS)
            coordenadas = (loc["lat"], loc["lon"])
            
            sucesso = limpar_metadados_ffmpeg(
                caminho_in,
                caminho_out,
                coordenadas,
                loc["alt"],
                antidup_config
            )
            
            barra_status.progress(100, text="✅ Processamento concluído com sucesso!")
            
            if sucesso and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
                nome_final = gerar_nome_arquivo_limpo()
                with open(caminho_out, "rb") as f:
                    dados_saida = f.read()
                
                st.download_button(
                    label=f"📥 Baixar Vídeo Pronto para Postar ({nome_final})",
                    data=dados_saida,
                    file_name=nome_final,
                    mime="video/mp4",
                    use_container_width=True
                )
                st.success("🎉 Vídeo processado com sucesso! Assinatura digital alterada e metadados limpos.")
            else:
                st.error("❌ Falha ao processar o vídeo no FFmpeg.")
                
        except Exception as e:
            st.error(f"❌ Erro durante o processamento: {str(e)}")
        finally:
            for p in [caminho_in, caminho_out]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except:
                        pass


__all__ = ["render_metadados_pro"]
