import streamlit as st
import requests
import os
import time
import json
from datetime import datetime

class SnapGenVideoGenerator:
    def __init__(self, api_key=None, email=None, password=None, galeria=None, creditos=None):
        self.api_key = api_key
        self.email = email
        self.password = password
        self.galeria = galeria
        self.creditos = creditos
        self.base_url = "https://api.snapgen.ai"
    
    def gerar_video(self, prompt, licenca, duracao=6, resolucao="480p", estilo="Realista", modelo="SnapGen"):
        if not self.api_key and not (self.email and self.password):
            return {"erro": "Credenciais SnapGen não configuradas"}
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Créditos diários esgotados. Volte amanhã!"}
        
        try:
            headers = {"Content-Type": "application/json"}
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.email and self.password:
                # Tentativa de autenticação
                auth_response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"email": self.email, "password": self.password},
                    timeout=10
                )
                if auth_response.status_code == 200:
                    token = auth_response.json().get("token")
                    headers["Authorization"] = f"Bearer {token}"
                else:
                    # Fallback: tenta usar API key diretamente se disponível
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"
                    else:
                        return {"erro": f"Falha na autenticação: {auth_response.text}"}
            
            payload = {
                "prompt": prompt,
                "duration": duracao,
                "aspect_ratio": "9:16",
                "style": estilo,
                "model": modelo,
                "resolution": resolucao
            }
            
            st.info(f"🎬 Iniciando geração com SnapGen...")
            st.caption(f"⏱️ Duração: {duracao}s | 📐 9:16 | 📺 {resolucao}")
            
            # Tenta diferentes endpoints
            endpoints = [
                f"{self.base_url}/generate",
                f"{self.base_url}/v1/generate",
                f"{self.base_url}/video/generate"
            ]
            
            response = None
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=60
                    )
                    if response.status_code == 200:
                        break
                except:
                    continue
            
            if response is None:
                return {"erro": "Nenhum endpoint disponível"}
            
            if response.status_code == 200:
                data = response.json()
                
                if "video_url" in data or "url" in data:
                    video_url = data.get("video_url") or data.get("url")
                    
                    video_response = requests.get(video_url, timeout=30)
                    if video_response.status_code == 200:
                        filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        with open(filename, "wb") as f:
                            f.write(video_response.content)
                        
                        video_info = {
                            "url": filename,
                            "prompt": prompt,
                            "duracao": duracao,
                            "resolucao": resolucao,
                            "estilo": estilo,
                            "modelo": modelo,
                            "status": "concluido"
                        }
                        
                        self.galeria.adicionar(video_info)
                        st.success("✅ Vídeo gerado com sucesso!")
                        return video_info
                    else:
                        return {"erro": f"Erro ao baixar vídeo: {video_response.status_code}"}
                else:
                    return {"erro": f"Erro: {data}"}
            else:
                return {"erro": f"Erro na geração: {response.text}"}
                
        except Exception as e:
            return {"erro": f"Erro na geração: {str(e)}"}

def render_video_generator(creditos, licenca, creditos_restantes, creditos_diarios, galeria, snapgen_api_key, snapgen_email, snapgen_password):
    st.markdown("## 🎬 Criar Vídeo com IA (9:16)")
    st.caption("Gere vídeos para TikTok, Reels e Shorts com SnapGen AI")
    
    if not (snapgen_api_key or (snapgen_email and snapgen_password)):
        st.warning("⚠️ **Credenciais SnapGen não configuradas.**")
        st.info("Configure no arquivo .streamlit/secrets.toml")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🎨 Configuração do Vídeo")
        
        modelo = st.selectbox(
            "Modelo",
            ["SnapGen", "SnapGen Fast", "SnapGen Pro"],
            help="SnapGen Pro tem melhor qualidade | Fast é mais rápido"
        )
        
        imagem_upload = st.file_uploader(
            "Selecionar Imagem (opcional)",
            type=["png", "jpg", "jpeg", "webp"]
        )
        
        prompt = st.text_area(
            "Comando",
            placeholder="Descreva o vídeo que deseja gerar...",
            height=120
        )
    
    with col2:
        st.markdown("#### ⚙️ Configurações Técnicas")
        
        resolucao = st.radio(
            "Qualidade",
            ["480p", "720p", "1080p"],
            index=1
        )
        
        duracao = st.selectbox(
            "Duração (segundos)",
            [4, 6, 8, 10],
            index=1
        )
        
        estilo = st.selectbox(
            "Estilo Visual",
            ["Realista", "Cinematográfico", "Animado", "Minimalista", "Vintage"]
        )
        
        st.markdown("---")
        
        if creditos_restantes > 0:
            st.metric("🎫 Créditos restantes", f"{creditos_restantes} / {creditos_diarios}")
        else:
            st.error("❌ Créditos esgotados! Volte amanhã.")
        
        if st.button("🚀 Gerar Vídeo", type="primary", width='stretch'):
            if not prompt:
                st.error("❌ Por favor, descreva o vídeo no campo 'Comando'.")
            elif not (snapgen_api_key or (snapgen_email and snapgen_password)):
                st.error("❌ Credenciais SnapGen não configuradas.")
            elif creditos_restantes <= 0:
                st.error("❌ Créditos esgotados! Volte amanhã.")
            else:
                generator = SnapGenVideoGenerator(
                    api_key=snapgen_api_key,
                    email=snapgen_email,
                    password=snapgen_password,
                    galeria=galeria,
                    creditos=creditos
                )
                
                resultado = generator.gerar_video(
                    prompt=prompt,
                    licenca=licenca,
                    duracao=duracao,
                    resolucao=resolucao,
                    estilo=estilo,
                    modelo=modelo
                )
                
                if "erro" in resultado:
                    st.error(f"❌ {resultado['erro']}")
                else:
                    st.success("✅ Vídeo gerado com sucesso!")
                    
                    if os.path.exists(resultado["url"]):
                        st.video(resultado["url"])
                        with open(resultado["url"], "rb") as f:
                            st.download_button(
                                label="📥 Baixar Vídeo",
                                data=f,
                                file_name=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                    
                    st.rerun()
    
    # ===== GALERIA DE VÍDEOS =====
    st.markdown("---")
    st.markdown("### 🖼️ Galeria de Vídeos Gerados")
    
    videos = galeria.listar(12)
    
    if videos:
        cols = st.columns(4)
        for i, video in enumerate(videos[:8]):
            with cols[i % 4]:
                with st.container(border=True):
                    if os.path.exists(video.get("url", "")):
                        st.video(video["url"])
                        with open(video["url"], "rb") as f:
                            st.download_button(
                                label="📥 Baixar",
                                data=f,
                                file_name=os.path.basename(video["url"]),
                                mime="video/mp4",
                                key=f"dl_{video.get('id', i)}"
                            )
                    else:
                        st.video(video.get("url", "https://placehold.co/600x400/000000/FFFFFF?text=Video"))
                    
                    st.caption(f"🎬 {video.get('modelo', 'IA')}")
                    st.caption(f"📝 {video.get('prompt', '')[:40]}...")
                    st.caption(f"⏱️ {video.get('duracao', 6)}s | {video.get('resolucao', '480p')}")
                    
                    if st.button("🗑️ Remover", key=f"del_{video.get('id', i)}"):
                        if os.path.exists(video.get("url", "")):
                            os.remove(video["url"])
                        galeria.remover(video.get('id'))
                        st.rerun()
    else:
        st.info("📭 Nenhum vídeo gerado ainda. Crie seu primeiro vídeo acima!")
