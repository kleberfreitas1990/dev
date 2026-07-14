import streamlit as st
import pandas as pd
from modules.produtos_dinamicos import obter_produtos_dinamicos

def render_metadados_pro():
    st.markdown("## 📈 Metadados Pro")
    st.caption("Análise aprofundada e métricas detalhadas dos produtos em tendência.")

    produtos = obter_produtos_dinamicos()

    if produtos:
        dados_tabela = []
        for nome_produto, dados in produtos.items():
            dados_tabela.append({
                "Produto": nome_produto,
                "Score": dados.get("score", 0),
                "Categoria": dados.get("categoria", "Geral"),
                "Evento": dados.get("evento", "Tendência"),
                "Pins": dados.get("pins", 0),
                "Crescimento": f"{dados.get("crescimento", 0)}%",
                "Views TikTok": f"{dados.get("views_tiktok", 0)}M",
                "Buscas no Mês": dados.get("buscas_mes", 0),
                "Resultados ML": dados.get("resultados_ml", 0),
                "Tendência": dados.get("tendencia", "Estável"),
                "Fonte": dados.get("fonte", "N/A")
            })
        
        df = pd.DataFrame(dados_tabela)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado de produto disponível para Metadados Pro.")
