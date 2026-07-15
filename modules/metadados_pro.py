import streamlit as st
import os
import subprocess
import random
import time
from datetime import datetime, timedelta
from app import PERFIS_CAMERA, LOCALIZACOES_REAIS # Importar para acessar resoluções e altitudes

def gerar_nome_arquivo_real(dispositivo, extensao=".mp4"):
    """Gera um nome de arquivo idêntico ao de uma câmera real"""
    num = random.randint(1000, 9999)
    if dispositivo == "Apple":
        return f"IMG_{num}{extensao}"
    else:
        return f"VID_{datetime.now().strftime('%Y%m%d')}_{num}{extensao}"

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

def render_metadados_pro():
    st.markdown("# 🎬 Metadata Pro - Camuflagem Profunda")
    st.caption("Remoção total de rastros digitais (Lavf, FFmpeg) e injeção de hardware nativo.")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("Upload do vídeo", type=["mp4", "mov"], key="up_meta_v64")

    if uploaded_file:
        col_cfg, col_res = st.columns(2)
        
        with col_cfg:
            dispositivo = st.radio("Simular Dispositivo:", ["Apple", "Samsung"], horizontal=True)
            usar_gps = st.checkbox("Injetar GPS Realista", value=True)
            
        with col_res:
            nome_sugerido = gerar_nome_arquivo_real(dispositivo)
            st.info(f"📁 Nome Original: `{uploaded_file.name}`")
            st.success(f"🛡️ Novo Nome: `{nome_sugerido}`")

        if st.button("🚀 Executar Camuflagem Profunda", type="primary", use_container_width=True):
            progress = st.progress(0, text="Iniciando camuflagem...")
            
            temp_in = f"raw_{random.randint(100,999)}_{uploaded_file.name}"
            temp_out = nome_sugerido # Usa o nome real de câmera
            
            try:
                with open(temp_in, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                progress.progress(40, text="Removendo rastro 'Lavf' e limpando VendorID...")
                
                # Obter altitude da cidade selecionada
                altitude = None
                if usar_gps:
                    # Precisa importar LOCALIZACOES_REAIS do app.py
                    # from app import LOCALIZACOES_REAIS # Já importado globalmente


                    cidade_escolhida = st.session_state.get("select_cidade_gps")
                    if cidade_escolhida:
                        loc_info = next((l for l in LOCALIZACOES_REAIS if l["cidade"] == cidade_escolhida), None)
                        if loc_info and "alt" in loc_info:
                            altitude = loc_info["alt"]
                    coordenadas = (-23.5505 + random.uniform(-0.01, 0.01), -46.6333 + random.uniform(-0.01, 0.01))
                else:
                    coordenadas = None

                # Obter resolução alvo do perfil selecionado
                resolucao_alvo = PERFIS_CAMERA[st.session_state.get("select_perfil_camera")]["resolucao"] if st.session_state.get("select_perfil_camera") else None

                if limpar_e_injetar_metadados_ffmpeg(temp_in, temp_out, dispositivo, coordenadas, altitude, resolucao_alvo):
                    progress.progress(100, text="✅ Camuflagem concluída! Rastro Lavf removido.")
                    st.balloons()
                    
                    with open(temp_out, "rb") as f:
                        st.download_button(
                            label=f"📥 Baixar {nome_sugerido}",
                            data=f,
                            file_name=nome_sugerido,
                            mime="video/mp4",
                            use_container_width=True
                        )
                else:
                    st.error("❌ Falha na camuflagem.")
            finally:
                if os.path.exists(temp_in): os.remove(temp_in)
                # O temp_out deve ser limpo depois ou gerenciado pelo Streamlit
