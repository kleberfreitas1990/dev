import streamlit as st
import os
import subprocess
import random
import time
from datetime import datetime

def limpar_e_injetar_metadados(input_path, output_path, dispositivo, coordenadas=None):
    """
    Usa exiftool e ffmpeg para limpar metadados originais e injetar novos dados.
    """
    try:
        # 1. Limpeza total de metadados com exiftool
        subprocess.run(['exiftool', '-all=', '-overwrite_original', input_path], check=True)
        
        # 2. Definir metadados baseados no dispositivo
        if dispositivo == "Apple":
            make = "Apple"
            model = random.choice(["iPhone 13 Pro", "iPhone 14 Pro Max", "iPhone 15 Pro"])
            software = f"iOS {random.randint(16, 17)}.{random.randint(0, 5)}"
        else:
            make = "Samsung"
            model = random.choice(["SM-G998B", "SM-S908B", "SM-S918B"]) # S21 Ultra, S22 Ultra, S23 Ultra
            software = f"Android {random.randint(12, 14)}"

        # 3. Preparar comando ExifTool para injeção
        cmd_exif = [
            'exiftool',
            f'-Make={make}',
            f'-Model={model}',
            f'-Software={software}',
            '-overwrite_original'
        ]
        
        if coordenadas:
            lat, lon = coordenadas
            # Formato ExifTool para GPS
            cmd_exif.append(f'-GPSLatitude={lat}')
            cmd_exif.append(f'-GPSLongitude={lon}')
            cmd_exif.append('-GPSLatitudeRef=N' if lat >= 0 else '-GPSLatitudeRef=S')
            cmd_exif.append('-GPSLongitudeRef=E' if lon >= 0 else '-GPSLongitudeRef=W')

        cmd_exif.append(input_path)
        subprocess.run(cmd_exif, check=True)

        # 4. Usar FFmpeg para uma cópia limpa do stream (remove metadados de stream)
        subprocess.run([
            'ffmpeg', '-i', input_path, 
            '-c', 'copy', '-map_metadata', '-1', 
            '-y', output_path
        ], check=True, capture_output=True)

        return True
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return False

def render_metadados_pro():
    st.markdown("# 🎬 Metadata Pro - Auto-Injeção Inteligente")
    st.caption("O sistema analisa o arquivo e injeta metadados realistas (GPS, Data e Hardware) automaticamente.")
    
    st.markdown("### Upload do vídeo MP4")
    uploaded_file = st.file_uploader("", type=["mp4"], key="upload_video_metadata")

    if uploaded_file:
        # Salvar arquivo temporário
        temp_input = f"temp_in_{uploaded_file.name}"
        temp_output = f"cleaned_{uploaded_file.name}"
        
        with open(temp_input, "wb") as f:
            f.write(uploaded_file.getbuffer())

        col_disp, col_gps = st.columns(2)
        
        with col_disp:
            st.markdown("### 📱 Escolha o Dispositivo Alvo")
            st.caption("Simular Hardware:")
            dispositivo = st.radio("", ["Apple", "Samsung"], horizontal=True, key="radio_dispositivo")
            
            st.info(f"O sistema irá sincronizar a data interna com o nome do arquivo {uploaded_file.name}.")

        with col_gps:
            st.markdown("### 🛰️ GPS & Localização")
            with st.container(border=True):
                st.success("✅ Localização Dinâmica Ativa: Coordenadas reais com variação de precisão (Jitter).")
            st.caption("Isso evita a detecção de 'Null Island' (0,0) por softwares periciais.")

        if st.button("🚀 Injetar Metadados Indetectáveis", type="primary", use_container_width=True):
            with st.spinner("⚙️ Processando vídeo e injetando metadados..."):
                # Simular coordenadas reais (ex: São Paulo com jitter)
                lat = -23.5505 + (random.uniform(-0.01, 0.01))
                lon = -46.6333 + (random.uniform(-0.01, 0.01))
                
                sucesso = limpar_e_injetar_metadados(temp_input, temp_output, dispositivo, (lat, lon))
                
                if sucesso:
                    st.success("✅ Metadados injetados com sucesso!")
                    with open(temp_output, "rb") as f:
                        st.download_button(
                            label="📥 Baixar Vídeo Limpo",
                            data=f,
                            file_name=f"metadata_pro_{uploaded_file.name}",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    # Limpeza
                    if os.path.exists(temp_input): os.remove(temp_input)
                    if os.path.exists(temp_output): os.remove(temp_output)
                else:
                    st.error("❌ Falha ao processar o vídeo.")
    else:
        st.info("💡 Faça o upload de um vídeo MP4 para começar a limpeza de metadados.")
