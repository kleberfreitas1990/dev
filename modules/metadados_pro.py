import streamlit as st
import os
import subprocess
import random
import time
from datetime import datetime, timedelta

def limpar_e_injetar_metadados_ffmpeg(input_path, output_path, dispositivo, coordenadas=None):
    """
    Usa apenas FFmpeg para limpar metadados originais e injetar novos dados.
    Remove a dependência do exiftool que estava causando erro.
    """
    # Verificar se ffmpeg está disponível
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
    except FileNotFoundError:
        st.error("❌ FFmpeg não encontrado no sistema. Por favor, certifique-se de que o arquivo 'packages.txt' contém 'ffmpeg' e que o app foi reiniciado no Streamlit Cloud.")
        return False

    try:
        # 1. Definir metadados baseados no dispositivo
        if dispositivo == "Apple":
            make = "Apple"
            model = random.choice(["iPhone 13 Pro", "iPhone 14 Pro Max", "iPhone 15 Pro"])
            software = f"iOS {random.randint(16, 17)}.{random.randint(0, 5)}"
            encoder = "com.apple.avfoundation.avcapturesession"
        else:
            make = "Samsung"
            model = random.choice(["SM-G998B", "SM-S908B", "SM-S918B"]) # S21 Ultra, S22 Ultra, S23 Ultra
            software = f"Android {random.randint(12, 14)}"
            encoder = "OMX.SEC.AVC.Encoder"

        # Gera uma data retroativa realista
        data_retroativa = datetime.now() - timedelta(days=random.randint(1, 30))
        data_str = data_retroativa.strftime("%Y-%m-%dT%H:%M:%S")
        data_creation = data_retroativa.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

        # 2. Construir comando FFmpeg para limpeza e injeção
        # -map_metadata -1 remove todos os metadados globais
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy',                # Copia streams sem re-encodar (rápido)
            '-map_metadata', '-1',       # Remove todos os metadados originais
            '-metadata', f'make={make}',
            '-metadata', f'model={model}',
            '-metadata', f'software={software}',
            '-metadata', f'encoder={encoder}',
            '-metadata', f'creation_time={data_creation}',
            '-metadata', f'date={data_str}',
            # Limpa tags específicas do TikTok/Redes Sociais
            '-metadata', 'comment=',
            '-metadata', 'VidMd5=',
            '-metadata', 'location=',
        ]

        if coordenadas:
            lat, lon = coordenadas
            # Formato ISO 6709 para GPS
            lat_str = f"+{lat:.4f}" if lat >= 0 else f"{lat:.4f}"
            lon_str = f"+{lon:.4f}" if lon >= 0 else f"{lon:.4f}"
            iso6709 = f"{lat_str}{lon_str}/"
            cmd.extend([
                '-metadata', f'location={iso6709}',
                '-metadata', f'com.apple.quicktime.location.ISO6709={iso6709}'
            ])

        cmd.extend(['-y', output_path])

        # Executa o comando
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"Erro FFmpeg: {result.stderr[-200:]}")
            return False

        return True
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return False

def render_metadados_pro():
    st.markdown("# 🎬 Metadata Pro - Auto-Injeção Inteligente")
    st.caption("Limpeza cirúrgica de metadados e injeção de hardware realista via FFmpeg.")
    
    with st.container(border=True):
        st.markdown("### 📁 Upload do vídeo MP4")
        uploaded_file = st.file_uploader("", type=["mp4", "mov", "mkv"], key="upload_video_metadata")

    if uploaded_file:
        # Detalhes do arquivo
        tamanho_mb = round(uploaded_file.size / (1024 * 1024), 2)
        
        col_disp, col_gps = st.columns(2)
        
        with col_disp:
            st.markdown("### 📱 Dispositivo Alvo")
            dispositivo = st.radio("Simular Hardware:", ["Apple", "Samsung"], horizontal=True, key="radio_dispositivo")
            st.info(f"📄 Arquivo: `{uploaded_file.name}` ({tamanho_mb} MB)")

        with col_gps:
            st.markdown("### 🛰️ GPS & Localização")
            usar_gps = st.checkbox("Injetar Coordenadas Reais", value=True)
            if usar_gps:
                st.success("✅ Jitter Dinâmico Ativo (±0.005°)")
            else:
                st.warning("⚠️ Sem dados de geolocalização")

        st.markdown("---")

        if st.button("🚀 Iniciar Higienização Profunda", type="primary", use_container_width=True):
            # 1. Feedback Visual "Load Legal"
            progress_bar = st.progress(0, text="Iniciando limpeza cirúrgica...")
            
            # Salvar arquivo temporário
            temp_input = f"temp_in_{random.randint(1000, 9999)}_{uploaded_file.name}"
            temp_output = f"cleaned_{random.randint(1000, 9999)}_{uploaded_file.name}"
            
            try:
                with open(temp_input, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                progress_bar.progress(30, text="Removendo tags de rastreamento (TikTok, VidMd5)...")
                time.sleep(0.5)
                
                progress_bar.progress(60, text=f"Injetando perfil de hardware {dispositivo}...")
                
                # Simular coordenadas reais se solicitado
                coordenadas = None
                if usar_gps:
                    lat = -23.5505 + (random.uniform(-0.01, 0.01))
                    lon = -46.6333 + (random.uniform(-0.01, 0.01))
                    coordenadas = (lat, lon)
                
                # Processamento real
                sucesso = limpar_e_injetar_metadados_ffmpeg(temp_input, temp_output, dispositivo, coordenadas)
                
                if sucesso:
                    progress_bar.progress(100, text="✅ Higienização concluída com sucesso!")
                    time.sleep(0.5)
                    
                    st.balloons()
                    st.success("✨ Vídeo higienizado e pronto para download!")
                    
                    with open(temp_output, "rb") as f:
                        st.download_button(
                            label="📥 Baixar Vídeo Limpo",
                            data=f,
                            file_name=f"higienizado_{uploaded_file.name}",
                            mime="video/mp4",
                            use_container_width=True
                        )
                else:
                    st.error("❌ Falha no processamento do vídeo.")
            
            finally:
                # Limpeza de arquivos temporários
                if os.path.exists(temp_input): os.remove(temp_input)
                if os.path.exists(temp_output): 
                    # Não removemos o output imediatamente para permitir o download no Streamlit
                    # O Streamlit mantém o botão de download ativo enquanto a página não for recarregada
                    pass
    else:
        st.info("💡 Faça o upload de um vídeo para remover rastros e injetar novos metadados.")
