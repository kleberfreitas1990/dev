    # ============================================================
    # VISÃO GERAL DO MÊS - COMPLETA (MENSAGEM + MÉTRICAS + OPORTUNIDADE + SUGESTÕES + TOP 3)
    # ============================================================
    st.markdown("## 📊 Visão Geral do Mês")
    
    produtos_top = gerar_top10_produtos(forcar_atualizacao=False)
    produtos_sugestoes = gerar_sugestoes_diarias(forcar_atualizacao=True)
    
    if produtos_top:
        top1 = produtos_top[0] if produtos_top else None
        
        scores = [p.get("Score", 0) for p in produtos_top]
        crescimentos = [float(p.get("Crescimento", "+0%").replace("+", "").replace("%", "")) for p in produtos_top]
        
        score_medio = sum(scores) / len(scores) if scores else 0
        crescimento_medio = sum(crescimentos) / len(crescimentos) if crescimentos else 0
        
        categorias = [p.get("Categoria", "Geral") for p in produtos_top]
        categoria_mais_freq = max(set(categorias), key=categorias.count) if categorias else "Geral"
        
        eventos = [p.get("Evento", "Tendência") for p in produtos_top]
        evento_mais_freq = max(set(eventos), key=eventos.count) if eventos else "Tendência"
        
        # ============================================================
        # LINHA 1: MENSAGEM DESTAQUE
        # ============================================================
        if top1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 16px;
                text-align: center;
            ">
                <span style="font-size: 18px; font-weight: bold;">🔥 {top1.get('Produto', 'Produto')} em alta!</span>
                <span style="font-size: 15px; margin-left: 10px;">
                    Com score {top1.get('Score', 0)}/10 e {top1.get('Crescimento', '+0%')} de crescimento, 
                    este é o momento ideal para criar conteúdo sobre este produto.
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 16px;
                text-align: center;
            ">
                <span style="font-size: 18px; font-weight: bold;">📊 Análise de mercado em tempo real</span>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================================
        # LINHA 2: MÉTRICAS + OPORTUNIDADE
        # ============================================================
        col1, col2 = st.columns([2, 1])
        
        with col1:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(
                    label="🔥 Produto em Alta",
                    value=top1.get("Produto", "N/A") if top1 else "N/A",
                    delta=top1.get("Categoria", "Moda") if top1 else "N/A"
                )
            with m2:
                st.metric(
                    label="📈 Crescimento Médio",
                    value=f"{crescimento_medio:.1f}%",
                    delta=f"{crescimento_medio - 5:.1f}%"
                )
            with m3:
                st.metric(
                    label="🎯 Categoria em Alta",
                    value=categoria_mais_freq,
                    delta=evento_mais_freq
                )
        
        with col2:
            with st.container(border=True):
                st.markdown("### 🎯 Melhor Oportunidade")
                
                melhor_score = max(produtos_top, key=lambda x: x.get("Score", 0)) if produtos_top else None
                
                if melhor_score:
                    produto_nome = melhor_score.get('Produto', 'N/A')
                    score = melhor_score.get('Score', 0)
                    
                    indicadores = obter_indicadores_horario(produto_nome)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**{produto_nome}**")
                    with col_b:
                        st.markdown(f"⭐ **{score}/10**")
                    
                    if indicadores:
                        st.markdown(f"""
                        <div style="
                            background: #f0f0f0; 
                            padding: 4px 10px; 
                            border-radius: 6px; 
                            margin: 6px 0; 
                            font-size: 12px; 
                            color: #333; 
                            text-align: center;
                        ">
                            🕐 Melhor horário: <strong>{indicadores.get('melhor_horario', '19h-22h')}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    potencial = score * 10
                    cor = "green" if potencial >= 70 else "orange" if potencial >= 40 else "red"
                    
                    st.markdown(f"""
                    <div style="margin: 6px 0;">
                        <small>Potencial de Mercado</small>
                        <div style="
                            background: #e0e0e0; 
                            border-radius: 8px; 
                            height: 18px; 
                            position: relative; 
                            overflow: hidden;
                        ">
                            <div style="
                                background: {cor}; 
                                width: {potencial}%; 
                                height: 18px; 
                                border-radius: 8px; 
                                transition: width 0.5s;
                            ">
                                <span style="
                                    position: absolute; 
                                    left: 50%; 
                                    top: 1px; 
                                    color: {'white' if potencial > 50 else 'black'}; 
                                    font-weight: bold; 
                                    font-size: 11px;
                                ">{potencial:.0f}%</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success(f"✅ {score}/10 Score")
                    with col_b:
                        st.success(f"📈 {melhor_score.get('Crescimento', '+0%')}")
                else:
                    st.info("📊 Aguardando dados...")
        
        # ============================================================
        # LINHA 3: SUGESTÕES DE PRODUTOS PARA HOJE
        # ============================================================
        st.markdown("---")
        st.markdown("### 🎯 Sugestões de Produtos para Hoje")
        st.caption(f"📊 Top {BUSCAS_DIARIAS} do dia | Buscas realizadas com base em tendências atuais")
        
        if produtos_sugestoes:
            cols = st.columns(3)
            
            for i, item in enumerate(produtos_sugestoes[:3]):
                with cols[i]:
                    produto_nome = item.get("Produto", "")
                    score = item.get("Score", 0)
                    categoria = item.get("Categoria", "Geral")
                    crescimento = item.get("Crescimento", "+0%")
                    views = item.get("Views TikTok", "0M")
                    pins = item.get("Pins", "0")
                    tendencia = item.get("Tendência", "➡️ Estável")
                    
                    if score >= 8:
                        cor_fundo = "#e8f5e9"
                        cor_borda = "#4CAF50"
                        emoji = "🔥"
                    elif score >= 6:
                        cor_fundo = "#fff3e0"
                        cor_borda = "#FF9800"
                        emoji = "📈"
                    else:
                        cor_fundo = "#fce4ec"
                        cor_borda = "#f44336"
                        emoji = "📊"
                    
                    icones = ["🥇", "🥈", "🥉"]
                    
                    st.markdown(f"""
                    <div style="
                        background: {cor_fundo};
                        border-left: 4px solid {cor_borda};
                        border-radius: 8px;
                        padding: 12px 14px;
                        margin: 4px 0;
                        height: 100%;
                    ">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span style="font-size: 20px;">{icones[i]}</span>
                            <span style="font-weight: bold; font-size: 15px; color: #333;">{produto_nome}</span>
                            <span style="font-size: 13px; margin-left: auto; background: {cor_borda}; color: white; padding: 1px 10px; border-radius: 12px;">{emoji} {score}/10</span>
                        </div>
                        <div style="display: flex; gap: 10px; font-size: 12px; color: #555; flex-wrap: wrap; margin-top: 4px;">
                            <span>📂 {categoria}</span>
                            <span>📈 {crescimento}</span>
                            <span>👁️ {views}</span>
                            <span>📌 {pins}</span>
                            <span>{tendencia}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with st.expander("📋 Ver detalhes completos", expanded=False):
                dados_tabela = []
                for item in produtos_sugestoes:
                    produto = item.get("Produto", "").lower()
                    dados_palavra = obter_palavra_chave(produto)
                    palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
                    
                    dados_tabela.append({
                        "Produto": item.get("Produto", ""),
                        "Palavra-chave": palavra_chave,
                        "Categoria": item.get("Categoria", "Geral"),
                        "Score": item.get("Score", 0),
                        "Crescimento": item.get("Crescimento", "+0%"),
                        "Views TikTok": item.get("Views TikTok", "0M"),
                        "Pins": item.get("Pins", "0"),
                        "Tendência": item.get("Tendência", "➡️ Estável")
                    })
                
                df = pd.DataFrame(dados_tabela)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"💡 {BUSCAS_DIARIAS} sugestões geradas com base em tendências atuais de mercado")
        else:
            st.info("📭 Nenhuma sugestão disponível no momento.")
        
        # ============================================================
        # LINHA 4: TOP 3 PRODUTOS DO MÊS (INTEGRADO)
        # ============================================================
        st.markdown("---")
        st.markdown("### 🏆 Top 3 Produtos do Mês")
        st.caption("Produtos com maior potencial - Use essas informações para criar conteúdo")
        
        # Exibe os Top 3 em cards
        top3 = sorted(produtos_top, key=lambda x: x.get("Score", 0), reverse=True)[:3]
        
        cols = st.columns(3)
        for i, item in enumerate(top3):
            with cols[i]:
                produto_nome = item.get("Produto", "")
                score = item.get("Score", 0)
                crescimento = item.get("Crescimento", "+0%")
                views = item.get("Views TikTok", "0M")
                pins = item.get("Pins", "0")
                
                indicadores = obter_indicadores_horario(produto_nome)
                horario = indicadores.get("melhor_horario", "19h-22h") if indicadores else "19h-22h"
                
                dados_palavra = obter_palavra_chave(produto_nome)
                palavra_chave = dados_palavra.get("palavra", f"{produto_nome} tendência 2026")
                hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:3]
                
                emojis = ["🥇", "🥈", "🥉"]
                
                with st.container(border=True):
                    st.markdown(f"### {emojis[i]} {produto_nome}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Score", f"{score}/10")
                    with col2:
                        st.metric("Crescimento", crescimento)
                    
                    st.markdown(f"""
                    <div style="
                        background: #f0f0f0; 
                        padding: 6px 10px; 
                        border-radius: 6px; 
                        margin: 6px 0;
                    ">
                        <div style="font-size: 12px; color: #333;">
                            🔑 <strong>Palavra-chave:</strong> {palavra_chave}
                        </div>
                        <div style="margin-top: 4px; font-size: 11px;">
                            {' '.join([f'<span style="background: #e0e0e0; padding: 2px 10px; border-radius: 12px; margin: 2px;">{h}</span>' for h in hashtags])}
                        </div>
                        <div style="margin-top: 4px; font-size: 11px; color: #555;">
                            🕐 Melhor horário: <strong>{horario}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"👁️ {views}")
                    with col2:
                        st.caption(f"📌 {pins}")
    
    else:
        # Fallback sem dados
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 10px;
            margin-bottom: 16px;
            text-align: center;
        ">
            <span style="font-size: 18px; font-weight: bold;">📊 Análise de mercado em tempo real</span>
            <span style="font-size: 15px; margin-left: 10px;">Buscando os melhores produtos para você criar conteúdo.</span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("🔥 Produto em Alta", "Aguardando", delta="...")
            with m2:
                st.metric("📈 Crescimento Médio", "0%", delta="0%")
            with m3:
                st.metric("🎯 Categoria em Alta", "Geral", delta="Tendência")
        
        with col2:
            with st.container(border=True):
                st.markdown("### 🎯 Melhor Oportunidade")
                st.info("📊 Carregando dados...")
                st.caption("🟢 Aguardando análise")
        
        st.markdown("---")
        st.markdown("### 🎯 Sugestões de Produtos para Hoje")
        st.info("📭 Nenhuma sugestão disponível no momento.")
        
        st.markdown("---")
        st.markdown("### 🏆 Top 3 Produtos do Mês")
        st.info("📭 Aguardando dados...")
    
    st.markdown("---")
