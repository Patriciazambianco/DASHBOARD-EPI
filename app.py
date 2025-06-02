import streamlit as st
import pandas as pd
import io

# Função para exportar DataFrame para Excel e retornar bytes para download
def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

@st.cache_data
def carregar_dados():
    # Troque 'seus_dados.xlsx' pelo caminho do seu arquivo real
    df = pd.read_excel('seus_dados.xlsx')
    return df

def show():
    st.title("Dashboard de Inspeções EPI")

    df = carregar_dados()

    # Certifique-se que a coluna de datas está no formato datetime
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

    # Técnicos que já tiveram inspeção (última por técnico + produto)
    inspecionados = (
        df.dropna(subset=['DATA_INSPECAO'])  # só com data
          .sort_values('DATA_INSPECAO', ascending=False)
          .drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'])
    )

    # Técnicos que nunca tiveram inspeção — identificados via merge left_only
    merge = pd.merge(
        df[['IDTEL_TECNICO', 'TÉCNICO', 'PRODUTO_SIMILAR', 'COORDENADOR', 'GERENTE']].drop_duplicates(),
        inspecionados[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']],
        on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'],
        how='left',
        indicator=True
    )

    nunca_inspecionados = merge[merge['_merge'] == 'left_only'].drop(columns=['_merge'])

    # Exibe e exporta inspecionados
    st.header("Técnicos com Inspeção")
    st.dataframe(inspecionados)

    st.download_button(
        label="Exportar Inspecionados para Excel",
        data=exportar_excel(inspecionados),
        file_name="inspecionados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Exibe e exporta nunca inspecionados
    st.header("Técnicos Nunca Inspecionados")
    st.dataframe(nunca_inspecionados)

    st.download_button(
        label="Exportar Nunca Inspecionados para Excel",
        data=exportar_excel(nunca_inspecionados),
        file_name="nunca_inspecionados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == '__main__':
    show()

