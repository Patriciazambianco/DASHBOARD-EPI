import streamlit as st
import pandas as pd
import io

def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

def show():
    st.title("Dashboard de Inspeções EPI")

    uploaded_file = st.file_uploader("Faça upload do arquivo Excel", type=['xlsx'])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

        inspecionados = (
            df.dropna(subset=['DATA_INSPECAO'])
              .sort_values('DATA_INSPECAO', ascending=False)
              .drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'])
        )

        merge = pd.merge(
            df[['IDTEL_TECNICO', 'TÉCNICO', 'PRODUTO_SIMILAR', 'COORDENADOR', 'GERENTE']].drop_duplicates(),
            inspecionados[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']],
            on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'],
            how='left',
            indicator=True
        )

        nunca_inspecionados = merge[merge['_merge'] == 'left_only'].drop(columns=['_merge'])

        st.header("Técnicos com Inspeção")
        st.dataframe(inspecionados)
        st.download_button(
            label="Exportar Inspecionados para Excel",
            data=exportar_excel(inspecionados),
            file_name="inspecionados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.header("Técnicos Nunca Inspecionados")
        st.dataframe(nunca_inspecionados)
        st.download_button(
            label="Exportar Nunca Inspecionados para Excel",
            data=exportar_excel(nunca_inspecionados),
            file_name="nunca_inspecionados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Por favor, faça upload do arquivo Excel para continuar.")

if __name__ == '__main__':
    show()
