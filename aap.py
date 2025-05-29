# app.py - só isso basta pra rodar no Streamlit Cloud

import streamlit as st
import pandas as pd
import plotly.express as px

st.title('Dashboard EPI - Upload e gráficos')

uploaded_file = st.file_uploader("📁 Envie seu arquivo Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    st.write(df.head())

    # Exemplo de gráfico
    fig = px.bar(df, x=df.columns[0], y=df.columns[1])
    st.plotly_chart(fig)
else:
    st.write("Envie um arquivo para começar.")
