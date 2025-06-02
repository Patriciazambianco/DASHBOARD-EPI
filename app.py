import pandas as pd
import streamlit as st
from io import BytesIO

@st.cache_data
def carregar_dados(uploaded_file):
    return pd.read_excel(uploaded_file)

def gerar_ultima_inspecao(df):
    df = df[df['DATA_INSPECAO'].notnull()]
    df = df.sort_values(by='DATA_INSPECAO', ascending=False)
    return df.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'], keep='first')

def gerar_nunca_inspecionados(df_total, df_inspecionados):
    merge = pd.merge(df_total, df_inspecionados[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']],
                     on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'], how='left', indicator=True)
    return merge[merge['_merge'] == 'left_only'].drop(columns=['_merge'])

def exportar_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)
    output.seek(0)
    return output

# STREAMLIT
st.set_page_config(page_title="Dashboard EPI", layout="wide")
st.title("📋 Dashboard de Inspeções de EPI")

uploaded_file = st.file_uploader("📂 Envie o arquivo Excel com os dados", type="xlsx")

if uploaded_file:
    df = carregar_dados(uploaded_file)

    st.subheader("👀 Prévia dos Dados")
    st.dataframe(df.head())

    # Lógicas principais
    ultimas = gerar_ultima_inspecao(df)
    nunca = gerar_nunca_inspecionados(df, ultimas)

    st.subheader("✅ Última Inspeção por Técnico + Produto")
    st.dataframe(ultimas)

    st.subheader("⚠️ Técnicos que Nunca Foram Inspecionados")
    st.dataframe(nunca)

    # Exportação
    output_excel = exportar_excel({'Ultima_Inspecao': ultimas, 'Nunca_Inspecionados': nunca})

    st.download_button(
        label="⬇️ Baixar Excel com Resultados",
        data=output_excel,
        file_name="inspecoes_epi_resultado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
