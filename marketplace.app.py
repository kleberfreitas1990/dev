class SnapGenVideoGenerator:
    def __init__(self):
        self.api_key = SNAPGEN_API_KEY
        self.email = SNAPGEN_EMAIL
        self.password = SNAPGEN_PASSWORD
        self.galeria = GaleriaVideos()
        self.creditos = CreditosDiarios()
        # Endpoint correto baseado na documentação
        self.base_url = "https://api.snapgen.ai/uapi/v1/generate"

    def gerar_video(self, prompt, licenca, duracao=6, resolucao="480p", estilo="Realista", modelo="SnapGen"):
        # Verificação de créditos e credenciais permanece igual
        if not self.api_key and not (self.email and self.password):
            return {"erro": "Credenciais SnapGen não configuradas. Adicione SNAPGEN_API_KEY ou SNAPGEN_EMAIL e SNAPGEN_PASSWORD no secrets.toml"}
        
        if not self.creditos.usar_credito(licenca):
            return {"erro": "Créditos diários esgotados. Volte amanhã!"}
        
        try:
            # Cabeçalhos com a chave de API no formato correto
            headers = {
                "x-api-key": self.api_key,  # Mudança chave: de 'Authorization: Bearer' para 'x-api-key'
                "Content-Type": "application/json"
            }
            
            # Se não tiver API Key, tenta autenticar com email/senha para obter uma chave de sessão
            if not self.api_key and self.email and self.password:
                # A documentação não detalha um endpoint de login, mas mantemos a tentativa como fallback
                try:
                    auth_response = requests.post(
                        "https://api.snapgen.ai/auth/login", # Endpoint hipotético
                        json={"email": self.email, "password": self.password},
                        timeout=10
                    )
                    if auth_response.status_code == 200:
                        session_key = auth_response.json().get("api_key") # Ajuste o campo conforme a resposta real
                        if session_key:
                            headers["x-api-key"] = session_key
                except Exception as auth_err:
                    # Se falhar, retorna erro
                    return {"erro": f"Falha na autenticação com email/senha: {str(auth_err)}. Verifique suas credenciais ou use uma API Key."}
            
            # Verifica se temos uma chave para enviar
            if "x-api-key" not in headers or not headers["x-api-key"]:
                return {"erro": "Nenhuma chave de API válida encontrada. Configure SNAPGEN_API_KEY."}

            # Payload adaptado para o formato esperado pela API
            # A documentação mostra um campo "type" para especificar o tipo de geração.
            # Assumimos que "type": "video" é o correto para vídeos.
            payload = {
                "type": "video",  # <--- ESSENCIAL: Define o tipo de geração
                "prompt": prompt,
                "duration": duracao,
                "aspect_ratio": "9:16",
                "style": estilo,
                "model": modelo,
                "resolution": resolucao
            }
            
            st.info(f"🎬 Iniciando geração com SnapGen...")
            st.caption(f"⏱️ Duração: {duracao}s | 📐 9:16 | 📺 {resolucao}")
            
            # Faz a requisição POST para o endpoint correto
            response = requests.post(
                self.base_url,  # Agora usando o endpoint correto
                json=payload,
                headers=headers,
                timeout=90 # Aumenta o timeout para geração de vídeo
            )
            
            # Processa a resposta
            if response.status_code == 200:
                data = response.json()
                
                # A estrutura de resposta pode variar. Vamos tentar encontrar a URL do vídeo.
                video_url = None
                if "video_url" in data:
                    video_url = data["video_url"]
                elif "url" in data:
                    video_url = data["url"]
                elif "output" in data and "url" in data["output"]:
                    video_url = data["output"]["url"]
                elif "data" in data and "url" in data["data"]:
                    video_url = data["data"]["url"]

                if video_url:
                    # Baixa o vídeo
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
                        return {"erro": f"Erro ao baixar vídeo: Status {video_response.status_code}"}
                else:
                    # Se não encontrou URL, retorna a resposta completa para debug
                    return {"erro": f"Resposta da API não contém URL de vídeo: {data}"}
            else:
                # Tenta extrair mensagem de erro detalhada
                try:
                    erro_detalhado = response.json()
                except:
                    erro_detalhado = response.text
                return {"erro": f"Erro na geração (Status {response.status_code}): {erro_detalhado}"}
                
        except requests.exceptions.Timeout:
            return {"erro": "A requisição excedeu o tempo limite. A geração de vídeo pode estar demorando mais que o esperado."}
        except Exception as e:
            return {"erro": f"Erro na geração: {str(e)}"}
