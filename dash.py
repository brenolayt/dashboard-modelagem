import pandas as pd
import oracledb
import streamlit as st
import plotly.express as px
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(layout="wide")
conn = oracledb.connect(user="C##TRABALHO", password="brenodba", dsn="localhost:1521/XE")

st.sidebar.title("📊 Menu de Visualização")
opcao = st.sidebar.selectbox(
    "Escolha:",
    ("Peso por material e dia", "Reciclagem por Cidade", "Vendas dos Beneficios")
)

if opcao == "Peso por material e dia":
    df = pd.read_sql("""
    SELECT *
    FROM(
        SELECT TIPO, PESO_KG AS KG, TO_CHAR(DATA_HORA, 'DY') AS DIA FROM MATERIAIS
        JOIN RECICLAGEM_MATERIAL USING(ID_MATERIAL)
        JOIN RECICLAGENS USING(ID_RECICLAGEM)
    )
    PIVOT (
        SUM(KG)
        FOR DIA IN (
            'MON' AS SEGUNDA,
            'TUE' AS TERCA,
            'WED' AS QUARTA,
            'THU' AS QUINTA,
            'FRI' AS SEXTA,
            'SAT' AS SABADO,
            'SUN' AS DOMINGO
        )
    )
    """, conn)
    df_melt = df.melt(id_vars='TIPO', var_name='DIA', value_name='PESO_KG')

    fig = px.bar(
        df_melt,
        x='DIA',
        y='PESO_KG',
        color='TIPO',
        barmode='group',
        title='Peso Reciclado por Material e Dia da Semana',
        labels={
            "PESO_KG" : "PESO (KG)"
        }
    )

    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(
        df_melt,
        x='DIA',
        y='PESO_KG',
        color='TIPO',
        markers=True,
        title='Tendência Semanal de Reciclagem por Tipo de Material',
        labels={
            "PESO_KG" : "PESO (KG)"
        }
    )

    st.plotly_chart(fig, use_container_width=True)

    st.write(df)


elif opcao == "Reciclagem por Cidade":
    df_cidade = pd.read_sql("""
        SELECT CIDADE, SUM(PESO_KG) AS QNT_KG
        FROM LOCALIZACOES
        JOIN CIDADES USING(ID_CIDADE)
        JOIN UNIDADE_FEDERATIVA USING(ID_UF)
        JOIN CONTAINERS USING(ID_LOCALIZACAO)
        JOIN RECICLAGENS USING(ID_CONTAINER)
        JOIN RECICLAGEM_MATERIAL USING(ID_RECICLAGEM)
        WHERE RECICLAGENS.STATUS = 'CONCLUIDA'
        GROUP BY CIDADE
        ORDER BY QNT_KG DESC
    """, conn)

    st.title("Reciclagem Total por Cidade")

    st.markdown("""
    Visualização comparativa da **quantidade total de material reciclado (em Kg)** 
    em cada cidade registrada no sistema.  
    Os gráficos abaixo mostram diferentes formas de interpretar os mesmos dados.
    """)

    cores_padrao = ['#5DADE2', '#F5B7B1', '#E74C3C', '#D98880', '#58D68D']

    fig_barh = px.bar(
        df_cidade.sort_values("QNT_KG", ascending=True),
        x="QNT_KG",
        y="CIDADE",
        orientation="h",
        title="Total de Reciclagem por Cidade (Barras Horizontais)",
        labels={"QNT_KG": "Quantidade (Kg)", "CIDADE": "Cidade"},
        text_auto=".2s",
        color="CIDADE",
        color_discrete_sequence=cores_padrao
    )
    fig_barh.update_layout(
        showlegend=False,
        height=450,
        plot_bgcolor="#111",
        paper_bgcolor="#111",
        font_color="white",
        xaxis_title="Quantidade (Kg)",
        yaxis_title="Cidade"
    )

    fig_barv = px.bar(
        df_cidade,
        x="CIDADE",
        y="QNT_KG",
        title="Total de Reciclagem por Cidade (Colunas Verticais)",
        labels={"QNT_KG": "Quantidade (Kg)", "CIDADE": "Cidade"},
        text_auto=".2s",
        color="CIDADE",
        color_discrete_sequence=cores_padrao
    )
    fig_barv.update_layout(
        showlegend=False,
        height=450,
        plot_bgcolor="#111",
        paper_bgcolor="#111",
        font_color="white",
        xaxis_title="Cidade",
        yaxis_title="Quantidade (Kg)"
    )

    fig_pie = px.pie(
        df_cidade,
        values="QNT_KG",
        names="CIDADE",
        title="Proporção de Reciclagem entre Cidades",
        hole=0.35,
        color_discrete_sequence=cores_padrao
    )
    fig_pie.update_traces(textinfo="percent+label", textposition="inside")
    fig_pie.update_layout(
        plot_bgcolor="#111",
        paper_bgcolor="#111",
        font_color="white"
    )

    col1, col2 = st.columns((1, 1))
    with col1:
        st.plotly_chart(fig_barh, use_container_width=True)
    with col2:
        st.plotly_chart(fig_barv, use_container_width=True)

    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("Tabela Resumo dos Dados")
    st.dataframe(
        df_cidade.style.format({"QNT_KG": "{:,.2f}"}),
        use_container_width=True
    )

elif opcao == "Vendas dos Beneficios":
    df_vendas = pd.read_sql("""
        SELECT 
        NOME AS EMPRESA,
        ITEM AS BENEFICIO,
        COUNT(ID_BENEFICIO) AS VENDAS
        FROM BENEFICIOS
        JOIN EMPRESAS USING(ID_EMPRESA)
        JOIN RESGATES USING(ID_BENEFICIO)
        GROUP BY NOME, ITEM
        ORDER BY NOME, VENDAS DESC
    """, conn)

    st.title("Vendas de Benefícios por Empresa")

    st.markdown("""
    Visualize o desempenho de vendas dos benefícios oferecidos por cada empresa.
    Use o filtro abaixo para selecionar uma empresa e analisar as métricas correspondentes.
    """)

    empresas = sorted(df_vendas["EMPRESA"].unique())
    empresa_selecionada = st.selectbox("Selecione uma empresa:", ["Todas"] + empresas)

    if empresa_selecionada != "Todas":
        df_filtrado = df_vendas[df_vendas["EMPRESA"] == empresa_selecionada]
    else:
        df_filtrado = df_vendas.copy()

    cores_padrao = ['#5DADE2', '#F5B7B1', '#E74C3C', '#D98880', '#58D68D']

    fig_bar = px.bar(
        df_filtrado,
        x="BENEFICIO",
        y="VENDAS",
        color="BENEFICIO",
        title=f"Quantidade de Vendas por Benefício {'(todas as empresas)' if empresa_selecionada=='Todas' else f'– {empresa_selecionada}'}",
        text_auto=True,
        color_discrete_sequence=cores_padrao
    )
    fig_bar.update_layout(
        xaxis_title="Benefício",
        yaxis_title="Vendas",
        showlegend=False,
        plot_bgcolor="#111",
        paper_bgcolor="#111",
        font_color="white"
    )

    fig_pie = px.pie(
        df_filtrado,
        values="VENDAS",
        names="BENEFICIO",
        title="Distribuição de Vendas por Benefício",
        hole=0.3,
        color_discrete_sequence=cores_padrao
    )
    fig_pie.update_traces(textinfo="percent+label", textposition="inside")
    fig_pie.update_layout(
        plot_bgcolor="#111",
        paper_bgcolor="#111",
        font_color="white"
    )

    fig_rank = px.bar(
        df_filtrado.sort_values("VENDAS", ascending=True),
        x="VENDAS",
        y="BENEFICIO",
        orientation="h",
        title="Ranking de Benefícios Mais Vendidos",
        color="BENEFICIO",
        text_auto=True,
        color_discrete_sequence=cores_padrao
    )
    fig_rank.update_layout(
        xaxis_title="Vendas",
        yaxis_title="Benefício",
        plot_bgcolor="#111",
        paper_bgcolor="#111",
        font_color="white",
        showlegend=False
    )

    col1, col2 = st.columns((1, 1))
    with col1:
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.plotly_chart(fig_pie, use_container_width=True)

    st.plotly_chart(fig_rank, use_container_width=True)

    st.markdown("Tabela de Vendas")
    st.dataframe(df_filtrado.style.format({"VENDAS": "{:,.0f}"}), use_container_width=True)