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

RESOLUCOES_SAIDA = {
    "Manter proporções do original": None,
    "Vertical Full HD (1080 × 1920)": "1080x1920",
    "Horizontal Full HD (1920 × 1080)": "1920x1080",
    "Vertical HD (720 × 1280)": "720x1280",
    "Horizontal HD (1280 × 720)": "1280x720",
}


REDES_SUPORTADAS = (
    "tiktok.com",
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "twitter.com",
    "x.com",
)


def gerar_nome_arquivo_limpo(extensao: str = ".mp4") -> str:
    """Gera um nome que simula o padrão de uma câmara real (Apple, Android, Sony)."""
    agora = datetime.now()
    padroes = [
        # Padrão Apple (iPhone)
        lambda: f"IMG_{random.randint(1000, 9999)}.MP4",
        # Padrão Android / Samsung
        lambda: f"VID_{agora.strftime('%Y%m%d_%H%M%S')}.mp4",
        # Padrão Sony / Nikon
        lambda: f"DSC_{random.randint(1000, 9999)}.MP4",
        # Padrão genérico de câmara
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
    except requests.exceptions.RequestException as exc:
        st.error(f"Erro ao descarregar o vídeo da URL direta: {exc}")
        return False
    except OSError as exc:
        st.error(f"Erro ao guardar o vídeo temporário: {exc}")
        return False


def baixar_video_yt_dlp(url: str, output_path: str) -> bool:
    """Descarrega um vídeo de uma plataforma suportada através de yt-dlp com headers de browser."""
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
            # Removido aria2c para evitar bloqueios de IP agressivos
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.tiktok.com/",
                "Origin": "https://www.tiktok.com/",
            },
            "extractor_args": {
                "tiktok": {
                    "web_impersonate": "chrome", # Tentar simular Chrome via web
                }
            }
        }
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except yt_dlp.utils.DownloadError as exc:
        st.error(f"Erro ao descarregar o vídeo com yt-dlp: {exc}")
        return False
    except Exception as exc:
        st.error(f"Erro inesperado no download: {exc}")
        return False


def construir_comando_ffmpeg(
    input_path: str,
    output_path: str,
    coordenadas=None,
    altitude=None,
    resolucao_alvo=None,
):
    """Constrói um comando de limpeza e reencodificação com metadados coerentes.

    O ficheiro é efetivamente reencodificado por FFmpeg/libx264. Por isso, o
    comando não injeta VendorID, fabricante, modelo ou nome de compressor de
    Apple/Samsung, pois essas etiquetas alegariam uma origem que o conteúdo
    reencodificado não possui.
    """
    creation_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z")

    comando = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        input_path,
        "-map_metadata",
        "-1",
        "-map_metadata:s:v",
        "-1",
        "-map_metadata:s:a",
        "-1",
        "-map_chapters",
        "-1",
        "-fflags",
        "+bitexact",
        "-flags:v",
        "+bitexact",
        "-flags:a",
        "+bitexact",
        "-metadata",
        f"creation_time={creation_time}",
        "-metadata:s:v",
        "handler_name=Core Media Video",
        "-metadata:s:a",
        "handler_name=Core Media Audio",
        "-c:v",
        "libx264",            # Voltamos a encodar para injetar qualidade e esconder o rasto do TikTok
        "-preset",
        "ultrafast",
        "-crf",
        "18",                 # Qualidade visualmente sem perdas (quase nativa)
        "-maxrate",
        "25M",                # Bitrate de nível iPhone
        "-bufsize",
        "50M",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-dn",
        "-sn",
        "-map_metadata",
        "-1",
        "-movflags",
        "+faststart",
    ]

    # Resolução agora é sempre a original via 'copy', sem filtros de vídeo
    pass

    if coordenadas:
        latitude, longitude = coordenadas
        if altitude is None:
            iso6709 = f"{latitude:+.4f}{longitude:+.4f}/"
        else:
            iso6709 = f"{latitude:+.4f}{longitude:+.4f}{float(altitude):+.0f}CRS/"
        comando.extend(
            [
                # Usar apenas a tag nativa da Apple para evitar duplicação suspeita
                "-metadata",
                f"com.apple.quicktime.location.ISO6709={iso6709}",
                "-metadata",
                "make=Apple",
                "-metadata",
                "model=iPhone 15 Pro",
                "-metadata",
                "encoder=HEVC", # Disfarce de codec
            ]
        )

    comando.extend(["-y", output_path])
    return comando


def limpar_metadados_ffmpeg(
    input_path,
    output_path,
    coordenadas=None,
    altitude=None,
    resolucao_alvo=None,
):
    """Limpa metadados e reencodifica o vídeo, sem falsificar origem de hardware."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        st.error("FFmpeg não está disponível no servidor.")
        return False

    comando = construir_comando_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        coordenadas=coordenadas,
        altitude=altitude,
        resolucao_alvo=resolucao_alvo,
    )

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        st.error("O processamento excedeu o limite de 15 minutos.")
        return False
    except OSError as exc:
        st.error(f"Não foi possível executar o FFmpeg: {exc}")
        return False

    if resultado.returncode != 0:
        detalhe = (resultado.stderr or "erro desconhecido")[-500:]
        st.error(f"O FFmpeg não concluiu o processamento: {detalhe}")
        return False

    return os.path.exists(output_path) and os.path.getsize(output_path) > 0


def obter_localizacao_selecionada(usar_gps: bool):
    """Obtém a localização (automática ou fixa na sessão)."""
    if not usar_gps:
        return None, None

    cidade = st.session_state.get("metadata_pro_localizacao_fixa")
    if not cidade:
        loc = random.choice(LOCALIZACOES_REAIS)
        return (loc["lat"], loc["lon"]), loc.get("alt")

    localizacao = next(
        (item for item in LOCALIZACOES_REAIS if item["cidade"] == cidade),
        LOCALIZACOES_REAIS[0],
    )
    coordenadas = (localizacao["lat"], localizacao["lon"])
    return coordenadas, localizacao.get("alt")


def processar_video_completo(
    input_source,
    is_url,
    usar_gps,
    resolucao_alvo,
    nome_sugerido,
):
    """Executa download/upload e limpeza somente após o clique do utilizador."""
    progresso = st.progress(0, text="A preparar o processamento...")
    caminho_entrada = None
    caminho_saida = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temporario:
            caminho_entrada = temporario.name

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temporario:
            caminho_saida = temporario.name

        if is_url:
            progresso.progress(20, text="A descarregar o vídeo...")
            dominio = urlparse(input_source).netloc.lower()
            if any(rede in dominio for rede in REDES_SUPORTADAS):
                sucesso_download = baixar_video_yt_dlp(input_source, caminho_entrada)
            else:
                sucesso_download = baixar_video_de_url_direta(input_source, caminho_entrada)
            if not sucesso_download:
                return None
        else:
            with open(caminho_entrada, "wb") as ficheiro:
                ficheiro.write(input_source.getbuffer())
            progresso.progress(20, text="Ficheiro local carregado...")

        coordenadas, altitude = obter_localizacao_selecionada(usar_gps)
        progresso.progress(50, text="A limpar metadados e reencodificar...")

        sucesso = limpar_metadados_ffmpeg(
            input_path=caminho_entrada,
            output_path=caminho_saida,
            coordenadas=coordenadas,
            altitude=altitude,
            resolucao_alvo=resolucao_alvo,
        )
        if not sucesso:
            return None

        progresso.progress(100, text="Processamento concluído.")
        with open(caminho_saida, "rb") as ficheiro:
            dados = ficheiro.read()

        return {
            "nome": nome_sugerido,
            "dados": dados,
            "mime": "video/mp4",
        }
    finally:
        for caminho in (caminho_entrada, caminho_saida):
            if caminho and os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except OSError:
                    pass


def render_metadados_pro():
    st.markdown("# Metadata Pro — Limpeza de Metadados")
    st.caption(
        "Remove metadados anteriores e reencodifica o vídeo. "
        "O resultado é um ficheiro processado por FFmpeg/libx264; não é apresentado como ficheiro bruto de câmara."
    )

    with st.container(border=True):
        modo_entrada = st.radio(
            "Escolha a fonte do vídeo:",
            ["Upload de Arquivo", "URL de Vídeo"],
            horizontal=True,
        )

        uploaded_file = None
        video_url = ""
        if modo_entrada == "Upload de Arquivo":
            uploaded_file = st.file_uploader(
                "Envie o vídeo",
                type=["mp4", "mov", "mkv"],
                key="up_meta_v76",
            )
        else:
            video_url = st.text_input(
                "Cole a URL do vídeo (TikTok, Instagram, YouTube ou URL direta)",
                key="url_meta_v76",
            ).strip()

    fonte_disponivel = uploaded_file is not None or bool(video_url)
    if not fonte_disponivel:
        st.session_state.pop("metadata_pro_resultado", None)
        st.info("Forneça um vídeo. O processamento só começa quando clicar no botão de limpeza.")
        return

    coluna_info, coluna_gps = st.columns(2)
    with coluna_info:
        st.info("📺 Resolução: **Proporção Original**")
        resolucao_alvo = None  # Fixado em manter proporções original

    with coluna_gps:
        usar_gps = st.checkbox(
            "Adicionar localização (Automática)",
            value=True,
            help="Adiciona uma localização aleatória do Brasil a cada processamento.",
        )
        if usar_gps:
            # Seleção automática de localização se não houver uma fixa na sessão
            if "metadata_pro_localizacao_fixa" not in st.session_state:
                st.session_state.metadata_pro_localizacao_fixa = random.choice(LOCALIZACOES_REAIS)["cidade"]
            
            st.info(f"📍 Localização: **{st.session_state.metadata_pro_localizacao_fixa}**")
            if st.button("🔄 Trocar local", key="btn_trocar_gps"):
                st.session_state.metadata_pro_localizacao_fixa = random.choice(LOCALIZACOES_REAIS)["cidade"]
                st.rerun()

    nome_sugerido = gerar_nome_arquivo_limpo()
    identidade_fonte = (
        f"upload:{uploaded_file.name}:{uploaded_file.size}"
        if uploaded_file
        else f"url:{video_url}"
    )
    assinatura_entrada = (
        identidade_fonte,
        "original", # Resolução agora é sempre original
        usar_gps,
        st.session_state.get("metadata_pro_localizacao_fixa") if usar_gps else None,
    )
    if st.session_state.get("metadata_pro_assinatura") != assinatura_entrada:
        st.session_state.metadata_pro_assinatura = assinatura_entrada
        st.session_state.pop("metadata_pro_resultado", None)

    if uploaded_file:
        st.info(f"Fonte: `{uploaded_file.name}`")
    else:
        st.info(f"Fonte: `{urlparse(video_url).netloc or 'URL informada'}`")

    st.caption(
        "A limpeza remove metadados anteriores, mas não torna indetetável o uso de software de edição. "
        "Analisadores podem identificar características compatíveis com FFmpeg/libx264."
    )

    if st.button(
        "Limpar metadados",
        type="primary",
        use_container_width=True,
        key="btn_limpar_metadata_pro",
    ):
        if video_url and not validar_url_video(video_url):
            st.error("Informe uma URL HTTP ou HTTPS válida.")
            st.session_state.pop("metadata_pro_resultado", None)
        else:
            resultado = processar_video_completo(
                input_source=uploaded_file if uploaded_file else video_url,
                is_url=uploaded_file is None,
                usar_gps=usar_gps,
                resolucao_alvo=resolucao_alvo,
                nome_sugerido=nome_sugerido,
            )
            if resultado:
                st.session_state.metadata_pro_resultado = resultado
                # Rotacionar localização para a próxima geração se estiver no modo automático
                if usar_gps:
                    st.session_state.metadata_pro_localizacao_fixa = random.choice(LOCALIZACOES_REAIS)["cidade"]
                st.success("Vídeo processado. O ficheiro está pronto para download.")
            else:
                st.session_state.pop("metadata_pro_resultado", None)

    resultado_pronto = st.session_state.get("metadata_pro_resultado")
    if resultado_pronto:
        st.download_button(
            label="Baixar vídeo limpo",
            data=resultado_pronto["dados"],
            file_name=resultado_pronto["nome"],
            mime=resultado_pronto["mime"],
            use_container_width=True,
            on_click="ignore",
            key="download_metadata_pro",
        )
