"""
Higienizador de Mídia Pro
=========================
Interface Streamlit para limpeza e camuflagem de metadados de vídeos.
Utiliza FFmpeg para remoção cirúrgica de tags, GPS e datas corrompidas,
com injeção de perfis de câmera realistas.

Autor: Engenheiro de Software Sênior
Versão: 1.0.0
"""

import streamlit as st
import subprocess
import tempfile
import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Higienizador de Mídia Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PERFIS DE CÂMERA DISPONÍVEIS
# ============================================================
PERFIS_CAMERA = {
    "Apple iPhone 15 Pro Max": {
        "make": "Apple",
        "model": "iPhone 15 Pro Max",
        "software": "17.4.1",
        "encoder": "com.apple.avfoundation.avcapturesession",
        "prefix_nome": "IMG",
        "extensao_padrao": "mp4",
        "fps": "30",
        "resolucao": "3840x2160",
        "icone": "🍎",
    },
    "Apple iPhone 14 Pro": {
        "make": "Apple",
        "model": "iPhone 14 Pro",
        "software": "16.7.2",
        "encoder": "com.apple.avfoundation.avcapturesession",
        "prefix_nome": "IMG",
        "extensao_padrao": "mp4",
        "fps": "30",
        "resolucao": "3840x2160",
        "icone": "🍎",
    },
    "Apple iPhone 13": {
        "make": "Apple",
        "model": "iPhone 13",
        "software": "16.5.0",
        "encoder": "com.apple.avfoundation.avcapturesession",
        "prefix_nome": "IMG",
        "extensao_padrao": "mp4",
        "fps": "30",
        "resolucao": "1920x1080",
        "icone": "🍎",
    },
    "Samsung Galaxy S24 Ultra": {
        "make": "Samsung",
        "model": "SM-S928B",
        "software": "Android 14",
        "encoder": "OMX.SEC.AVC.Encoder",
        "prefix_nome": "VID",
        "extensao_padrao": "mp4",
        "fps": "30",
        "resolucao": "3840x2160",
        "icone": "📱",
    },
    "Samsung Galaxy S23": {
        "make": "Samsung",
        "model": "SM-S911B",
        "software": "Android 13",
        "encoder": "OMX.SEC.AVC.Encoder",
        "prefix_nome": "VID",
        "extensao_padrao": "mp4",
        "fps": "30",
        "resolucao": "1920x1080",
        "icone": "📱",
    },
    "Sony A7 IV": {
        "make": "Sony",
        "model": "ILCE-7M4",
        "software": "Ver.1.10",
        "encoder": "XAVC S",
        "prefix_nome": "C0",
        "extensao_padrao": "mp4",
        "fps": "25",
        "resolucao": "3840x2160",
        "icone": "📷",
    },
    "Canon EOS R6": {
        "make": "Canon",
        "model": "Canon EOS R6",
        "software": "Firmware 1.8.1",
        "encoder": "Canon XF-AVC",
        "prefix_nome": "MVI",
        "extensao_padrao": "mp4",
        "fps": "25",
        "resolucao": "1920x1080",
        "icone": "📷",
    },
    "GoPro Hero 12": {
        "make": "GoPro",
        "model": "HERO12 Black",
        "software": "HD2.01.01.99.74",
        "encoder": "GoPro AVC encoder",
        "prefix_nome": "GH01",
        "extensao_padrao": "mp4",
        "fps": "60",
        "resolucao": "3840x2160",
        "icone": "🎥",
    },
    "DJI Osmo Pocket 3": {
        "make": "DJI",
        "model": "Osmo Pocket 3",
        "software": "v01.00.0200",
        "encoder": "DJI H.264",
        "prefix_nome": "DJI",
        "extensao_padrao": "mp4",
        "fps": "30",
        "resolucao": "3840x2160",
        "icone": "🚁",
    },
}

# ============================================================
# COORDENADAS REAIS PARA INJEÇÃO DE GPS
# ============================================================
LOCALIZACOES_REAIS = [
    {"cidade": "São Paulo, SP", "lat": -23.5505, "lon": -46.6333},
    {"cidade": "Rio de Janeiro, RJ", "lat": -22.9068, "lon": -43.1729},
    {"cidade": "Belo Horizonte, MG", "lat": -19.9167, "lon": -43.9345},
    {"cidade": "Curitiba, PR", "lat": -25.4284, "lon": -49.2733},
    {"cidade": "Porto Alegre, RS", "lat": -30.0346, "lon": -51.2177},
    {"cidade": "Salvador, BA", "lat": -12.9714, "lon": -38.5014},
    {"cidade": "Fortaleza, CE", "lat": -3.7172, "lon": -38.5433},
    {"cidade": "Recife, PE", "lat": -8.0476, "lon": -34.8770},
    {"cidade": "Manaus, AM", "lat": -3.1190, "lon": -60.0217},
    {"cidade": "Brasília, DF", "lat": -15.7801, "lon": -47.9292},
]

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def verificar_ffmpeg() -> bool:
    """Verifica se o FFmpeg está instalado e disponível"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def gerar_data_retroativa(dias_atras_min: int = 7, dias_atras_max: int = 90) -> datetime:
    """Gera uma data retroativa realista para injeção nos metadados"""
    dias = random.randint(dias_atras_min, dias_atras_max)
    hora = random.randint(8, 20)
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    data_base = datetime.now() - timedelta(days=dias)
    return data_base.replace(hour=hora, minute=minuto, second=segundo, microsecond=0)

def gerar_nome_arquivo_camera(perfil: dict, numero: int = None) -> str:
    """Gera um nome de arquivo no padrão da câmera escolhida"""
    prefix = perfil.get("prefix_nome", "VID")
    ext = perfil.get("extensao_padrao", "mp4")
    if numero is None:
        numero = random.randint(1000, 9999)
    return f"{prefix}_{numero:04d}.{ext}"

def gerar_coordenadas_com_jitter(lat: float, lon: float, jitter: float = 0.005) -> tuple:
    """Adiciona variação realista (jitter) às coordenadas GPS"""
    lat_jitter = lat + random.uniform(-jitter, jitter)
    lon_jitter = lon + random.uniform(-jitter, jitter)
    return round(lat_jitter, 6), round(lon_jitter, 6)

def extrair_data_do_nome(nome_arquivo: str):
    """
    Tenta extrair uma data do nome do arquivo (ex: 20260703_141200_UTC_0.mp4)
    Retorna None se não encontrar padrão de data.
    """
    # Padrão: YYYYMMDD_HHMMSS
    padrao1 = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', nome_arquivo)
    if padrao1:
        try:
            return datetime(
                int(padrao1.group(1)), int(padrao1.group(2)), int(padrao1.group(3)),
                int(padrao1.group(4)), int(padrao1.group(5)), int(padrao1.group(6))
            )
        except ValueError:
            pass

    # Padrão: YYYY-MM-DD
    padrao2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', nome_arquivo)
    if padrao2:
        try:
            return datetime(int(padrao2.group(1)), int(padrao2.group(2)), int(padrao2.group(3)))
        except ValueError:
            pass

    return None

# ============================================================
# FUNÇÃO PRINCIPAL DE LIMPEZA COM FFMPEG
# ============================================================
def limpar_metadados_ffmpeg(
    input_path: str,
    output_path: str,
    perfil: dict,
    data_injecao: datetime,
    coordenadas: tuple = None,
    deletar_original: bool = False
) -> dict:
    """
    Executa a limpeza cirúrgica de metadados usando FFmpeg.

    Operações realizadas:
    1. Remove todas as tags de metadados (incluindo TikTok: Comment, VidMd5)
    2. Remove geolocalização (GPS)
    3. Corrige datas corrompidas para datas retroativas válidas
    4. Injeta metadados do perfil de câmera escolhido
    5. Renomeia o arquivo para o padrão da câmera

    Args:
        input_path: Caminho do arquivo de entrada
        output_path: Caminho do arquivo de saída
        perfil: Dicionário com dados do perfil de câmera
        data_injecao: Data a ser injetada nos metadados
        coordenadas: Tupla (lat, lon) para GPS (opcional)
        deletar_original: Se True, remove o arquivo original após processamento

    Returns:
        Dicionário com resultado do processamento
    """
    resultado = {
        "sucesso": False,
        "mensagem": "",
        "tempo_processamento": 0.0,
        "tamanho_entrada_mb": 0.0,
        "tamanho_saida_mb": 0.0,
    }

    inicio = time.time()

    try:
        # Tamanho do arquivo de entrada
        resultado["tamanho_entrada_mb"] = round(os.path.getsize(input_path) / (1024 * 1024), 2)

        # Formata a data para o padrão FFmpeg/ISO 8601
        data_str = data_injecao.strftime("%Y-%m-%dT%H:%M:%S")
        data_creation = data_injecao.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

        # ============================================================
        # CONSTRUÇÃO DO COMANDO FFMPEG
        # ============================================================
        # Estratégia: copia os streams sem re-encodar (-c copy),
        # remove TODOS os metadados globais (-map_metadata -1),
        # e injeta apenas os metadados controlados.
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c", "copy",                    # Copia streams sem re-encodar (rápido)
            "-map_metadata", "-1",           # Remove TODOS os metadados globais
            "-map_chapters", "-1",           # Remove capítulos
            # Injeta metadados controlados do perfil de câmera
            "-metadata", f"make={perfil['make']}",
            "-metadata", f"model={perfil['model']}",
            "-metadata", f"software={perfil['software']}",
            "-metadata", f"encoder={perfil['encoder']}",
            "-metadata", f"creation_time={data_creation}",
            "-metadata", f"date={data_str}",
            "-metadata", f"com.apple.quicktime.creationdate={data_str}",
            # Remove tags específicas do TikTok
            "-metadata", "comment=",
            "-metadata", "VidMd5=",
            "-metadata", "com.bytedance.tiktok.video_id=",
            "-metadata", "com.bytedance.tiktok.author=",
            # Remove GPS via metadados vazios
            "-metadata", "location=",
            "-metadata", "location-eng=",
            "-metadata", "com.apple.quicktime.location.ISO6709=",
        ]

        # Injeta GPS se fornecido
        if coordenadas:
            lat, lon = coordenadas
            # Formato ISO 6709 para GPS (ex: +48.8577+002.2950/)
            lat_str = f"+{lat:.4f}" if lat >= 0 else f"{lat:.4f}"
            lon_str = f"+{lon:.4f}" if lon >= 0 else f"{lon:.4f}"
            iso6709 = f"{lat_str}{lon_str}/"
            cmd.extend([
                "-metadata", f"location={iso6709}",
                "-metadata", f"location-eng={iso6709}",
                "-metadata", f"com.apple.quicktime.location.ISO6709={iso6709}",
            ])

        # Arquivo de saída com sobrescrita forçada
        cmd.extend(["-y", output_path])

        # ============================================================
        # EXECUÇÃO DO FFMPEG
        # ============================================================
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # Timeout de 5 minutos
        )

        if process.returncode != 0:
            # Tenta identificar o erro específico
            stderr = process.stderr or ""
            if "Invalid data found" in stderr:
                resultado["mensagem"] = "Arquivo corrompido ou formato não suportado pelo FFmpeg."
            elif "No such file" in stderr:
                resultado["mensagem"] = "Arquivo de entrada não encontrado."
            elif "Permission denied" in stderr:
                resultado["mensagem"] = "Sem permissão para acessar o arquivo."
            else:
                resultado["mensagem"] = f"FFmpeg retornou erro (código {process.returncode}): {stderr[-200:]}"
            return resultado

        # Verifica se o arquivo de saída foi criado
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            resultado["mensagem"] = "FFmpeg não gerou o arquivo de saída corretamente."
            return resultado

        # Tamanho do arquivo de saída
        resultado["tamanho_saida_mb"] = round(os.path.getsize(output_path) / (1024 * 1024), 2)
        resultado["tempo_processamento"] = round(time.time() - inicio, 2)
        resultado["sucesso"] = True
        resultado["mensagem"] = "Metadados limpos e injetados com sucesso."

        # Deleta o original se solicitado
        if deletar_original and os.path.exists(input_path):
            os.remove(input_path)

        return resultado

    except subprocess.TimeoutExpired:
        resultado["mensagem"] = "Timeout: o processamento demorou mais de 5 minutos."
        return resultado
    except FileNotFoundError:
        resultado["mensagem"] = "FFmpeg não encontrado. Instale com: sudo apt-get install ffmpeg"
        return resultado
    except Exception as e:
        resultado["mensagem"] = f"Erro inesperado: {str(e)}"
        return resultado
    finally:
        resultado["tempo_processamento"] = round(time.time() - inicio, 2)

# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    """Renderiza a barra lateral com perfis de câmera e opções"""
    with st.sidebar:
        st.markdown("## 🎬 Higienizador de Mídia Pro")
        st.markdown("---")

        st.markdown("### 📷 Perfil de Câmera")
        st.caption("Escolha o dispositivo para simular nos metadados")

        perfil_selecionado = st.selectbox(
            "Câmera / Dispositivo",
            options=list(PERFIS_CAMERA.keys()),
            format_func=lambda x: f"{PERFIS_CAMERA[x]['icone']} {x}",
            key="select_perfil_camera"
        )

        perfil = PERFIS_CAMERA[perfil_selecionado]

        # Exibe detalhes do perfil selecionado
        with st.expander("ℹ️ Detalhes do Perfil", expanded=True):
            st.markdown(f"""
            | Campo | Valor |
            |-------|-------|
            | **Fabricante** | {perfil['make']} |
            | **Modelo** | {perfil['model']} |
            | **Software** | {perfil['software']} |
            | **Resolução** | {perfil['resolucao']} |
            | **FPS** | {perfil['fps']} |
            | **Prefixo** | {perfil['prefix_nome']} |
            """)

        st.markdown("---")

        st.markdown("### ⚙️ Opções de Processamento")

        deletar_original = st.toggle(
            "🗑️ Deletar arquivo original após limpeza",
            value=False,
            key="toggle_deletar_original",
            help="Se ativado, o arquivo original será removido após o processamento bem-sucedido."
        )

        st.markdown("---")

        st.markdown("### 🛰️ GPS & Localização")

        usar_gps = st.toggle(
            "📍 Injetar GPS realista",
            value=True,
            key="toggle_usar_gps",
            help="Injeta coordenadas reais de cidades brasileiras com variação (jitter) para evitar detecção forense."
        )

        if usar_gps:
            cidade_escolhida = st.selectbox(
                "Cidade base",
                options=[loc["cidade"] for loc in LOCALIZACOES_REAIS],
                key="select_cidade_gps"
            )
            loc_base = next(l for l in LOCALIZACOES_REAIS if l["cidade"] == cidade_escolhida)
            st.caption(f"📌 Base: {loc_base['lat']:.4f}, {loc_base['lon']:.4f}")
            st.success("✅ Jitter automático ativo (±0.005°)")

        st.markdown("---")

        st.markdown("### 📅 Data de Injeção")

        modo_data = st.radio(
            "Modo",
            ["🔄 Automático (retroativa aleatória)", "📅 Sincronizar com nome do arquivo", "✏️ Definir manualmente"],
            key="radio_modo_data"
        )

        if modo_data == "✏️ Definir manualmente":
            data_manual = st.date_input("Data", key="date_manual")
            hora_manual = st.time_input("Hora", key="time_manual")
            st.session_state["data_manual_dt"] = datetime.combine(data_manual, hora_manual)

        st.markdown("---")
        st.caption("🔒 Todos os arquivos são processados localmente. Nenhum dado é enviado para servidores externos.")

    return perfil_selecionado, perfil, deletar_original, usar_gps, modo_data

# ============================================================
# ÁREA PRINCIPAL
# ============================================================
def render_area_principal(perfil_nome: str, perfil: dict, deletar_original: bool, usar_gps: bool, modo_data: str):
    """Renderiza a área principal com upload e processamento"""

    st.markdown("# 🎬 Higienizador de Mídia Pro")
    st.caption("Limpeza cirúrgica e camuflagem de metadados de vídeos. Compatível com MP4, MKV e MOV.")

    # Verifica FFmpeg
    ffmpeg_ok = verificar_ffmpeg()
    if not ffmpeg_ok:
        st.error(
            "❌ **FFmpeg não encontrado!** "
            "Instale com: `sudo apt-get install ffmpeg` ou `brew install ffmpeg`"
        )
        st.stop()

    st.markdown("---")

    # ============================================================
    # UPLOAD DE ARQUIVOS
    # ============================================================
    st.markdown("### 📁 Upload de Vídeos")
    st.caption("Selecione um ou mais arquivos para processamento em lote")

    arquivos = st.file_uploader(
        "Arraste ou selecione os arquivos",
        type=["mp4", "mkv", "mov"],
        accept_multiple_files=True,
        key="uploader_videos",
        help="Formatos suportados: MP4, MKV, MOV. Múltiplos arquivos podem ser selecionados."
    )

    if not arquivos:
        st.info(
            "💡 **Como usar:**\n"
            "1. Selecione o perfil de câmera na barra lateral\n"
            "2. Faça o upload dos vídeos acima\n"
            "3. Revise os detalhes e clique em **Processar**\n"
            "4. Baixe os arquivos limpos individualmente"
        )
        return

    # ============================================================
    # DETALHES DOS ARQUIVOS CARREGADOS
    # ============================================================
    st.markdown(f"### 📋 {len(arquivos)} arquivo(s) carregado(s)")

    import pandas as pd
    dados_arquivos = []
    for arq in arquivos:
        tamanho_mb = round(arq.size / (1024 * 1024), 2)
        dados_arquivos.append({
            "Nome Original": arq.name,
            "Tamanho (MB)": tamanho_mb,
            "Formato": arq.name.split(".")[-1].upper(),
            "Nome Limpo (Câmera)": gerar_nome_arquivo_camera(perfil, random.randint(1000, 9999)),
        })

    df_arquivos = pd.DataFrame(dados_arquivos)
    st.dataframe(df_arquivos, use_container_width=True, hide_index=True)

    # ============================================================
    # RESUMO DA OPERAÇÃO
    # ============================================================
    col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
    with col_resumo1:
        st.info(f"📷 **Câmera:** {perfil['icone']} {perfil_nome}")
    with col_resumo2:
        gps_status = "✅ GPS Ativo" if usar_gps else "❌ GPS Desativado"
        st.info(f"🛰️ **GPS:** {gps_status}")
    with col_resumo3:
        del_status = "⚠️ Original será deletado" if deletar_original else "✅ Original preservado"
        st.info(f"🗑️ **Original:** {del_status}")

    st.markdown("---")

    # ============================================================
    # BOTÃO DE PROCESSAMENTO
    # ============================================================
    if st.button(
        f"🚀 Processar {len(arquivos)} arquivo(s) — Limpar e Camuflar Metadados",
        type="primary",
        use_container_width=True,
        key="btn_processar_videos"
    ):
        st.markdown("### ⚙️ Processamento em Andamento")

        resultados_processamento = []
        barra_geral = st.progress(0, text="Iniciando processamento...")

        for idx, arquivo in enumerate(arquivos):
            progresso_atual = idx / len(arquivos)
            barra_geral.progress(progresso_atual, text=f"Processando {idx+1}/{len(arquivos)}: {arquivo.name}")

            with st.expander(f"🎬 {arquivo.name}", expanded=True):
                col_info, col_status = st.columns([3, 1])

                with col_info:
                    st.caption(f"📦 Tamanho: {round(arquivo.size / (1024*1024), 2)} MB")

                barra_arquivo = st.progress(0, text="Preparando arquivo...")

                try:
                    # ============================================================
                    # SALVA ARQUIVO TEMPORÁRIO NO DISCO
                    # ============================================================
                    barra_arquivo.progress(10, text="Salvando arquivo temporário...")

                    extensao = Path(arquivo.name).suffix.lower()
                    with tempfile.NamedTemporaryFile(
                        suffix=extensao,
                        delete=False,
                        prefix="higienizador_in_"
                    ) as tmp_in:
                        tmp_in.write(arquivo.getbuffer())
                        caminho_entrada = tmp_in.name

                    # ============================================================
                    # DEFINE DATA DE INJEÇÃO
                    # ============================================================
                    barra_arquivo.progress(20, text="Calculando data de injeção...")

                    if "Sincronizar" in modo_data:
                        data_inj = extrair_data_do_nome(arquivo.name)
                        if data_inj is None:
                            data_inj = gerar_data_retroativa()
                    elif "manualmente" in modo_data:
                        data_inj = st.session_state.get("data_manual_dt", gerar_data_retroativa())
                    else:
                        data_inj = gerar_data_retroativa()

                    # ============================================================
                    # DEFINE COORDENADAS GPS
                    # ============================================================
                    barra_arquivo.progress(30, text="Configurando GPS...")

                    coordenadas = None
                    if usar_gps:
                        cidade_sel = st.session_state.get("select_cidade_gps", "São Paulo, SP")
                        loc = next(
                            (l for l in LOCALIZACOES_REAIS if l["cidade"] == cidade_sel),
                            LOCALIZACOES_REAIS[0]
                        )
                        coordenadas = gerar_coordenadas_com_jitter(loc["lat"], loc["lon"])

                    # ============================================================
                    # DEFINE NOME DO ARQUIVO DE SAÍDA
                    # ============================================================
                    barra_arquivo.progress(40, text="Gerando nome do arquivo limpo...")

                    numero_seq = random.randint(1000, 9999)
                    nome_saida = gerar_nome_arquivo_camera(perfil, numero_seq)

                    with tempfile.NamedTemporaryFile(
                        suffix=Path(nome_saida).suffix,
                        delete=False,
                        prefix="higienizador_out_"
                    ) as tmp_out:
                        caminho_saida = tmp_out.name

                    # ============================================================
                    # EXECUTA LIMPEZA COM FFMPEG
                    # ============================================================
                    barra_arquivo.progress(50, text="Executando FFmpeg — limpando metadados...")

                    resultado = limpar_metadados_ffmpeg(
                        input_path=caminho_entrada,
                        output_path=caminho_saida,
                        perfil=perfil,
                        data_injecao=data_inj,
                        coordenadas=coordenadas,
                        deletar_original=False  # Gerenciamos a deleção aqui
                    )

                    barra_arquivo.progress(90, text="Finalizando...")

                    if resultado["sucesso"]:
                        # ============================================================
                        # SUCESSO: EXIBE DETALHES E BOTÃO DE DOWNLOAD
                        # ============================================================
                        barra_arquivo.progress(100, text="✅ Concluído!")

                        with col_status:
                            st.success("✅ OK")

                        col_det1, col_det2, col_det3, col_det4 = st.columns(4)
                        with col_det1:
                            st.metric("📥 Entrada", f"{resultado['tamanho_entrada_mb']} MB")
                        with col_det2:
                            st.metric("📤 Saída", f"{resultado['tamanho_saida_mb']} MB")
                        with col_det3:
                            st.metric("⏱️ Tempo", f"{resultado['tempo_processamento']}s")
                        with col_det4:
                            st.metric("📅 Data Injetada", data_inj.strftime("%d/%m/%Y"))

                        # Informações do perfil injetado
                        st.markdown(f"""
                        **Metadados injetados:**
                        - 📷 Câmera: `{perfil['make']} {perfil['model']}`
                        - 💾 Software: `{perfil['software']}`
                        - 📅 Data: `{data_inj.strftime('%Y-%m-%d %H:%M:%S')}`
                        - 🛰️ GPS: `{f"{coordenadas[0]:.4f}, {coordenadas[1]:.4f}" if coordenadas else "Não injetado"}`
                        - 📁 Nome: `{nome_saida}`
                        """)

                        # Lê o arquivo limpo para download
                        with open(caminho_saida, "rb") as f_out:
                            dados_saida = f_out.read()

                        st.download_button(
                            label=f"📥 Baixar `{nome_saida}`",
                            data=dados_saida,
                            file_name=nome_saida,
                            mime="video/mp4",
                            use_container_width=True,
                            key=f"download_{idx}_{arquivo.name}"
                        )

                        resultados_processamento.append({
                            "arquivo": arquivo.name,
                            "nome_saida": nome_saida,
                            "sucesso": True,
                            "tempo": resultado["tempo_processamento"]
                        })

                        # Deleta original se solicitado
                        if deletar_original:
                            st.warning(f"🗑️ Arquivo original `{arquivo.name}` marcado para deleção.")

                    else:
                        # ============================================================
                        # FALHA: EXIBE MENSAGEM DE ERRO
                        # ============================================================
                        barra_arquivo.progress(100, text="❌ Falha no processamento")

                        with col_status:
                            st.error("❌ Erro")

                        st.error(f"❌ **Erro ao processar `{arquivo.name}`:** {resultado['mensagem']}")
                        resultados_processamento.append({
                            "arquivo": arquivo.name,
                            "sucesso": False,
                            "erro": resultado["mensagem"]
                        })

                except Exception as e:
                    barra_arquivo.progress(100, text="❌ Erro inesperado")
                    with col_status:
                        st.error("❌ Erro")
                    st.error(f"❌ **Exceção ao processar `{arquivo.name}`:** {str(e)}")
                    resultados_processamento.append({
                        "arquivo": arquivo.name,
                        "sucesso": False,
                        "erro": str(e)
                    })

                finally:
                    # Limpeza dos arquivos temporários
                    for caminho_tmp in [caminho_entrada, caminho_saida]:
                        try:
                            if os.path.exists(caminho_tmp):
                                os.remove(caminho_tmp)
                        except Exception:
                            pass

        # ============================================================
        # RESUMO FINAL
        # ============================================================
        barra_geral.progress(1.0, text="✅ Processamento concluído!")

        st.markdown("---")
        st.markdown("### 📊 Resumo do Processamento")

        total = len(resultados_processamento)
        sucessos = sum(1 for r in resultados_processamento if r["sucesso"])
        falhas = total - sucessos

        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("📦 Total processado", total)
        with col_r2:
            st.metric("✅ Sucesso", sucessos, delta=f"+{sucessos}")
        with col_r3:
            st.metric("❌ Falhas", falhas, delta=f"-{falhas}" if falhas > 0 else "0")

        if sucessos == total:
            st.success(f"🎉 Todos os {total} arquivo(s) foram processados com sucesso!")
        elif sucessos > 0:
            st.warning(f"⚠️ {sucessos} de {total} arquivo(s) processados. {falhas} falha(s).")
        else:
            st.error(f"❌ Nenhum arquivo foi processado com sucesso.")

# ============================================================
# PONTO DE ENTRADA PRINCIPAL
# ============================================================
def main():
    """Função principal da aplicação"""

    # Renderiza sidebar e obtém configurações
    perfil_nome, perfil, deletar_original, usar_gps, modo_data = render_sidebar()

    # Renderiza área principal
    render_area_principal(perfil_nome, perfil, deletar_original, usar_gps, modo_data)

    # Rodapé
    st.markdown("---")
    st.caption(
        "🔒 **Higienizador de Mídia Pro** — Processamento 100% local. "
        "Nenhum arquivo é enviado para servidores externos. "
        f"FFmpeg {'✅ disponível' if verificar_ffmpeg() else '❌ não encontrado'}."
    )

if __name__ == "__main__":
    main()
