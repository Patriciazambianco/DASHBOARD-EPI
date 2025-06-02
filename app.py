import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO

@st.cache_data
def carregar_dados(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    df.loc[df['DATA_INSPECAO'] == pd.Timestamp('2001-01-01'), 'DATA_INSPECAO'] = pd.NaT
    df['IDTEL_TECNICO'] = df['IDTEL_TECNICO'].astype(str).str.strip()
    df['PRODUTO_SIMILAR'] = df['PRODUTO_SIMILAR'].astype(str).str.strip().str.upper()
    return df

def consolidar_ultima_inspecao_ou_pendente(df):
    # Agrupa por Técnico + Produto e acha a data máxima (última inspeção) dentro do grupo
    ultima_data = df.groupby(['IDTEL_TECNICO', 'PRODUTO_SIMILAR'])['DATA_INSPECAO'].max().reset_index()

    # Agora juntamos essa última data com o df original para pegar todas as colunas daquela linha
    # Se a última data for NaT, vai tentar casar com linhas com DATA_INSPECAO NaT
    df_merged = pd.merge(df, ultima_data, on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'], how='inner')

    # Removemos duplicatas que podem surgir se houver várias linhas idênticas
    df_merged = df_merged.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'])

    return df_merged.reset_index(drop=True)

def exportar_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)
    output.seek(0)
    return output

st.set_page_config(page_title="Dashboard EPI", layout="wide")
st.title("📋 Dashboard de Inspeções de EPI")

uploaded_file = st.file_uploader("📂 Envie o arquivo Excel com os dados", type="xlsx")

if uploaded_file:
    df = carregar_dados(uploaded_file)

    colunas_necessarias = ['DATA_INSPECAO', 'IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'GERENTE', 'COORDENADOR']
    if not all(col in df.columns for col in colunas_necessarias):
        st.error("Arquivo enviado não possui as colunas necessárias.")
        st.stop()

    gerentes = ['Todos'] + sorted(df['GERENTE'].dropna().unique())
    coordenadores = ['Todos'] + sorted(df['COORDENADOR'].dropna().unique())

    gerente_selecionado = st.selectbox("Filtrar por Gerente", gerentes)
    coordenador_selecionado = st.selectbox("Filtrar por Coordenador", coordenadores)

    df_filtrado = df.copy()
    if gerente_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['GERENTE'] == gerente_selecionado]
    if coordenador_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['COORDENADOR'] == coordenador_selecionado]

    # Debug rápido pra conferir números:
    st.write(f"Linhas após filtro: {len(df_filtrado)}")
    st.write(f"Técnico + Produto únicos após filtro: {df_filtrado[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']].drop_duplicates().shape[0]}")

    df_resultado = consolidar_ultima_inspecao_ou_pendente(df_filtrado)

    total_registros = len(df_filtrado)
    total_unicos = df_filtrado[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']].drop_duplicates().shape[0]
    total_inspecionados = df_resultado['DATA_INSPECAO'].notna().sum()
    total_pendentes = df_resultado['DATA_INSPECAO'].isna().sum()

    # Total únicos é o total real de técnico+produto únicos
    # total_inspecionados + total_pendentes devem ser iguais a total_unicos
    st.write(f"Técnico + Produto únicos consolidados: {total_unicos}")
    st.write(f"Consolidados com inspeção: {total_inspecionados}")
    st.write(f"Consolidados pendentes: {total_pendentes}")
    st.write(f"Soma inspecionados + pendentes: {total_inspecionados + total_pendentes}")

    pct_inspecionados = (total_inspecionados / total_unicos * 100) if total_unicos else 0
    pct_pendentes = (total_pendentes / total_unicos * 100) if total_unicos else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registros (linhas no filtro)", total_registros)
    col2.metric("Técnico+Produto Únicos", total_unicos)
    col3.metric("Inspecionados (%)", f"{pct_inspecionados:.1f}%")
    col1.metric("Pendentes (%)", f"{pct_pendentes:.1f}%")

    fig = px.pie(
        names=["Inspecionados", "Pendentes"],
        values=[total_inspecionados, total_pendentes],
        color_discrete_sequence=["#4CAF50", "#FF6F61"],
        title="📊 Distribuição de Inspeções"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("✅ Última Inspeção ou Pendentes por Técnico + Produto")
    st.dataframe(df_resultado)

    output_excel = exportar_excel({'Resultado': df_resultado})

    st.download_button(
        label="⬇️ Baixar Excel com Resultados",
        data=output_excel,
        file_name="inspecoes_epi_resultado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
