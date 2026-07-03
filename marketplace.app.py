# ===== TAB 3: ANÁLISE DE SATURAÇÃO =====
with tab3:
    st.markdown("### 🎯 Análise de Saturação de Mercado")
    st.caption("Quanto menor o número de resultados, menor a concorrência!")
    
    termo_busca = st.text_input("🔍 Digite um produto:", placeholder="Ex: smartwatch, fone bluetooth...")
    
    if termo_busca and st.button("📊 Analisar Saturação"):
        with st.spinner(f"Analisando '{termo_busca}'..."):
            # Busca dados
            total_ml = buscar_total_resultados_ml(termo_busca)
            total_shopee = buscar_total_resultados_shopee(termo_busca)
            total = total_ml + total_shopee
            saturacao = analisar_saturacao(total)
            produtos_ml = buscar_produtos_mercadolivre(termo_busca, 3)
            produtos_shopee = buscar_produtos_shopee(termo_busca, 3)
            
            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("🔵 ML", f"{total_ml}")
            c2.metric("🟠 Shopee", f"{total_shopee}")
            c3.metric("📊 Total", f"{total}")
            
            st.markdown("---")
            
            # Status com cores
            cores = [
                (total < 50, st.success, "✅"),
                (total < 200, st.info, "📊"),
                (total < 500, st.warning, "⚠️"),
                (True, st.error, "🚨")
            ]
            for cond, func, icon in cores:
                if cond:
                    func(f"{icon} **{saturacao['nivel']}**")
                    func(f"💡 {saturacao['recomendacao']}")
                    break
            
            st.markdown("---")
            
            # Produtos
            c1, c2 = st.columns(2)
            
            def mostrar_produtos(col, produtos, nome, emoji):
                col.markdown(f"#### {emoji} {nome}")
                if produtos:
                    for p in produtos[:3]:
                        col.markdown(f"- **{p.get('nome', '')}**")
                        col.markdown(f"  💰 {p.get('preco', '')} | 📦 {p.get('vendas', 0)} vendidos")
                        if p.get('link'):
                            col.markdown(f"  [🔗 Ver]({p['link']})")
                        col.markdown("")
                else:
                    col.info(f"Nenhum produto no {nome}")
            
            mostrar_produtos(c1, produtos_ml, "Mercado Livre", "🔵")
            mostrar_produtos(c2, produtos_shopee, "Shopee", "🟠")
            
            # Links rápidos
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.link_button("🔍 ML", f"https://lista.mercadolivre.com.br/{quote(termo_busca)}", width='stretch')
            c2.link_button("🔍 Shopee", f"https://shopee.com.br/search?keyword={quote(termo_busca)}", width='stretch')
