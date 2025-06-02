import pandas as pd
import streamlit as st
from io import BytesIO

@st.cache_data
def carregar_dados(uploaded_file):
    return pd.read_excel(uploaded_file)

def gerar_ultima_inspecao(df):
    df_inspec = df[df['DATA_INSPECAO'].notnull()]
    df_inspec = df_inspec.sort_values(by='DATA_INSPECAO', ascending=False)
    return df_inspec.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'], keep='first')

def gerar_nunca_inspecionados(df):
    return df[df['DATA_INSPECAO'].isnull()]

def exportar_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)
    output.seek(0)
    return output

# --- Streamlit ---
st.set_page_config(page_title="Dashboard EPI", layout="wide")
st.title("📋 Dashboard de Inspeções de EPI")

uploaded_file = st.file_uploader("📂 Envie o arquivo Excel com os dados", type="xlsx")

if uploaded_file:
    df = carregar_dados(uploaded_file)

    # Filtros de gerente e coordenador
    gerentes = ['Todos'] + sorted(df['GERENTE'].dropna().unique().tolist())
    coordenadores = ['Todos'] + sorted(df['COORDENADOR'].dropna().unique().tolist())

    gerente_selecionado = st.selectbox("Filtrar por Gerente", gerentes)
    if gerente_selecionado != 'Todos':
        df = df[df['GERENTE'] == gerente_selecionado]

    coordenador_selecionado = st.selectbox("Filtrar por Coordenador", coordenadores)
    if coordenador_selecionado != 'Todos':
        df = df[df['COORDENADOR'] == coordenador_selecionado]

    # Processa os dados filtrados
    ultimas = gerar_ultima_inspecao(df)
    nunca = gerar_nunca_inspecionados(df)

    total_registros = len(df)
    total_inspecionados = len(ultimas)
    total_pendentes = len(nunca)

    pct_inspecionados = (total_inspecionados / total_registros) * 100 if total_registros > 0 else 0
    pct_pendentes = (total_pendentes / total_registros) * 100 if total_registros > 0 else 0

    # Exibe os cards resumidos
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registros", total_registros)
    col2.metric("Inspecionados (%)", f"{pct_inspecionados:.1f}%")
    col3.metric("Pendentes (%)", f"{pct_pendentes:.1f}%")

    # Tabelas detalhadas
    st.subheader("✅ Última Inspeção por Técnico + Produto")
    st.dataframe(ultimas)

    st.subheader("⚠️ Técnicos que Nunca Foram Inspecionados")
    st.dataframe(nunca)

    # Botão para exportar
    output_excel = exportar_excel({'Ultima_Inspecao': ultimas, 'Nunca_Inspecionados': nunca})

    st.download_button(
        label="⬇️ Baixar Excel com Resultados",
        data=output_excel,
        file_name="inspecoes_epi_resultado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
