    # ===== TAB 3: ANÁLISE DE SATURAÇÃO =====
    with tab3:
        st.markdown("### 🎯 Análise de Saturação de Mercado")
        st.markdown("""
        Esta ferramenta analisa quantos resultados existem para um produto no Mercado Livre e Shopee.
        **Quanto menor o número de resultados, menor a concorrência!**
        """)
        
        # Buscador de saturação
        termo_busca = st.text_input("🔍 Digite um produto para analisar:", placeholder="Ex: smartwatch, fone bluetooth...")
        
        if termo_busca:
            if st.button("📊 Analisar Saturação"):
                with st.spinner(f"Analisando saturação para '{termo_busca}'..."):
                    # Busca totais
                    total_ml = buscar_total_resultados_ml(termo_busca)
                    total_shopee = buscar_total_resultados_shopee(termo_busca)
                    total_geral = total_ml + total_shopee
                    
                    # Análise de saturação
                    saturacao = analisar_saturacao(total_geral)
                    
                    # Busca produtos para mostrar
                    produtos_ml = buscar_produtos_mercadolivre(termo_busca, 3)
                    produtos_shopee = buscar_produtos_shopee(termo_busca, 3)
                    
                    # Exibe resultados
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("🔵 Mercado Livre", f"{total_ml} resultados")
                    
                    with col2:
                        st.metric("🟠 Shopee", f"{total_shopee} resultados")
                    
                    with col3:
                        st.metric("📊 Total", f"{total_geral} resultados")
                    
                    st.markdown("---")
                    
                    # Status de saturação
                    if total_geral < 50:
                        st.success(f"✅ **{saturacao['nivel']}**")
                        st.info(f"💡 {saturacao['recomendacao']}")
                    elif total_geral < 200:
                        st.info(f"📊 **{saturacao['nivel']}**")
                        st.info(f"💡 {saturacao['recomendacao']}")
                    elif total_geral < 500:
                        st.warning(f"⚠️ **{saturacao['nivel']}**")
                        st.warning(f"💡 {saturacao['recomendacao']}")
                    else:
                        st.error(f"🚨 **{saturacao['nivel']}**")
                        st.error(f"💡 {saturacao['recomendacao']}")
                    
                    st.markdown("---")
                    
                    # Produtos encontrados
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🔵 Produtos no Mercado Livre")
                        if produtos_ml:
                            for p in produtos_ml[:3]:
                                st.markdown(f"- {p.get('nome', '')}")
                                st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                                if p.get('link'):
                                    st.markdown(f"  [🔗 Ver produto]({p['link']})")
                                st.markdown("")
                        else:
                            st.info("Nenhum produto encontrado no Mercado Livre")
                    
                    with col2:
                        st.markdown("#### 🟠 Produtos na Shopee")
                        if produtos_shopee:
                            for p in produtos_shopee[:3]:
                                st.markdown(f"- {p.get('nome', '')}")
                                st.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                                if p.get('link'):
                                    st.markdown(f"  [🔗 Ver produto]({p['link']})")
                                st.markdown("")
                        else:
                            st.info("Nenhum produto encontrado na Shopee")
                    
                    # Links para busca
                    st.markdown("---")
                    st.markdown("### 🔍 Buscar diretamente")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.link_button(
                            "🔍 Buscar no Mercado Livre",
                            f"https://lista.mercadolivre.com.br/{quote(termo_busca)}",
                            use_container_width=True
                        )
                    with col2:
                        st.link_button(
                            "🔍 Buscar na Shopee",
                            f"https://shopee.com.br/search?keyword={quote(termo_busca)}",
                            use_container_width=True
                        )
