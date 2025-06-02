import streamlit as st
import pandas as pd
import io

def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

def show():
    st.title("Dashboard Inspeções EPI - Limpeza e Filtragem Profissa")

    uploaded_file = st.file_uploader("Envie seu arquivo Excel com os dados", type=['xlsx'])
    if uploaded_file is None:
        st.info("Por favor, faça upload do arquivo para continuar.")
        return

    # Leitura do arquivo
    df = pd.read_excel(uploaded_file)

    # Limpeza geral dos dados para evitar duplicações bobas
    cols_string = ['IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'TÉCNICO', 'COORDENADOR', 'GERENTE']
    for col in cols_string:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Converter datas, erros vira NaT
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

    # Debug: mostrar linhas totais
    st.write(f"Linhas totais no arquivo: {len(df)}")

    # Pegar a última inspeção por Técnico + Produto
    inspecionados = (
        df.dropna(subset=['DATA_INSPECAO'])  # só quem tem data
          .sort_values('DATA_INSPECAO', ascending=False)
          .drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'])
          .reset_index(drop=True)
    )
    st.write(f"Técnicos + Produtos com inspeção: {len(inspecionados)}")

    # Lista única de Técnico + Produto (com info de gerente/coordenador)
    tecnicos_produtos = (
        df[['IDTEL_TECNICO', 'TÉCNICO', 'PRODUTO_SIMILAR', 'COORDENADOR', 'GERENTE']]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    st.write(f"Técnicos + Produtos totais (sem filtro): {len(tecnicos_produtos)}")

    # Merge para encontrar quem nunca inspecionou (join anti)
    nunca_inspecionados = tecnicos_produtos.merge(
        inspecionados[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']],
        on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'],
        how='left',
        indicator=True
    )
    nunca_inspecionados = nunca_inspecionados[
        nunca_inspecionados['_merge'] == 'left_only'
    ].drop(columns=['_merge']).reset_index(drop=True)
    st.write(f"Técnicos + Produtos que nunca tiveram inspeção: {len(nunca_inspecionados)}")

    # Mostrar tabelas para conferência
    st.header("Última inspeção por Técnico e Produto")
    st.dataframe(inspecionados)

    st.header("Técnicos e Produtos sem nenhuma inspeção")
    st.dataframe(nunca_inspecionados)

    # Botões para exportar arquivos Excel
    st.download_button(
        "Exportar Inspecionados",
        data=exportar_excel(inspecionados),
        file_name="inspecionados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.download_button(
        "Exportar Nunca Inspecionados",
        data=exportar_excel(nunca_inspecionados),
        file_name="nunca_inspecionados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    show()
