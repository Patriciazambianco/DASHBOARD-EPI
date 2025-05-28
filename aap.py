import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de EPIs", layout="wide")

st.title("Dashboard de EPIs")

uploaded_file = st.file_uploader("📁 Envie seu arquivo Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")

    # Exemplo de status fictício (você pode adaptar com base no seu merge real)
    df["Status"] = df["DATA_INSPECAO"].apply(lambda x: "OK" if pd.notna(x) and pd.Timestamp.now() - x <= pd.Timedelta(days=180) else "Pendente")

    pendencias = df.groupby("COORDENADOR_IMEDIATO")["Status"].value_counts().unstack().fillna(0)

    st.subheader("📊 Pendências por Coordenador")
    st.bar_chart(pendencias)

    gerente = df.groupby("GERENTE_IMEDIATO")["Status"].value_counts().unstack().fillna(0)
    st.subheader("📊 Pendências por Gerente")
    st.bar_chart(gerente)
