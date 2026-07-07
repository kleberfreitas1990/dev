# ============================================================
# GRADE DE DESCOBERTA - VISUALIZAÇÃO EM TABELA
# ============================================================
def render_grade_descoberta():
    """
    Renderiza a grade de descoberta de produtos em formato de tabela
    """
    st.markdown("## 🎯 Grade de Descoberta de Produtos")
    st.caption("Produtos em tendência descobertos automaticamente")
    
    # ============================================================
    # FILTROS
    # ============================================================
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        categoria_filtro = st.selectbox(
            "Filtrar por categoria:",
            ["Todas", "moda", "eletrônico", "beleza", "casa", "infantil", "esporte"],
            index=0
        )
    
    with col2:
        quantidade = st.selectbox(
            "Quantidade:",
            [5, 10, 15, 20],
            index=1
        )
    
    with col3:
        if st.button("🔄 Atualizar Grade", use_container_width=True):
            st.rerun()
    
    # ============================================================
    # BUSCA PRODUTOS
    # ============================================================
    with st.spinner("🔍 Descobrindo produtos..."):
        categoria = None if categoria_filtro == "Todas" else categoria_filtro
        produtos_descobrir = descobrir_produtos_grade(categoria=categoria, quantidade=quantidade)
    
    if not produtos_descobrir:
        st.info("📭 Nenhum produto encontrado na grade de descoberta.")
        return
    
    # ============================================================
    # EXIBE EM TABELA
    # ============================================================
    st.markdown(f"### 📦 {len(produtos_descobrir)} produtos descobertos")
    
    # Cria DataFrame
    dados_tabela = []
    for item in produtos_descobrir:
        produto = item.get("produto", "").capitalize()
        fonte = item.get("fonte", "grade")
        score = item.get("score", 0)
        categoria = item.get("categoria", "Geral")
        
        # Mapeia fonte para emoji
        fonte_emoji = {
            "sazonal": "📅",
            "grade": "📊",
            "api": "🌐",
            "raspagem": "📡"
        }.get(fonte, "📌")
        
        # Botão Criar Conteúdo (como HTML para ficar na tabela)
        botao_html = f'<a href="#" onclick="document.getElementById(\'criar_conteudo_{produto.lower()}\').click(); return false;" style="text-decoration: none;"><span style="background-color: #FF6B6B; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; border: none; cursor: pointer;">🎬 Criar</span></a>'
        
        dados_tabela.append({
            "Produto": produto,
            "Categoria": categoria,
            "Fonte": f"{fonte_emoji} {fonte.capitalize()}",
            "Score": f"{score}/10",
            "Buscar na Shopee": f'<a href="https://shopee.com.br/search?keyword={quote(item.get("produto", ""))}" target="_blank" style="text-decoration: none;"><span style="background-color: #f0f0f0; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ddd;">🔍 Buscar</span></a>',
            "🎬 Ação": botao_html
        })
    
    df = pd.DataFrame(dados_tabela)
    
    # Estiliza e exibe a tabela
    st.markdown(
        df.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )
    
    # ============================================================
    # PRODUTOS SAZONAIS (EM TABELA)
    # ============================================================
    st.markdown("---")
    st.markdown("### 📅 Produtos Sazonais do Mês")
    
    sazonais = get_produtos_sazonais()
    if sazonais:
        dados_sazonais = []
        for i, produto in enumerate(sazonais):
            dados_sazonais.append({
                "Produto": produto.capitalize(),
                "Status": "📅 Em alta",
                "🎬 Ação": f'<a href="#" onclick="document.getElementById(\'criar_sazonal_{i}\').click(); return false;" style="text-decoration: none;"><span style="background-color: #FF6B6B; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; border: none; cursor: pointer;">🎬 Criar</span></a>'
            })
        
        df_sazonais = pd.DataFrame(dados_sazonais)
        st.markdown(
            df_sazonais.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
        
        # Botões ocultos para criar conteúdo
        for i, produto in enumerate(sazonais):
            if st.button(f"criar_sazonal_{i}", key=f"btn_sazonal_{i}", hidden=True):
                st.session_state.produto_conteudo = produto
                st.session_state.aba_conteudo = True
                st.success(f"✅ Produto '{produto}' selecionado! Vá para a tab '🤖 Criar Conteúdo'.")
    else:
        st.info("📭 Nenhum produto sazonal para este mês.")
    
    # Botões ocultos para criar conteúdo da tabela principal
    for item in produtos_descobrir:
        produto = item.get("produto", "")
        if st.button(f"criar_conteudo_{produto.lower()}", key=f"btn_grade_{produto.lower()}", hidden=True):
            st.session_state.produto_conteudo = produto
            st.session_state.aba_conteudo = True
            st.success(f"✅ Produto '{produto}' selecionado! Vá para a tab '🤖 Criar Conteúdo'.")
