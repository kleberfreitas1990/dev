"""
Módulo Metadados Pro v10.2 + Download Robusto TikTok/Instagram + Preview
======================================================================
Interface Streamlit unificada para:
1. Upload manual de arquivo ou download direto via link (TikTok / Instagram / YouTube) com botão de "Identificar Vídeo" e preview
2. Antiduplicação visual e sonora (micro-zoom, espelhamento, áudio morphing)
3. Limpeza cirúrgica de metadados, remoção de GPS e injeção de perfil de câmera realista

Autor: Manus AI
Versão: 10.2.0
"""

import os
import random
import shutil
import subprocess
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlparse

import requests
import streamlit as st
import yt_dlp
import cv2
import numpy as np

ENCODER_METADATA = "Apple H.264 Camcorder"
FPS_PERMITIDOS = (30.0, 29.97)
LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


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


def gerar_nome_arquivo_limpo(extensao: str = ".MOV") -> str:
    """Gera o nome obrigatório de câmera: IMG_XXXX.MOV."""
    return f"IMG_{random.randint(0, 9999):04d}.MOV"


def normalizar_fps(valor: float) -> float:
    """Restringe a saída aos dois padrões aceitos: 30.00 ou 29.97 fps."""
    try:
        fps = float(valor)
    except (TypeError, ValueError):
        return FPS_PERMITIDOS[0]

    if abs(fps - 29.97) < 0.001:
        return 29.97
    if abs(fps - 30.0) < 0.001:
        return 30.0
    return FPS_PERMITIDOS[0]


def formatar_localizacao_iso6709(coordenadas: tuple, altitude: float) -> str:
    """Gera a forma ISO 6709 usada pela chave QuickTime de localização."""
    lat, lon = coordenadas
    return f"{float(lat):+.5f}{float(lon):+010.5f}{float(altitude):+.1f}/"


def validar_url_video(url: str) -> bool:
    """Aceita apenas URLs HTTP(S) completas."""
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def baixar_video_yt_dlp(url: str, caminho_destino: str) -> bool:
    """
    Motor de download multi-estratégia ultra-robusto para TikTok, Instagram e YouTube.
    Utiliza estratégias combinadas de yt-dlp com headers atualizados e APIs de contorno de bloqueio.
    """
    clean_url = url.strip()
    
    # Estratégia 1: yt-dlp com configuração mobile/desktop avançada e bypass de geofence/bot
    estrategias = [
        {
            'format': 'best[ext=mp4]/best',
            'outtmpl': caminho_destino,
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractor_args': {'tiktok': {'app_info': '7.2.0'}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        },
        {
            'format': 'best',
            'outtmpl': caminho_destino,
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        },
        {
            'format': 'bv*+ba/b',
            'outtmpl': caminho_destino,
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
        }
    ]

    for idx, opts in enumerate(estrategias):
        try:
            # Remove arquivo anterior se existir
            if os.path.exists(caminho_destino):
                os.remove(caminho_destino)
                
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([clean_url])
                
            if os.path.exists(caminho_destino) and os.path.getsize(caminho_destino) > 1024:
                return True
        except Exception as e:
            print(f"Estratégia de download {idx+1} falhou: {e}")
            continue

    # Estratégia de Fallback com API pública de espelhamento/proxy se yt-dlp falhar por completo
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
        # Tenta requisição direta caso seja link direto de mídia
        resp = requests.get(clean_url, headers=headers, timeout=15, stream=True)
        if resp.status_code == 200 and 'video' in resp.headers.get('content-type', ''):
            with open(caminho_destino, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.exists(caminho_destino) and os.path.getsize(caminho_destino) > 1024:
                return True
    except Exception as e:
        print(f"Fallback de requisição direta falhou: {e}")

    return False


def extrair_primeiro_frame(caminho_video: str) -> np.ndarray:
    """Extrai o primeiro frame do vídeo para visualização."""
    cap = cv2.VideoCapture(caminho_video)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise ValueError("Não foi possível ler o primeiro frame do vídeo")
    return frame


def obter_informacoes_video(caminho_video: str) -> dict:
    """Extrai informações técnicas do vídeo."""
    cap = cv2.VideoCapture(caminho_video)
    info = {
        "largura": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "altura": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duracao_segundos": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30))
    }
    cap.release()
    return info


def normalizar_encoder_mp4(output_path: str) -> bool:
    """Substitui a tag global automática do muxer sem recodificar MP4/MOV."""
    arquivo_saida = Path(output_path)
    if arquivo_saida.suffix.lower() not in {".mp4", ".mov"} or not arquivo_saida.is_file() or arquivo_saida.stat().st_size == 0:
        return False

    temporario = None
    try:
        from mutagen.mp4 import MP4, MP4Tags

        with tempfile.NamedTemporaryFile(
            prefix=f".{arquivo_saida.name}.",
            suffix=".tmp",
            dir=arquivo_saida.parent,
            delete=False,
        ) as arquivo_tmp:
            temporario = Path(arquivo_tmp.name)

        shutil.copy2(arquivo_saida, temporario)
        mp4 = MP4(str(temporario))
        tags = mp4.tags or MP4Tags()
        tags["©too"] = [ENCODER_METADATA]
        mp4.tags = tags
        mp4.save()
        os.replace(temporario, arquivo_saida)
        temporario = None
        return True
    except Exception as exc:
        print(f"Falha ao normalizar a tag global do MP4: {exc}")
        return False
    finally:
        if temporario is not None:
            try:
                temporario.unlink(missing_ok=True)
            except OSError:
                pass


def normalizar_location_information_quicktime(
    output_path: str,
    coordenadas: tuple,
    altitude: float,
    nome_localizacao: str,
) -> bool:
    """Escreve o campo QuickTime legado que o ExifTool exibe como LocationInformation."""
    exiftool = shutil.which("exiftool")
    if not exiftool:
        print("ExifTool não encontrado; não foi possível gravar LocationInformation.")
        return False

    lat, lon = coordenadas
    iso6709 = formatar_localizacao_iso6709((lat, lon), altitude)
    location_value = (
        f"{nome_localizacao} Role=shooting "
        f"Lat={float(lat):+.5f} Lon={float(lon):+.5f} "
        f"Alt={float(altitude):.2f} Body=earth Notes="
    )
    try:
        resultado = subprocess.run(
            [
                exiftool,
                "-overwrite_original",
                f"-LocationInformation={location_value}",
                f"-Keys:GPSCoordinates={iso6709}",
                f"-Keys:LocationName={nome_localizacao}",
                "-Keys:LocationBody=earth",
                "-Keys:LocationRole#=0",
                output_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return resultado.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Falha ao gravar LocationInformation no QuickTime: {exc}")
        return False


def construir_comando_ffmpeg(
    input_path: str,
    output_path: str,
    coordenadas: tuple,
    altitude: float,
    config: dict
) -> bool:
    """
    Constrói e executa o comando FFmpeg ultra-otimizado (Ghost Mode).
    Limpa metadados, força resolução exata 1080x1920 e aplica uma identificação
    explícita de encoder no stream de vídeo; a tag global do MP4 é normalizada
    depois da codificação porque o muxer costuma recriá-la automaticamente.
    """
    try:
        lat, lon = coordenadas
        alt = altitude
        
        # Pipeline de filtros garantindo escala exata 1080x1920 (Full HD vertical nativo de smartphone)
        filtros = []
        zoom = config.get("zoom", 1.01)
        if zoom != 1.0:
            h = f"ih*{zoom}"
            w = f"iw*{zoom}"
            filtros.append(f"scale={w}:{h},crop=iw/({zoom}):ih/({zoom})")
        
        # Força dimensões codificadas exatas e pixels quadrados, sem depender do
        # SAR/DAR do arquivo de origem, que pode fazer leitores exibirem 1083/1084 px.
        filtros.append(
            "scale=1080:1920:force_original_aspect_ratio=decrease:flags=bicubic,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1/1,setdar=9/16"
        )
        
        if config.get("hflip", False):
            filtros.append("hflip")
        
        brilho = config.get("brilho", 0.02)
        contraste = config.get("contraste", 1.02)
        saturacao = config.get("saturacao", 1.05)
        if brilho != 0.0 or contraste != 1.0 or saturacao != 1.0:
            filtros.append(f"eq=brightness={brilho}:contrast={contraste}:saturation={saturacao}")
        
        fps_mod = normalizar_fps(config.get("fps", 30.0))
        fps_filter = "30000/1001" if fps_mod == 29.97 else "30"
        filtros.append(f"fps={fps_filter}")
        
        filter_complex_str = ",".join(filtros)
        
        audio_args = []
        if config.get("audio_morph", True):
            pitch = config.get("pitch", 1.005)
            tempo = config.get("tempo", 1.001)
            sample_rate = int(44100 * pitch)
            audio_args = [
                "-af", f"atempo={tempo},aresample={sample_rate}"
            ]
        
        # O contêiner armazena creation_time em UTC, mas o valor local explícito
        # mantém o horário correto de São Paulo/Brasília para leitores Apple.
        agora_local = datetime.now(LOCAL_TIMEZONE)
        agora_consistente = agora_local.isoformat(timespec="seconds")
        creationdate_local = agora_consistente
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", filter_complex_str,
        ]
        
        if audio_args:
            cmd.extend(audio_args)
            
        iso6709 = formatar_localizacao_iso6709((lat, lon), alt)
        nome_localizacao = str(config.get("location_name", "Brasil")).strip() or "Brasil"
        
        cmd.extend([
            # Limpa metadados globais, de streams e capítulos anteriores.
            "-map_metadata", "-1",
            "-map_metadata:s:v", "-1",
            "-map_metadata:s:a", "-1",
            "-map_chapters", "-1",
            
            # Identificação explícita da codificação de vídeo.
            "-metadata", f"encoder={ENCODER_METADATA}",
            "-metadata:s:v:0", f"encoder={ENCODER_METADATA}",
            # Não deixa o encoder de áudio regravado pelo FFmpeg aparecer como Lavc.
            "-metadata:s:a:0", "encoder=",
            "-metadata", "make=Apple",
            "-metadata", "model=iPhone 15 Pro Max",
            "-metadata", "software=iOS 17.4.1",
            "-metadata", "handler_name=Core Media Video",
            
            # Horário do instante de gravação: o MOV normaliza creation_time
            # para UTC; creationdate preserva explicitamente o offset local -03:00.
            "-metadata", f"creation_time={agora_consistente}",
            "-metadata", f"com.apple.quicktime.creationdate={creationdate_local}",
            
            # Localização Apple/QuickTime em ISO 6709. A flag use_metadata_tags
            # cria a chave mdta com.apple.quicktime.location.ISO6709.
            "-metadata", f"location={iso6709}",
            "-metadata", f"location-eng={iso6709}",
            "-metadata", f"com.apple.quicktime.location.ISO6709={iso6709}",
            "-metadata", f"com.apple.quicktime.location.name={nome_localizacao}",
            
            # Limpeza de campos residuais que entregam automação
            "-metadata", "comment=",
            "-metadata", "description=",
            "-metadata", "title=",
            "-metadata", "artist=",
            "-metadata", "composer=",
            "-metadata", "genre=",
            "-metadata", "encoder_version=",
            
            # Codificação H.264 e supressão das assinaturas automáticas do FFmpeg.
            "-c:v", "libx264",
            "-crf", "21",
            "-preset", "slow",
            "-profile:v", "main",
            "-level", "4.0",
            "-fflags", "+bitexact",
            "-flags:v", "+bitexact",
            "-flags:a", "+bitexact",
            # Evita que o x264 injete a string Lavc no SEI do bitstream H.264.
            "-x264-params", "info=0",
            
            "-movflags", "+faststart+use_metadata_tags",
            "-f", "mov",
            "-y",
            output_path
        ])
        
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        ffmpeg_sucesso = (
            resultado.returncode == 0
            and os.path.exists(output_path)
            and os.path.getsize(output_path) > 0
        )
        if not ffmpeg_sucesso or not normalizar_encoder_mp4(output_path):
            return False
        return normalizar_location_information_quicktime(
            output_path,
            (lat, lon),
            alt,
            nome_localizacao,
        )

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
    st.markdown("## 🎬 Metadata Pro v10.2 — Antiduplicação & Limpeza")
    st.caption(
        "Envie um arquivo de vídeo ou cole o link do **TikTok / Instagram / YouTube**. "
        "Utilize o botão de identificação para visualizar o vídeo antes de processar."
    )

    tipo_entrada = st.radio(
        "Selecione a forma de envio do vídeo:",
        ["📁 Upload de Arquivo (MP4, MOV, MKV)", "🔗 Colar Link (TikTok / Instagram / YouTube)"],
        horizontal=True,
        key="radio_tipo_entrada"
    )

    caminho_video_pronto = None
    uploaded_file = None
    video_url = ""

    if "Upload" in tipo_entrada:
        with st.container(border=True):
            uploaded_file = st.file_uploader("Envie o vídeo", type=["mp4", "mov", "mkv"], key="uploader_meta_pro")
            if uploaded_file is not None:
                # Salva em temporário para uso posterior
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_up:
                    tmp_up.write(uploaded_file.getbuffer())
                    caminho_video_pronto = tmp_up.name
    else:
        with st.container(border=True):
            st.markdown("### 🔗 Download de Vídeo por Link")
            video_url = st.text_input(
                "Cole o link do vídeo (TikTok, Instagram Reels, YouTube Shorts, etc.):",
                placeholder="https://www.tiktok.com/@usuario/video/...",
                key="input_url_video"
            )
            
            # Botão destacado logo abaixo da URL com largura total
            identificar_clicado = st.button("🔍 Clique Aqui para Identificar e Baixar Vídeo", type="primary", use_container_width=True)
            
            if identificar_clicado:
                if not video_url or not validar_url_video(video_url):
                    st.error("❌ Por favor, cole uma URL válida (com http:// ou https://) antes de clicar em identificar.")
                else:
                    with st.spinner("⏳ Baixando vídeo da rede social e gerando preview..."):
                        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_dl:
                            caminho_dl = tmp_dl.name
                        
                        sucesso_dl = baixar_video_yt_dlp(video_url, caminho_dl)
                        if sucesso_dl:
                            st.session_state['cached_video_url'] = video_url
                            st.session_state['cached_video_path'] = caminho_dl
                            st.success("✅ Vídeo baixado e identificado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Não foi possível baixar o vídeo. Verifique se o link é público e tente novamente.")
            
            # Se já foi baixado na sessão atual
            if 'cached_video_path' in st.session_state and os.path.exists(st.session_state['cached_video_path']):
                caminho_video_pronto = st.session_state['cached_video_path']
                try:
                    info_v = obter_informacoes_video(caminho_video_pronto)
                    frm_v = extrair_primeiro_frame(caminho_video_pronto)
                    h_d = 280
                    p_d = h_d / (frm_v.shape[0] or 1)
                    w_d = int(frm_v.shape[1] * p_d)
                    frm_res = cv2.resize(frm_v, (w_d, h_d))
                    
                    st.markdown("---")
                    st.success(f"✅ **Vídeo Carregado com Sucesso!** Resolução: `{info_v['largura']}×{info_v['altura']}` | Duração: `{info_v['duracao_segundos']}s`")
                    st.image(
                        cv2.cvtColor(frm_res, cv2.COLOR_BGR2RGB),
                        caption="📸 Miniatura (Primeiro Frame) do Vídeo",
                        use_column_width=True
                    )
                except Exception as e:
                    st.warning(f"Não foi possível renderizar o preview: {e}")

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
            fps_mod = st.selectbox(
                "Taxa de quadros da saída",
                [30.0, 29.97],
                index=0,
                format_func=lambda valor: f"{valor:.2f} fps",
                key="meta_fps",
            )
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
        "location_name": "",
    }

    if not caminho_video_pronto or not os.path.exists(caminho_video_pronto):
        st.info("Aguardando o envio do arquivo ou identificação do vídeo via link para prosseguir.")
        return

    if st.button("🚀 Processar e Limpar Metadados", type="primary", use_container_width=True):
        barra_status = st.progress(0, text="Iniciando processamento...")
        
        with tempfile.NamedTemporaryFile(suffix=".mov", delete=False) as temp_out:
            caminho_out = temp_out.name
        
        try:
            barra_status.progress(50, text="Aplicando Antiduplicação e Limpando Metadados (FFmpeg)...")
            loc = random.choice(LOCALIZACOES_REAIS)
            coordenadas = (loc["lat"], loc["lon"])
            antidup_config["location_name"] = loc["cidade"]
            
            sucesso = limpar_metadados_ffmpeg(
                caminho_video_pronto,
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
                    mime="video/quicktime",
                    use_container_width=True
                )
                st.success("🎉 Vídeo processado com sucesso! Assinatura digital alterada e metadados limpos.")
            else:
                st.error("❌ Falha ao processar o vídeo no FFmpeg.")
                
        except Exception as e:
            st.error(f"❌ Erro durante o processamento: {str(e)}")
        finally:
            if caminho_out and os.path.exists(caminho_out):
                try:
                    os.remove(caminho_out)
                except:
                    pass


__all__ = ["render_metadados_pro"]
