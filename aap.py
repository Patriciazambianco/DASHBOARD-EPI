# app.py - Pronto para rodar no Streamlit Cloud

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard EPI", layout="wide")

st.title("🛡️ Relatório de EPI - Painel Interativo")

# Upload de arquivo
uploaded_file = st.file_uploader("📁 Envie seu arquivo CSV com os dados de EPI", type=["csv"])

if uploaded_file:
    # Leitura e tratamento
    df = pd.read_csv(uploaded_file)
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

    st.subheader("📊 Dados Originais")
    st.dataframe(df)

    # Última inspeção por técnico e produto
    df = df.sort_values(['TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'], ascending=[True, True, False])
    df_unique = df.drop_duplicates(subset=['TECNICO', 'PRODUTO_SIMILAR'], keep='first')

    # Define status: OK ou PENDENTE (>180 dias ou sem inspeção)
    hoje = pd.Timestamp.today()
    df_unique['STATUS'] = df_unique['DATA_INSPECAO'].apply(
        lambda x: 'PENDENTE' if pd.isna(x) or (hoje - x).days > 180 else 'OK'
    )

    # 🎛️ Filtros
    st.sidebar.header("🔎 Filtros")
    gerente = st.sidebar.selectbox("Filtrar por Gerente", options=["Todos"] + sorted(df_unique['GERENTE_IMEDIATO'].dropna().unique()))
    coordenador = st.sidebar.selectbox("Filtrar por Coordenador", options=["Todos"] + sorted(df_unique['COORDENADOR_IMEDIATO'].dropna().unique()))

    if gerente != "Todos":
        df_unique = df_unique[df_unique['GERENTE_IMEDIATO'] == gerente]
    if coordenador != "Todos":
        df_unique = df_unique[df_unique['COORDENADOR_IMEDIATO'] == coordenador]

    # KPIs
    total_registros = df_unique.shape[0]
    total_ok = df_unique[df_unique['STATUS'] == 'OK'].shape[0]
    total_pendente = total_registros - total_ok
    pct_ok = (total_ok / total_registros * 100) if total_registros > 0 else 0

    st.subheader("✅ Visão Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Registros", total_registros)
    col2.metric("Com EPI OK", total_ok)
    col3.metric("Pendentes", total_pendente)

    st.progress(pct_ok / 100)

    # Gráfico de situação
    status_count = df_unique['STATUS'].value_counts().reset_index()
    fig_status = px.pie(status_count, names='index', values='STATUS', title='Distribuição de Situação EPI')
    st.plotly_chart(fig_status, use_container_width=True)

    # Ranking por coordenador
    st.subheader("🏆 Registros por Coordenador")
    coord_count = df_unique['COORDENADOR_IMEDIATO'].value_counts().reset_index()
    coord_count.columns = ['COORDENADOR', 'QTD']
    fig_coord = px.bar(coord_count, x='COORDENADOR', y='QTD', title='Quantidade por Coordenador')
    st.plotly_chart(fig_coord, use_container_width=True)

    # Visualização dos dados finais
    with st.expander("📋 Visualizar dados filtrados"):
        st.dataframe(df_unique)

else:
    st.info("👆 Envie um arquivo CSV para visualizar o painel.")


