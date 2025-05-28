import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Dashboard Simples de Inspeções")

uploaded_file = st.file_uploader("📁 Envie seu arquivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    
    st.write("### Visualização dos dados")
    st.dataframe(df.head())

    # Exemplo de gráfico: quantidade de registros por coordenador
    if 'COORDENADOR_IMEDIATO' in df.columns and 'SITUACAO' in df.columns:
        resumo = df.groupby(['COORDENADOR_IMEDIATO', 'SITUACAO']).size().reset_index(name='quantidade')
        fig = px.bar(resumo, x='COORDENADOR_IMEDIATO', y='quantidade', color='SITUACAO',
                     title='Pendências e OK por Coordenador')
        st.plotly_chart(fig)
    else:
        st.warning("As colunas 'COORDENADOR_IMEDIATO' ou 'SITUACAO' não foram encontradas no arquivo.")
else:
    st.info("Por favor, envie um arquivo Excel para começar.")

