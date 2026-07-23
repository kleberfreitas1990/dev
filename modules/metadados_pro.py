import os
import random
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import streamlit as st
import yt_dlp

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

REDES_SUPORTADAS = (
    "tiktok.com",
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "twitter.com",
    "x.com",
)


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


def baixar_video_de_url_direta(url: str, output_path: str) -> bool:
    """Baixa um vídeo de uma URL direta para um ficheiro temporário."""
    try:
        with requests.get(url, stream=True, timeout=(10, 120)) as resposta:
            resposta.raise_for_status()
            with open(output_path, "wb") as ficheiro:
                for chunk in resposta.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        ficheiro.write(chunk)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as exc:
        st.error(f"Erro ao descarregar o vídeo da URL direta: {exc}")
        return False


def baixar_video_yt_dlp(url: str, output_path: str) -> bool:
    """Descarrega um vídeo de uma plataforma suportada através de yt-dlp."""
    try:
        opcoes = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": output_path,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "no_color": True,
            "socket_timeout": 60,
            "retries": 10,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            },
        }
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as exc:
        st.error(f"Erro ao descarregar o vídeo com yt-dlp: {exc}")
        return False


def construir_comando_ffmpeg(
    input_path: str,
    output_path: str,
    coordenadas=None,
    altitude=None,
    antidup_config=None,
):
    """
    Constrói o comando FFmpeg v9.6 focado em antiduplicação.
    Implementa reencodificação profunda e micro-ajustes visuais.
    """
    creation_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    
    # Configuração padrão de antiduplicação
    if antidup_config is None:
        antidup_config = {
            "zoom": 1.01,          # 1% de zoom
            "brilho": 0.02,        # +2% de brilho
            "contraste": 1.02,     # +2% de contraste
            "saturacao": 1.05,     # +5% de saturação
            "hflip": False,        # Inversão horizontal
            "fps": 30.01,          # Micro ajuste de FPS
        }

    # Filtros de vídeo para quebrar a assinatura visual (Antiduplicação)
    video_filters = []
    
    # 1. Zoom e Recorte (Zoom de 1% para mudar o enquadramento em pixels)
    # Usamos scale + crop para simular zoom sem perder proporção
    video_filters.append(f"scale=iw*{antidup_config['zoom']}:-1")
    video_filters.append("crop=iw/1.01:ih/1.01")
    
    # 2. Ajustes de Cor (Imperceptíveis ao olho, mas mudam os valores RGB/YUV)
    # eq=brightness:contrast:saturation
    video_filters.append(
        f"eq=brightness={antidup_config['brilho']}:contrast={antidup_config['contraste']}:saturation={antidup_config['saturacao']}"
    )
    
    # 3. Inversão Horizontal (Opcional)
    if antidup_config.get("hflip"):
        video_filters.append("hflip")
        
    # 4. Micro ajuste de FPS (Muda o timing dos frames)
    video_filters.append(f"fps=fps={antidup_config['fps']}")

    filter_complex = ",".join(video_filters)

    comando = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i", input_path,
        # v9.7: Limpeza e Disfarce de Encoder
        "-map_metadata", "-1",
        "-map_chapters", "-1",
        "-fflags", "+bitexact",
        "-flags:v", "+bitexact",
        "-flags:a", "+bitexact",

        # Reencodificação Profunda
        "-c:v", "libx264",
        "-preset", "medium", 
        "-crf", "20",
        "-vf", filter_complex,
        "-pix_fmt", "yuv420p",
        # Áudio reencodificado com Morphing (v9.8)
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
    ]

    if antidup_config.get("audio_morph"):
        # Aplica rubberband para pitch e atempo para ajuste fino de tempo
        # rubberband=pitch=X:tempo=Y
        audio_filters = [f"rubberband=pitch={antidup_config['pitch']}", f"atempo={antidup_config['tempo']}"]
        comando.extend(["-af", ",".join(audio_filters)])

    comando.extend([

        # Injeção de metadados simulando hardware nativo
        "-metadata", f"creation_time={creation_time}",
        "-metadata", "encoder=Camera",
        "-metadata:s:v", "encoder=Camera",
        "-metadata:s:a", "encoder=Camera",
        "-metadata:s:v", "handler_name=VideoHandler",
        "-metadata:s:a", "handler_name=SoundHandler",
        "-metadata", "make=Apple",
        "-metadata", "model=iPhone 15 Pro",
        "-metadata", "software=iOS 17.5.1",
        # Força o container a esconder o rastro do Lavf
        "-brand", "mp42",
        "-movflags", "+faststart",
    ])

    if coordenadas:
        latitude, longitude = coordenadas
        iso6709 = f"{latitude:+.4f}{longitude:+.4f}/"
        if altitude:
            iso6709 = f"{latitude:+.4f}{longitude:+.4f}{float(altitude):+.0f}CRS/"
        comando.extend(["-metadata", f"com.apple.quicktime.location.ISO6709={iso6709}"])

    comando.extend(["-y", output_path])
    return comando


def limpar_metadados_ffmpeg(input_path, output_path, coordenadas=None, altitude=None, antidup_config=None):
    """Executa a limpeza v9.6 com Antiduplicação."""
    comando = construir_comando_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        coordenadas=coordenadas,
        altitude=altitude,
        antidup_config=antidup_config
    )

    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=600)
        if resultado.returncode != 0:
            st.error(f"Erro no processamento: {resultado.stderr[-500:]}")
            return False
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        st.error(f"Falha na execução do FFmpeg: {e}")
        return False


def render_metadados_pro():
    st.markdown("## 🎬 Metadata Pro v9.6 — Antiduplicação Shopee")
    st.caption(
        "A Shopee pune vídeos duplicados. Esta ferramenta altera a assinatura digital (hash) "
        "e aplica micro-ajustes visuais para que o vídeo seja visto como conteúdo original."
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader("Envie o vídeo", type=["mp4", "mov", "mkv"])
        video_url = "" # Mantido vazio para compatibilidade

    if not uploaded_file:
        st.info("Aguardando vídeo para processamento.")
        return

    # Painel de Antiduplicação
    with st.expander("🛡️ Configurações Antiduplicação v9.8", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Visual**")
            zoom_val = st.slider("Micro Zoom", 1.0, 1.05, 1.01, format="%.2f")
            hflip = st.checkbox("Inversão Horizontal (Espelhar)", value=False)
            ajuste_cor = st.checkbox("Micro-ajuste de cor/brilho", value=True)
            fps_mod = st.selectbox("Variação de FPS", [29.97, 30.01, 60.01], index=1)
        with col2:
            st.markdown("**Sonoro (Audio Morphing)**")
            audio_morph = st.checkbox("Ativar Proteção Sonora", value=True, help="Altera levemente o tom e tempo para quebrar o rastro de áudio.")
            pitch_val = st.slider("Ajuste de Tom (Pitch)", 0.98, 1.02, 1.005, format="%.3f", disabled=not audio_morph)
            tempo_val = st.slider("Ajuste de Tempo", 0.99, 1.01, 1.001, format="%.3f", disabled=not audio_morph)

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

    if st.button("🚀 Processar e Gerar Original", type="primary", use_container_width=True):
        progresso = st.progress(0, text="Iniciando...")
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_in:
            caminho_in = temp_in.name
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_out:
            caminho_out = temp_out.name

        try:
            # 1. Carregamento
            with open(caminho_in, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 2. Processamento FFmpeg
            progresso.progress(50, text="Aplicando Antiduplicação e Limpando Metadados...")
            loc = random.choice(LOCALIZACOES_REAIS)
            coordenadas = (loc["lat"], loc["lon"])
            
            if limpar_metadados_ffmpeg(caminho_in, caminho_out, coordenadas, loc["alt"], antidup_config):
                progresso.progress(100, text="Concluído!")
                nome_final = gerar_nome_arquivo_limpo()
                with open(caminho_out, "rb") as f:
                    st.download_button(
                        label=f"📥 Baixar Vídeo Original ({nome_final})",
                        data=f.read(),
                        file_name=nome_final,
                        mime="video/mp4",
                        use_container_width=True
                    )
                st.success("✅ Vídeo pronto para postar na Shopee! Assinatura digital alterada.")
            else:
                st.error("Falha ao processar vídeo.")
        finally:
            for p in [caminho_in, caminho_out]:
                if os.path.exists(p):
                    os.remove(p)

__all__ = ["render_metadados_pro"]
