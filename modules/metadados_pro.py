import streamlit as st
import os
import subprocess
import random
import time
import requests
import shutil
import yt_dlp
from datetime import datetime, timedelta
from app import PERFIS_CAMERA, LOCALIZACOES_REAIS # Importar para acessar resoluções e altitudes

def gerar_nome_arquivo_real(dispositivo, extensao=".mp4"):
    """Gera um nome de arquivo idêntico ao de uma câmera real"""
    num = random.randint(1000, 9999)
    if dispositivo == "Apple":
        return f"IMG_{num}{extensao}"
    else:
        return f"VID_{datetime.now().strftime('%Y%m%d')}_{num}{extensao}"

def baixar_video_de_url_direta(url: str, output_path: str) -> bool:
    """Baixa um vídeo de uma URL direta para o caminho especificado."""
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao baixar vídeo da URL direta: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Erro inesperado no download direto: {e}")
        return False

def baixar_video_yt_dlp(url: str, output_path: str) -> bool:
    """Baixa um vídeo de plataformas sociais usando yt-dlp."""
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except yt_dlp.utils.DownloadError as e:
        st.error(f"❌ Erro ao baixar vídeo com yt-dlp: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Erro inesperado no download com yt-dlp: {e}")
        return False

def limpar_e_injetar_metadados_ffmpeg(input_path, output_path, dispositivo, coordenadas=None, altitude=None, resolucao_alvo=None):
    """
    Camuflagem Profunda:
    - Remove o rastro 'Lavf' (Software Encoder)
    - Injeta VendorID Apple real
    - Remove qualquer rastro de processamento
    """
    try:
        # Verificar se ffmpeg está disponível
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
        except FileNotFoundError:
            st.error("❌ FFmpeg não encontrado. Verifique o packages.txt.")
            return False

        # 1. Configurações de Camuflagem
        if dispositivo == "Apple":
            make = "Apple"
            model = random.choice(["iPhone 14 Pro", "iPhone 15 Pro Max"])
            # Encoder camuflado para parecer nativo da Apple
            encoder = "com.apple.avfoundation.avcapturesession"
            vendor = "apl0" # Apple Vendor ID
        else:
            make = "Samsung"
            model = "SM-S918B"
            encoder = "OMX.SEC.AVC.Encoder"
            vendor = "samsung"

        # Jitter de data/hora mais orgânico
        dias_atras = random.randint(1, 90) # Até 3 meses atrás
        horas_atras = random.randint(0, 23)
        minutos_atras = random.randint(0, 59)
        segundos_atras = random.randint(0, 59)
        data_retro = datetime.now() - timedelta(days=dias_atras, hours=horas_atras, minutes=minutos_atras, seconds=segundos_atras)
        creation_time = data_retro.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

        # 2. Comando FFmpeg com flags de camuflagem
        # -fflags +bitexact: Remove o rastro do Lavf no cabeçalho
        # -flags:v +bitexact -flags:a +bitexact: Garante que streams não tenham marcas
        cmd = [
            'ffmpeg', '-i', input_path,
            '-map_metadata', '-1',           # Limpa TUDO primeiro
            '-fflags', '+bitexact',          # REMOVE RASTRO LAVF (CRÍTICO)
            '-flags:v', '+bitexact',
            '-flags:a', '+bitexact',
            '-metadata', f'make={make}',
            '-metadata', f'model={model}',
            '-metadata', f'encoder={encoder}',
            '-metadata', f'creation_time={creation_time}',
            '-metadata', f'major_brand=qt  ', # Força formato QuickTime/Apple
            '-metadata', f'minor_version=0',
            '-metadata', f'compatible_brands=qt  ',
            '-metadata:s:v', f'handler_name=VideoHandler',
            '-metadata:s:v', f'vendor_id={vendor}',
            '-metadata:s:a', f'handler_name=SoundHandler',
            '-metadata:s:a', f'vendor_id={vendor}',
            '-c:v', 'libx264',               # Re-encodar vídeo com H.264
            '-preset', 'medium',             # Qualidade média para equilíbrio
            '-crf', '23',                    # Constant Rate Factor para VBR (Variable Bitrate)
            '-c:a', 'aac',                   # Re-encodar áudio com AAC
            '-b:a', '128k',                  # Bitrate de áudio
        ]
        if resolucao_alvo:
            # Exemplo: '1920x1080' ou '3840x2160'
            # Inverte para formato vertical se for celular
            width, height = map(int, resolucao_alvo.split('x'))
            if width > height:
                width, height = height, width # Força vertical (ex: 1080x1920)
            cmd.extend(['-vf', f'scale={width}:{height}']) # Redimensiona para resolução nativa

        if coordenadas:
            lat, lon = coordenadas
            iso6709 = f"{lat:+.4f}{lon:+.4f}/"
            cmd.extend([
                '-metadata', f'location={iso6709}',
                '-metadata', f'location-eng={iso6709}',
                '-metadata', f'com.apple.quicktime.location.ISO6709={iso6709}',
            ])
            if altitude is not None:
                cmd.extend(['-metadata', f'location_alt={altitude:.0f}']) # Injeta altitude

        cmd.extend(['-y', output_path])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return False

def processar_video_completo(input_source, is_url, dispositivo, usar_gps, resolucao_alvo, nome_sugerido):
    """Encapsula o fluxo completo de download e higienização"""
    progress = st.progress(0, text="Iniciando processamento...")
    temp_in = f"raw_{random.randint(100,999)}.mp4"
    temp_out = nome_sugerido
    
    try:
        if not is_url:
            with open(temp_in, "wb") as f:
                f.write(input_source.getbuffer())
            progress.progress(20, text="Arquivo local carregado...")
        else:
            progress.progress(20, text="Baixando vídeo da URL...")
            if any(domain in input_source for domain in ['tiktok.com', 'instagram.com', 'youtube.com', 'youtu.be', 'twitter.com', 'x.com']):
                sucesso_download = baixar_video_yt_dlp(input_source, temp_in)
            else:
                sucesso_download = baixar_video_de_url_direta(input_source, temp_in)
            
            if not sucesso_download:
                st.error("❌ Falha ao baixar o vídeo da URL.")
                return False
            progress.progress(40, text="Vídeo baixado. Iniciando camuflagem...")

        # Coordenadas e Altitude
        altitude = None
        if usar_gps:
            cidade_escolhida = st.session_state.get("select_cidade_gps")
            if cidade_escolhida:
                loc_info = next((l for l in LOCALIZACOES_REAIS if l["cidade"] == cidade_escolhida), None)
                if loc_info and "alt" in loc_info:
                    altitude = loc_info["alt"]
            coordenadas = (-23.5505 + random.uniform(-0.01, 0.01), -46.6333 + random.uniform(-0.01, 0.01))
        else:
            coordenadas = None

        if limpar_e_injetar_metadados_ffmpeg(temp_in, temp_out, dispositivo, coordenadas, altitude, resolucao_alvo):
            progress.progress(100, text="✅ Processamento concluído!")
            st.balloons()
            
            with open(temp_out, "rb") as f:
                st.download_button(
                    label=f"📥 Baixar {nome_sugerido}",
                    data=f.read(),
                    file_name=nome_sugerido,
                    mime="video/mp4",
                    use_container_width=True
                )
            return True
        else:
            st.error("❌ Falha na camuflagem.")
            return False
    finally:
        if os.path.exists(temp_in): os.remove(temp_in)
        if os.path.exists(temp_out): os.remove(temp_out)

def render_metadados_pro():
    st.markdown("# 🎬 Metadata Pro - Camuflagem Profunda")
    st.caption("Remoção total de rastros digitais (Lavf, FFmpeg) e injeção de hardware nativo.")
    
    # Inicializar estado para URL se não existir
    if "last_processed_url" not in st.session_state:
        st.session_state.last_processed_url = ""

    with st.container(border=True):
        modo_entrada = st.radio("Escolha a fonte do vídeo:", ["Upload de Arquivo", "URL de Vídeo"], horizontal=True)

        uploaded_file = None
        video_url = ""

        if modo_entrada == "Upload de Arquivo":
            uploaded_file = st.file_uploader("Upload do vídeo", type=["mp4", "mov"], key="up_meta_v64")
        else:
            video_url = st.text_input("Cole a URL do vídeo (TikTok, Instagram, YouTube, etc.)", key="url_meta_v64")

    if uploaded_file or video_url:
        col_cfg, col_res = st.columns(2)
        
        with col_cfg:
            dispositivo = st.radio("Simular Dispositivo:", ["Apple", "Samsung"], horizontal=True)
            usar_gps = st.checkbox("Injetar GPS Realista", value=True)
            
        with col_res:
            nome_sugerido = gerar_nome_arquivo_real(dispositivo)
            nome_original = uploaded_file.name if uploaded_file else "Vídeo de URL"
            st.info(f"📁 Fonte: `{nome_original}`")
            st.success(f"🛡️ Novo Nome: `{nome_sugerido}`")

        resolucao_alvo = PERFIS_CAMERA[st.session_state.get("select_perfil_camera")]["resolucao"] if st.session_state.get("select_perfil_camera") else None

        # Gatilho Automático para URL
        if video_url and video_url != st.session_state.last_processed_url:
            st.session_state.last_processed_url = video_url
            processar_video_completo(video_url, True, dispositivo, usar_gps, resolucao_alvo, nome_sugerido)
        
        # Botão Manual (sempre disponível para re-processar ou para Upload)
        if st.button("🚀 Executar Camuflagem Profunda", type="primary", use_container_width=True):
            if uploaded_file:
                processar_video_completo(uploaded_file, False, dispositivo, usar_gps, resolucao_alvo, nome_sugerido)
            elif video_url:
                processar_video_completo(video_url, True, dispositivo, usar_gps, resolucao_alvo, nome_sugerido)
            else:
                st.warning("Por favor, forneça um vídeo.")
