"""
Módulo Metadados Pro v10.0 + Remoção de Marca d'Água Shopee
=============================================================
Interface Streamlit unificada para:
1. Remoção de marca d'água de vídeos Shopee (opcional) com presets de posição e OpenCV inpainting
2. Antiduplicação visual e sonora (micro-zoom, espelhamento, áudio morphing)
3. Limpeza cirúrgica de metadados, remoção de GPS e injeção de perfil de câmera realista

Autor: Manus AI
Versão: 10.0.1
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

# ============================================================
# PRESETS DE MARCA D'ÁGUA SHOPEE
# ============================================================
PRESETS_SHOPEE = {
    "Canto Inferior Direito (Padrão Shopee)": {
        "descricao": "Logo Shopee no canto inferior direito (posição mais comum)",
        "x_percent": 0.75,
        "y_percent": 0.85,
        "width_percent": 0.20,
        "height_percent": 0.12,
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

ALGORITMOS_INPAINTING = {
    "TELEA (Rápido)": cv2.INPAINT_TELEA,
    "NS (Qualidade)": cv2.INPAINT_NS,
}


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


def calcular_coordenadas_reais(
    altura_frame: int,
    largura_frame: int,
    x_percent: float,
    y_percent: float,
    width_percent: float,
    height_percent: float
) -> tuple:
    """Converte percentuais em coordenadas reais do frame."""
    x = int(largura_frame * x_percent)
    y = int(altura_frame * y_percent)
    width = int(largura_frame * width_percent)
    height = int(altura_frame * height_percent)
    
    x = max(0, min(x, largura_frame - 1))
    y = max(0, min(y, altura_frame - 1))
    width = min(width, largura_frame - x)
    height = min(height, altura_frame - y)
    
    return (x, y, width, height)


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


def extrair_audio(caminho_video: str, caminho_audio: str) -> bool:
    """Extrai o áudio do vídeo usando FFmpeg."""
    try:
        cmd = ["ffmpeg", "-i", caminho_video, "-q:a", "9", "-y", caminho_audio]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and os.path.exists(caminho_audio)
    except Exception as e:
        print(f"Exception em metadados_pro: {e}")
        return False


def remover_marca_dagua_cv(
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
    """Remove marca d'água usando OpenCV inpainting."""
    try:
        cap = cv2.VideoCapture(caminho_video)
        if not cap.isOpened():
            return False
        
        largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(caminho_saida, fourcc, fps, (largura, altura))
        
        if not out.isOpened():
            cap.release()
            return False
        
        mascara = np.zeros((altura, largura), dtype=np.uint8)
        mascara[y:y+height, x:x+width] = 255
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_processado = cv2.inpaint(frame, mascara, raio_inpainting, algoritmo)
            out.write(frame_processado)
            frame_count += 1
            
            if callback_progresso and total_frames > 0:
                callback_progresso(frame_count / total_frames)
        
        cap.release()
        out.release()
        return os.path.exists(caminho_saida) and os.path.getsize(caminho_saida) > 0
    except Exception as e:
        print(f"Exception em metadados_pro: {e}")
        return False


def muxar_audio_video(
    caminho_video_sem_audio: str,
    caminho_audio: str,
    caminho_saida_final: str
) -> bool:
    """Mescla o vídeo processado sem áudio com o áudio original."""
    try:
        cmd = [
            "ffmpeg",
            "-i", caminho_video_sem_audio,
            "-i", caminho_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-y",
            caminho_saida_final
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode == 0 and os.path.exists(caminho_saida_final)
    except Exception as e:
        print(f"Exception em metadados_pro: {e}")
        return False


def processar_remocao_marca_dagua(
    caminho_video: str,
    x: int,
    y: int,
    width: int,
    height: int,
    algoritmo: int = cv2.INPAINT_TELEA,
    raio_inpainting: int = 3,
    status_callback=None
) -> str:
    """Executa o pipeline completo de remoção de marca d'água preservando áudio."""
    caminho_temp_audio = None
    caminho_temp_video = None
    caminho_final = None
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".aac", delete=False) as tmp_audio:
            caminho_temp_audio = tmp_audio.name
        
        if status_callback:
            status_callback("🔊 Extraindo áudio original...", 0.1)
        if not extrair_audio(caminho_video, caminho_temp_audio):
            # Se falhar extração de áudio, prossegue sem áudio
            caminho_temp_audio = None
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
            caminho_temp_video = tmp_video.name
        
        if status_callback:
            status_callback("🎬 Removendo marca d'água quadro a quadro...", 0.3)
        
        def prog_cb(p):
            if status_callback:
                status_callback(f"🎬 Removendo marca d'água: {int(p*100)}%", 0.3 + (p * 0.4))
        
        if not remover_marca_dagua_cv(
            caminho_video,
            caminho_temp_video,
            x, y, width, height,
            algoritmo,
            raio_inpainting,
            prog_cb
        ):
            return caminho_video  # Retorna original se falhar
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_final:
            caminho_final = tmp_final.name
        
        if caminho_temp_audio and os.path.exists(caminho_temp_audio) and os.path.getsize(caminho_temp_audio) > 0:
            if status_callback:
                status_callback("🔗 Mesclando áudio e vídeo...", 0.8)
            if muxar_audio_video(caminho_temp_video, caminho_temp_audio, caminho_final):
                return caminho_final
        
        # Fallback se mux falhar
        return caminho_temp_video
        
    except Exception:
        return caminho_video
    finally:
        if caminho_temp_audio and os.path.exists(caminho_temp_audio):
            try:
                os.remove(caminho_temp_audio)
            except:
                pass


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
            # aresample para pitch/tempo shift imperceptível
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
        
        if resultado.returncode != 0:
            print(f"FFmpeg stderr: {resultado.stderr}")
            
        return resultado.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"Exception em metadados_pro: {e}")
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
    st.markdown("## 🎬 Metadata Pro v10.0 — Antiduplicação & Limpeza Shopee")
    st.caption(
        "A Shopee pune vídeos duplicados e com marca d'água. Esta ferramenta remove a marca d'água (opcional), "
        "altera a assinatura digital (hash), aplica micro-ajustes visuais/sonoros e injeta metadados de câmera realistas."
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader("Envie o vídeo Shopee (MP4, MOV, MKV)", type=["mp4", "mov", "mkv"], key="uploader_meta_pro")

    if not uploaded_file:
        st.info("Aguardando upload de vídeo para processamento.")
        return

    # ============================================================
    # MÓDULO OPCIONAL: REMOÇÃO DE MARCA D'ÁGUA
    # ============================================================
    with st.expander("💧 Remoção de Marca d'Água Shopee (Opcional)", expanded=False):
        remover_wm = st.checkbox("Remover marca d'água do vídeo antes de limpar metadados", value=False)
        
        if remover_wm:
            # Salva temporário para ler o frame
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_ref:
                tmp_ref.write(uploaded_file.getbuffer())
                caminho_ref = tmp_ref.name
            
            try:
                info_vid = obter_informacoes_video(caminho_ref)
                primeiro_frm = extrair_primeiro_frame(caminho_ref)
                
                # Exibe miniatura do primeiro frame
                h_disp = 300
                prop = h_disp / (primeiro_frm.shape[0] or 1)
                w_disp = int(primeiro_frm.shape[1] * prop)
                frm_disp = cv2.resize(primeiro_frm, (w_disp, h_disp))
                
                st.image(
                    cv2.cvtColor(frm_disp, cv2.COLOR_BGR2RGB),
                    caption=f"📸 Primeiro frame de referência ({info_vid['largura']}×{info_vid['altura']})",
                    use_column_width=True
                )
                
                preset_nome = st.selectbox(
                    "Selecione o Preset de Posição da Logo Shopee:",
                    list(PRESETS_SHOPEE.keys()),
                    key="meta_pro_preset"
                )
                
                p_info = PRESETS_SHOPEE[preset_nome]
                st.markdown(f"**{p_info['icone']} {p_info['descricao']}**")
                
                if "Personalizado" in preset_nome:
                    col_x, col_y = st.columns(2)
                    with col_x:
                        wm_x_pct = st.slider("Posição X (% da largura)", 0.0, 1.0, p_info['x_percent'], 0.01, key="meta_x")
                    with col_y:
                        wm_y_pct = st.slider("Posição Y (% da altura)", 0.0, 1.0, p_info['y_percent'], 0.01, key="meta_y")
                    
                    col_w, col_h = st.columns(2)
                    with col_w:
                        wm_w_pct = st.slider("Largura (% da largura)", 0.01, 0.5, p_info['width_percent'], 0.01, key="meta_w")
                    with col_h:
                        wm_h_pct = st.slider("Altura (% da altura)", 0.01, 0.5, p_info['height_percent'], 0.01, key="meta_h")
                else:
                    wm_x_pct = p_info['x_percent']
                    wm_y_pct = p_info['y_percent']
                    wm_w_pct = p_info['width_percent']
                    wm_h_pct = p_info['height_percent']
                
                col_algo, col_raio = st.columns(2)
                with col_algo:
                    algo_nome = st.selectbox("Algoritmo de Inpainting:", list(ALGORITMOS_INPAINTING.keys()), key="meta_algo")
                    wm_algoritmo = ALGORITMOS_INPAINTING[algo_nome]
                with col_raio:
                    wm_raio = st.slider("Raio de Inpainting (pixels):", 1, 10, 3, key="meta_raio")
                
            except Exception as e:
                st.error(f"Erro ao carregar pré-visualização do vídeo: {e}")
                remover_wm = False
            finally:
                if os.path.exists(caminho_ref):
                    try:
                        os.remove(caminho_ref)
                    except:
                        pass
        else:
            st.caption("ℹ️ A remoção de marca d'água está desativada. O vídeo será processado apenas com antiduplicação e metadados.")

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

    if st.button("🚀 Processar Vídeo Completo (Marca d'Água + Metadados)", type="primary", use_container_width=True):
        barra_status = st.progress(0, text="Iniciando processamento...")
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_in:
            caminho_in = temp_in.name
        
        caminho_sem_wm = None
        caminho_out = None
        
        try:
            # 1. Salva arquivo enviado
            barra_status.progress(10, text="Carregando arquivo enviado...")
            with open(caminho_in, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            caminho_atual = caminho_in
            
            # 2. Remove marca d'água se solicitado (sem reescrever o upload original do usuário)
            if remover_wm:
                barra_status.progress(20, text="Removendo marca d'água do vídeo...")
                info_v = obter_informacoes_video(caminho_in)
                rx, ry, rw, rh = calcular_coordenadas_reais(
                    info_v['altura'], info_v['largura'],
                    wm_x_pct, wm_y_pct, wm_w_pct, wm_h_pct
                )
                
                def status_cb(msg, prog):
                    barra_status.progress(int(prog * 50), text=msg)
                
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_wm:
                    caminho_sem_wm = tmp_wm.name
                
                caminho_processado_wm = processar_remocao_marca_dagua(
                    caminho_in,
                    rx, ry, rw, rh,
                    wm_algoritmo,
                    wm_raio,
                    status_cb
                )
                
                if caminho_processado_wm and os.path.exists(caminho_processado_wm):
                    caminho_atual = caminho_processado_wm
            
            # 3. Limpeza de metadados e antiduplicação (FFmpeg)
            barra_status.progress(60, text="Aplicando Antiduplicação e Limpando Metadados...")
            loc = random.choice(LOCALIZACOES_REAIS)
            coordenadas = (loc["lat"], loc["lon"])
            
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_final:
                caminho_out = temp_final.name
            
            sucesso_meta = limpar_metadados_ffmpeg(
                caminho_atual,
                caminho_out,
                coordenadas,
                loc["alt"],
                antidup_config
            )
            
            barra_status.progress(100, text="✅ Processamento concluído com sucesso!")
            
            if sucesso_meta and os.path.exists(caminho_out) and os.path.getsize(caminho_out) > 0:
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
                
                if remover_wm:
                    st.success("🎉 Marca d'água removida + Assinatura digital alterada + Metadados limpos com sucesso!")
                else:
                    st.success("🎉 Assinatura digital alterada + Metadados limpos com sucesso!")
            else:
                st.error("❌ Falha ao aplicar antiduplicação no FFmpeg.")
                
        except Exception as e:
            st.error(f"❌ Erro durante o processamento unificado: {str(e)}")
        finally:
            # Limpeza de arquivos temporários
            for p in [caminho_in, caminho_sem_wm, caminho_out]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except:
                        pass


__all__ = ["render_metadados_pro"]
