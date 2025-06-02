import streamlit as st
import pandas as pd
import io

def color_badge(status):
    colors = {
        'OK': 'background-color: #4CAF50; color: white; font-weight: bold;',
        'Pendente': 'background-color: #FF9800; color: white; font-weight: bold;',
        'Reprovado': 'background-color: #F44336; color: white; font-weight: bold;',
        'Em Análise': 'background-color: #2196F3; color: white; font-weight: bold;',
    }
    return colors.get(status, '')

def style_badges(df):
    return df.style.applymap(lambda v: color_badge(v), subset=['STATUS CHECK LIST'])

def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
        writer.save()
    return output.getvalue()

def show():
    st.title("Dashboard EPI - Técnicos Inspecionados e Nunca Inspecionados")

    uploaded_file = st.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])
    if not uploaded_file:
        st.info("Por favor, faça upload do arquivo Excel para continuar.")
        return

    df = pd.read_excel(uploaded_file)
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

    # Filtros dinâmicos
    gerentes = df['GERENTE'].dropna().unique()
    gerente_sel = st.multiselect("Selecione Gerente(s)", options=gerentes, default=gerentes)

    df = df[df['GERENTE'].isin(gerente_sel)]

    coordenadores = df['COORDENADOR'].dropna().unique()
    coord_sel = st.multiselect("Selecione Coordenador(es)", options=coordenadores, default=coordenadores)

    df = df[df['COORDENADOR'].isin(coord_sel)]

    supervisores = df['SUPERVISOR'].dropna().unique()
    sup_sel = st.multiselect("Selecione Supervisor(es)", options=supervisores, default=supervisores)

    df = df[df['SUPERVISOR'].isin(sup_sel)]

    # Separando técnicos que já tiveram inspeção e que nunca tiveram
    inspecionados = df[df['DATA_INSPECAO'].notna()]
    nunca_inspecionados = df[df['DATA_INSPECAO'].isna()]

    st.subheader("Técnicos que já tiveram inspeção")
    st.dataframe(style_badges(inspecionados), use_container_width=True)

    st.subheader("Técnicos nunca inspecionados")
    st.dataframe(nunca_inspecionados, use_container_width=True)

    # Exportação dos dados filtrados
    excel_inspecionados = exportar_excel(inspecionados)
    excel_nunca = exportar_excel(nunca_inspecionados)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Exportar Técnicos com Inspeção",
            data=excel_inspecionados,
            file_name='tecnicos_com_inspecao.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    with col2:
        st.download_button(
            label="Exportar Técnicos Nunca Inspecionados",
            data=excel_nunca,
            file_name='tecnicos_nunca_inspecionados.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

if __name__ == "__main__":
    show()
