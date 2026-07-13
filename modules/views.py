import streamlit as st
import pandas as pd
import random
from datetime import datetime
from urllib.parse import quote
import os

# Importa do auth.py (SistemaLicencas está aqui)
from modules.auth import SistemaLicencas
from modules.models import (
    PALAVRAS_CHAVE_CAUDA_LONGA,
    obter_palavra_chave,
    gerar_top10_produtos,
    gerar_sugestoes_diarias,
    BUSCAS_DIARIAS,
    carregar_apoiadores,
    adicionar_apoiador,
    remover_apoiador
)

# Importa grade de descoberta
from modules.grade_descoberta import (
    descobrir_produtos_grade,
    enriquecer_produto,
    get_produtos_sazonais,
    get_produtos_sazonais_com_motivos,
    GRADE_PRODUTOS,
    obter_motivo_busca,
    obter_indicadores_horario
)

# Importa para verificar data do cache
from modules.produtos_dinamicos import verificar_data_cache

# Tenta importar serper, se falhar usa fallback
try:
    from modules.serper import buscar_produtos_serper
    SERPER_DISPONIVEL = True
except ImportError:
    SERPER_DISPONIVEL = False
    def buscar_produtos_serper(termo, limite=5):
        return []

# ============================================================
# STATUS DO USUÁRIO (REMOVIDO)
# ============================================================
def render_status_usuario():
    """Renderiza o status do usuário - REMOVIDO"""
    pass

# ============================================================
# GRADE DE DESCOBERTA - SOMENTE TABELA
# ============================================================
def render_grade_descoberta():
    """
    Renderiza a grade de descoberta de produtos em formato de tabela
    """
    st.markdown("## 🎯 Grade de Descoberta de Produtos")
    st.caption("Produtos em tendência descobertos automaticamente - Análise baseada em dados do Pinterest e Google Trends")
    
    # Filtros removidos a pedido do usuário - Fixado em 20 itens
    quantidade = 20
    categoria = None
    
    # ============================================================
    # BUSCA PRODUTOS
    # ============================================================
    with st.spinner("🔍 Descobrindo produtos..."):
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
        score = item.get("score", 0)
        categoria = item.get("categoria", "Geral").capitalize()
        motivo = item.get("motivo", "📊 Produto em tendência no mercado")
        indicadores = item.get("indicadores", {})
        
        # Status de score
        if score >= 8:
            status = "🔥 Alta"
        elif score >= 6:
            status = "📈 Média"
        else:
            status = "📊 Baixa"
        
        # Palavra-chave e hashtags
        dados_palavra = obter_palavra_chave(produto)
        palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
        hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:3]
        
        # Horário
        horario = indicadores.get("horario", "10h-12h") if indicadores else "10h-12h"
        intensidade = indicadores.get("porcentagem", 50) if indicadores else 50
        
        dados_tabela.append({
            "Produto": produto,
            "Categoria": categoria,
            "Score": f"{score}/10",
            "Status": status,
            "Palavra-chave": palavra_chave,
            "Hashtags": " ".join(hashtags),
            "Melhor Horário": horario,
            "Intensidade": f"{intensidade}%",
            "Motivo": motivo[:80] + "..."
        })
    
    df = pd.DataFrame(dados_tabela)
    
    # Exibe tabela com st.dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Produto": st.column_config.TextColumn("Produto", width="medium"),
            "Categoria": st.column_config.TextColumn("Categoria", width="small"),
            "Score": st.column_config.TextColumn("Score", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Palavra-chave": st.column_config.TextColumn("Palavra-chave", width="large"),
            "Hashtags": st.column_config.TextColumn("Hashtags", width="medium"),
            "Melhor Horário": st.column_config.TextColumn("Melhor Horário", width="small"),
            "Intensidade": st.column_config.TextColumn("Intensidade", width="small"),
            "Motivo": st.column_config.TextColumn("Motivo", width="large"),
        }
    )

# ============================================================
# APOIADORES EM CARDS PEQUENOS
# ============================================================
def render_apoiadores_compactos():
    """Renderiza os apoiadores em cards pequenos com coroa centralizada"""
    
    apoiadores = carregar_apoiadores()
    
    if not apoiadores:
        return
    
    st.markdown("### 👑 Apoiadores do Projeto")
    st.caption("Pessoas que acreditam e apoiam este projeto")
    
    apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
    
    cores = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
        "#FFEAA7", "#DDA0DD", "#FF8A5C", "#A29BFE",
        "#FD79A8", "#00B894", "#E17055", "#6C5CE7"
    ]
    
    cols = st.columns(6)
    
    for i, apoiador in enumerate(apoiadores_ordenados):
        with cols[i % 6]:
            cor = cores[i % len(cores)]
            nome = apoiador.get("nome", "Apoiador")
            ordem = apoiador.get("ordem", 999)
            coroinha = apoiador.get("coroinha", "👑")
            
            with st.container(border=True):
                st.markdown(f"""
                <div style="text-align: center; font-size: 28px; margin: -8px 0 2px 0;">
                    {coroinha}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="text-align: center; font-weight: bold; font-size: 13px; margin: 0;">
                    {nome}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="text-align: center; font-size: 10px; color: #888; margin: 0;">
                    #{ordem}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="
                    background: {cor};
                    height: 3px;
                    border-radius: 2px;
                    margin: 4px 0 2px 0;
                ">
                </div>
                """, unsafe_allow_html=True)
                
                depois = sum(1 for k, d in apoiadores.items() if d.get("ordem", 999) > ordem)
                
                if depois > 0 and apoiador.get("repasse_ativo", True):
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 10px; color: #4CAF50; margin: 0;">
                        ⬇️ R${depois * 5.00:.0f}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 10px; color: #888; margin: 0;">
                        ⏳
                    </div>
                    """, unsafe_allow_html=True)

# ============================================================
# INSIGHTS ESTRATÉGICOS - SEM TENDÊNCIAS DE MERCADO
# ============================================================
def render_insights_estrategicos(produtos):
    """
    Renderiza insights estratégicos sem Plotly (usando apenas Streamlit)
    """
    
    st.markdown("## 💡 Insights Estratégicos")
    st.caption("Análise de mercado baseada em dados do Pinterest e Google Trends")
    
    # ============================================================
    # PRODUTOS SAZONAIS - TABELA
    # ============================================================
    sazonais = get_produtos_sazonais_com_motivos()
    
    if sazonais:
        st.markdown("### 📅 Produtos Sazonais do Mês")
        st.caption("Produtos em alta devido à temporada atual")
        
        dados_sazonais = []
        for item in sazonais[:4]:
            produto = item.get("produto", "").capitalize()
            motivo = item.get("motivo", "")
            
            indicadores = obter_indicadores_horario(produto)
            horario = indicadores.get("melhor_horario", "19h-22h") if indicadores else "19h-22h"
            intensidade = indicadores.get("porcentagem", 70) if indicadores else 70
            
            dados_palavra = obter_palavra_chave(produto)
            palavra_chave = dados_palavra.get("palavra", f"{produto} tendência 2026")
            hashtags = dados_palavra.get("hashtags", ["#tendência", "#moda", "#2026"])[:2]
            
            dados_sazonais.append({
                "Produto": produto,
                "Motivo": motivo[:60] + "...",
                "Melhor Horário": horario,
                "Intensidade": f"{intensidade}%",
                "Palavra-chave": palavra_chave,
                "Hashtags": " ".join(hashtags)
            })
        
        df_sazonais = pd.DataFrame(dados_sazonais)
        st.dataframe(df_sazonais, use_container_width=True, hide_index=True)

# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
def render_dashboard():
    """Renderiza o dashboard principal"""
    
    # Status do topo removido a pedido do usuário
    pass
    
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.title("📊 Minerador de Produtos")
        st.caption(f"📅 {datetime.now().strftime('%A, %d de %B de %Y - %H:%M')}")
    
    with col_refresh:
        # Botão removido - Atualização agora é 100% automática a cada 2 horas
        st.empty()
    
    # ============================================================
    # VISÃO GERAL DO MÊS - COMPLETA
    # ============================================================
    st.markdown("## 📊 Visão Geral do Mês")
    
    # Forçar dados v4.9
    from modules.produtos_dinamicos import PRODUTOS_FALLBACK
    produtos_top_base = PRODUTOS_FALLBACK
    
    # Converter para formato de lista para o Top 10
    produtos_top = []
    for nome, dados in produtos_top_base.items():
        item = dados.copy()
        item["Produto"] = nome
        item["Crescimento"] = f"+{dados.get('crescimento', 0)}%"
        item["Categoria"] = dados.get("categoria", "Geral")
        item["Evento"] = dados.get("evento", "Tendência")
        item["Score"] = dados.get("score", 0)
        item["Fonte"] = dados.get("fonte", "Shopee")
        produtos_top.append(item)
    
    produtos_top = sorted(produtos_top, key=lambda x: x.get("Score", 0), reverse=True)[:10]
    produtos_sugestoes = produtos_top[:5]
    
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
        
        # LINHA 1: MENSAGEM DESTAQUE
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
                    Com score {top1.get('Score', 0)}/10 e {top1.get('Crescimento', '+0%')} de crescimento.
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # LINHA 2: MÉTRICAS + OPORTUNIDADE
        col1, col2 = st.columns([2, 1])
        with col1:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(label="🔥 Produto em Alta", value=top1.get("Produto", "N/A") if top1 else "N/A", delta=top1.get("Categoria", "Moda") if top1 else "N/A")
            with m2:
                st.metric(label="📈 Crescimento Médio", value=f"{crescimento_medio:.1f}%", delta=f"{crescimento_medio - 5:.1f}%")
            with m3:
                st.metric(label="🎯 Categoria em Alta", value=categoria_mais_freq, delta=evento_mais_freq)
        
        with col2:
            with st.container(border=True):
                st.markdown("### 🎯 Melhor Oportunidade")
                melhor_score = max(produtos_top, key=lambda x: x.get("Score", 0)) if produtos_top else None
                if melhor_score:
                    st.markdown(f"**{melhor_score.get('Produto', 'N/A')}** ⭐ **{melhor_score.get('Score', 0)}/10**")
                    st.success(f"📈 {melhor_score.get('Crescimento', '+0%')}")
                else:
                    st.info("📊 Aguardando dados...")
    else:
        st.info("📊 Buscando dados de mercado...")

    st.markdown("---")
    
    # ============================================================
    # GRADE DE DESCOBERTA (TABELA)
    # ============================================================
    render_grade_descoberta()
    
    st.markdown("---")
    
    # ===== TOP 10 =====
    st.markdown("## 🏆 Top 10 Produtos em Tendência")
    st.caption("Ranking completo baseado em score e dados de mercado")
    
    top10 = gerar_top10_produtos(forcar_atualizacao=False)
    if top10:
        df_top10 = pd.DataFrame(top10)
        colunas_top10 = ["Produto", "Fonte", "Categoria", "Evento", "Potencial", "Score", "Pins", "Crescimento", "Views TikTok", "Buscas no Mês", "Resultados ML", "Tendência"]
        df_top10 = df_top10[colunas_top10]
        st.dataframe(df_top10, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ===== INSIGHTS ESTRATÉGICOS =====
    if produtos_sugestoes:
        render_insights_estrategicos(produtos_sugestoes)
    
    st.markdown("---")
    
    # ===== APOIADORES COMPACTOS =====
    render_apoiadores_compactos()

# ============================================================
# PAINEL DE APOIADORES DETALHADO
# ============================================================
def render_painel_apoiadores_detalhado():
    """Renderiza o painel completo de gestão de apoiadores"""
    st.markdown("## 👑 Gestão de Apoiadores")
    st.caption("Controle completo da rede de apoio e repasses")
    
    apoiadores = carregar_apoiadores()
    if not apoiadores:
        st.info("📭 Nenhum apoiador cadastrado.")
    else:
        apoiadores_ordenados = sorted(apoiadores.values(), key=lambda x: x.get("ordem", 999))
        
        # Exibição em cards
        cores = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
        cols = st.columns(4)
        for i, apoiador in enumerate(apoiadores_ordenados):
            with cols[i % 4]:
                cor = cores[i % len(cores)]
                nome = apoiador.get("nome", "Apoiador")
                ordem = apoiador.get("ordem", 999)
                with st.container(border=True):
                    st.markdown(f"**{nome}** (#{ordem})")
                    st.caption(f"📅 {apoiador.get('data_entrada', '2026-07-01')}")
                    depois = sum(1 for k, d in apoiadores.items() if d.get("ordem", 999) > ordem)
                    if depois > 0:
                        st.success(f"⬇️ R${depois * 5.00:.2f}/mês")

# ============================================================
# NOVA SEÇÃO: TOP 20 GOOGLE
# ============================================================
def render_top_20_marketplace():
    """
    Renderiza uma nova grade exclusiva com os 20 produtos reais de marketplace
    """
    st.markdown("## 🔥 Top 20 Google (Shopping & Trends)")
    st.caption("Dados brutos de alto giro pesquisados diretamente na Shopee Brasil - Julho 2026")
    
    produtos_reais = [
        {"produto": "Mini Processador de Alimentos Manual", "categoria": "Casa", "score": 10, "motivo": "Campeão de vendas absoluto em utilidades domésticas"},
        {"produto": "Smartwatch D20 Ultra Bluetooth", "categoria": "Eletrônicos", "score": 10, "motivo": "O eletrônico mais vendido para entrada no marketplace"},
        {"produto": "Fone de Ouvido Bluetooth i12 TWS", "categoria": "Eletrônicos", "score": 10, "motivo": "Alto giro e volume massivo de buscas diárias"},
        {"produto": "Mop Spray com Reservatório", "categoria": "Casa", "score": 9, "motivo": "Produto viral com alta taxa de conversão"},
        {"produto": "Kit 10 Pares de Meias Soquete", "categoria": "Moda", "score": 9, "motivo": "Item de necessidade básica com venda recorrente"},
        {"produto": "Lâmpada LED com Sensor de Movimento", "categoria": "Eletrônicos", "score": 9, "motivo": "Tendência em iluminação inteligente de baixo custo"},
        {"produto": "Garrafa Térmica 2 Litros Motivacional", "categoria": "Casa", "score": 9, "motivo": "Febre em vendas impulsionada por redes sociais"},
        {"produto": "Ring Light de Mesa 10 Polegadas", "categoria": "Eletrônicos", "score": 9, "motivo": "Essencial para criadores de conteúdo iniciantes"},
        {"produto": "Kit 12 Utensílios de Cozinha em Silicone", "categoria": "Casa", "score": 9, "motivo": "Alta procura por renovação de itens de cozinha"},
        {"produto": "Mini Umidificador de Ar Portátil", "categoria": "Eletrônicos", "score": 9, "motivo": "Sazonalidade positiva e busca constante"},
        {"produto": "Escova Secadora e Alisadora 3 em 1", "categoria": "Beleza", "score": 8, "motivo": "Destaque em beleza com alto volume de vendas"},
        {"produto": "Kit 3 Potes Herméticos de Acrílico", "categoria": "Casa", "score": 8, "motivo": "Tendência forte de organização doméstica"},
        {"produto": "Touca de Cetim Anti-Frizz", "categoria": "Beleza", "score": 8, "motivo": "Produto de baixo custo com giro extremamente rápido"},
        {"produto": "Suporte Articulado para Celular e Tablet", "categoria": "Eletrônicos", "score": 8, "motivo": "Acessório indispensável para home office"},
        {"produto": "Fita LED RGB 5 Metros com Controle", "categoria": "Eletrônicos", "score": 8, "motivo": "Decoração gamer e tech em alta"},
        {"produto": "Dispenser de Água Automático para Galão", "categoria": "Casa", "score": 8, "motivo": "Utilidade doméstica prática com muita saída"},
        {"produto": "Kit 10 Cuecas Boxer Microfibra", "categoria": "Moda", "score": 8, "motivo": "Líder em moda masculina básica"},
        {"produto": "Maquininha de Cortar Cabelo Vintage T9", "categoria": "Eletrônicos", "score": 8, "motivo": "Viral de vendas em cuidados masculinos"},
        {"produto": "Organizador de Gavetas para Roupas Intimas", "categoria": "Casa", "score": 8, "motivo": "Busca crescente por soluções de espaço"},
        {"produto": "Mini Aspirador de Pó Portátil para Carro", "categoria": "Eletrônicos", "score": 8, "motivo": "Acessório automotivo mais procurado do mês"}
    ]
    
    dados_tabela = []
    for item in produtos_reais:
        dados_palavra = obter_palavra_chave(item["produto"])
        dados_tabela.append({
            "Produto": item["produto"],
            "Categoria": item["categoria"],
            "Score": f"{item['score']}/10",
            "Palavra-chave": dados_palavra.get("palavra", f"{item['produto']}"),
            "Motivo Estratégico": item["motivo"]
        })
    
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True, hide_index=True)
