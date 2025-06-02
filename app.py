import streamlit as st
import pandas as pd
import io

def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

def show():
    st.title("Dashboard de Inspeções EPI - Sem Duplicatas")

    uploaded_file = st.file_uploader("Faça upload do arquivo Excel", type=['xlsx'])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

        # Filtra só quem tem data (já foi inspecionado), ordena para pegar a última
        inspecionados = (
            df.dropna(subset=['DATA_INSPECAO'])
              .sort_values('DATA_INSPECAO', ascending=False)
              .drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'])
              .reset_index(drop=True)
        )

        # Tabela só com técnicos e produtos únicos
        tecnicos_produtos = (
            df[['IDTEL_TECNICO', 'TÉCNICO', 'PRODUTO_SIMILAR', 'COORDENADOR', 'GERENTE']]
            .drop_duplicates()
        )

        # Merge para achar os que NUNCA tiveram inspeção
        nunca_inspecionados = tecnicos_produtos.merge(
            inspecionados[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']],
            on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'],
            how='left',
            indicator=True
        )

        nunca_inspecionados = nunca_inspecionados[ 
            nunca_inspecionados['_merge'] == 'left_only'
        ].drop(columns=['_merge']).reset_index(drop=True)

        # Exibe e exporta
        st.header("Técnicos que já realizaram inspeção")
        st.dataframe(inspecionados)

        st.download_button(
            label="Exportar Inspecionados",
            data=exportar_excel(inspecionados),
            file_name="inspecionados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.header("Técnicos que nunca realizaram inspeção")
        st.dataframe(nunca_inspecionados)

        st.download_button(
            label="Exportar Nunca Inspecionados",
            data=exportar_excel(nunca_inspecionados),
            file_name="nunca_inspecionados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Faça upload do arquivo Excel para continuar.")

if __name__ == '__main__':
    show()
