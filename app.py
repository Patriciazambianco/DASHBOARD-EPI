import pandas as pd
import streamlit as st
from io import BytesIO

@st.cache_data
def carregar_dados(uploaded_file):
    return pd.read_excel(uploaded_file)

def gerar_ultima_inspecao(df):
    # Só linhas com data de inspeção
    df_inspec = df[df['DATA_INSPECAO'].notnull()]
    # Ordena pra pegar a última
    df_inspec = df_inspec.sort_values(by='DATA_INSPECAO', ascending=False)
    # Remove duplicados (técnico + produto)
    return df_inspec.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'], keep='first')

def gerar_nunca_inspecionados(df):
    # Só linhas sem data de inspeção
    return df[df['DATA_INSPECAO'].isnull()]

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

    # Filtros
    gerentes = ['Todos'] + sorted(df['GERENTE'].dropna().unique())
    coordenadores = ['Todos'] + sorted(df['COORDENADOR'].dropna().unique())

    gerente_selecionado = st.selectbox("Filtrar por Gerente", gerentes)
    coordenador_selecionado = st.selectbox("Filtrar por Coordenador", coordenadores)

    # Aplica filtro no df original antes de gerar as tabelas
    df_filtrado = df.copy()

    if gerente_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['GERENTE'] == gerente_selecionado]

    if coordenador_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['COORDENADOR'] == coordenador_selecionado]

    # Agora gera as tabelas *com o df filtrado* — é aqui que eliminamos duplicatas
    ultimas = gerar_ultima_inspecao(df_filtrado)
    nunca = gerar_nunca_inspecionados(df_filtrado)

    # Métricas
    total_registros = len(df_filtrado)
    total_inspecionados = len(ultimas)
    total_pendentes = len(nunca)

    pct_inspecionados = (total_inspecionados / total_registros * 100) if total_registros else 0
    pct_pendentes = (total_pendentes / total_registros * 100) if total_registros else 0

    # Cards de resumo
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registros", total_registros)
    col2.metric("Inspecionados (%)", f"{pct_inspecionados:.1f}%")
    col3.metric("Pendentes (%)", f"{pct_pendentes:.1f}%")

    # Tabelas detalhadas
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
