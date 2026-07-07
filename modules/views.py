# modules/views.py - ADICIONAR NO FINAL DO ARQUIVO

def render_insights_interativos(produtos):
    """
    Renderiza insights interativos que levam para a tab de conteúdo
    """
    if not produtos:
        return
    
    st.markdown("## 💡 Insights Estratégicos - Top 3")
    
    top3 = sorted(produtos, key=lambda x: x.get("Score", 0), reverse=True)[:3]
    cols = st.columns(3)
    
    for i, item in enumerate(top3):
        with cols[i]:
            produto_nome = item.get("Produto", "")
            
            with st.container(border=True):
                # Emoji do ranking
                emojis = ["🥇", "🥈", "🥉"]
                st.markdown(f"### {emojis[i]} {produto_nome}")
                
                # Métricas resumidas
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Score", f"{item.get('Score', 0)}/10")
                    st.metric("Crescimento", item.get('Crescimento', '+0%'))
                with col2:
                    st.metric("Views TikTok", item.get('Views TikTok', '0M'))
                    st.metric("Pins", item.get('Pins', '0'))
                
                # Palavra-chave
                produto_lower = produto_nome.lower()
                dados_palavra = obter_palavra_chave(produto_lower)
                palavra_chave = dados_palavra.get("palavra", f"{produto_lower} tendência 2026")
                st.info(f"🔑 **Palavra-chave:** {palavra_chave}")
                
                # Hashtags resumidas
                hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:3]
                tags_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 2px 8px; border-radius: 12px; margin: 2px; font-size: 11px;">{h}</span>' for h in hashtags])
                st.markdown(tags_html, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Botão "Criar Conteúdo" - vai para a tab de conteúdo
                if st.button(f"🎬 Criar Conteúdo para {produto_nome}", key=f"insight_{produto_nome}", use_container_width=True):
                    # Salva no session_state para a tab de conteúdo
                    st.session_state.produto_conteudo = produto_nome
                    st.success(f"✅ Redirecionando para criar conteúdo sobre {produto_nome}...")
                    st.rerun()
