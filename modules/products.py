import streamlit as st
import pandas as pd

def render_products(df):
    st.markdown("## 🎯 Sugestões de Produtos Estratégicos")
    st.caption("Produtos em alta baseados em tendências de mercado e datas comemorativas")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Produto": "Produto",
            "Categoria": "Categoria",
            "Evento": "Evento Relacionado",
            "Potencial": "Potencial",
            "Pins": "Pins no Pinterest",
            "Crescimento": "Crescimento",
            "Views": "Visualizações TikTok",
            "Resultados": "Resultados",
            "Buscar na Shopee": st.column_config.LinkColumn("Buscar na Shopee", validate=False)
        }
    )
