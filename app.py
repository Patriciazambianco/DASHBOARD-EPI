import streamlit as st
import pandas as pd
import io

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    # Ajuste colunas (adapte se precisar)
    tecnico_col = [c for c in df.columns if 'TECNICO' in c.upper()][0]
    produto_col = [c for c in df.columns if 'PRODUTO' in c.upper()][0]
    data_col = [c for c in df.columns if 'INSPECAO' in c.upper()][0]

    # Renomeia para padronizar
    df.rename(columns={'GERENTE': 'GERENTE_IMEDIATO', 'SITUAÇÃO CHECK LIST': 'Status_Final'}, inplace=True)
    df['Data_Inspecao'] = pd.to_datetime(df[data_col], errors='coerce')

    # Base única técnico+produto
    base = df[[tecnico_col, produto_col]].drop_duplicates()

    # Quem já teve inspeção
    com_inspecao = df.dropna(subset=['Data_Inspecao'])[[tecnico_col, produto_col]].drop_duplicates()

    # Nunca inspecionados = base menos os que já tiveram inspeção
    nunca = pd.merge(base, com_inspecao, on=[tecnico_col, produto_col], how='left', indicator=True)
    nunca = nunca[nenhuma = nunca['_merge'] == 'left_only'].drop(columns=['_merge'])

    # Última inspeção de cada técnico+produto
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby([tecnico_col, produto_col], as_index=False)
        .last()
    )

    # Tabela final junta base com últimas inspeções (ou sem inspeção = NaN)
    final = pd.merge(base, ultimas, on=[tecnico_col, produto_col], how='left')

    # Padroniza nomes colunas para usar em filtros e exibição
    final.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)
    nunca.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)

    return final, nunca

def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
        writer.save()
    processed_data = output.getvalue()
    return processed_data

def badge_status(status):
    if status == "OK":
        return f"<span style='color: white; background-color: green; padding: 3px 8px; border-radius: 5px;'>OK</span>"
    elif status == "Pendente":
        return f"<span style='color: white; background-color: red; padding: 3px 8px; border-radius: 5px;'>Pendente</span>"
    else:
        return f"<span style='color: black; background-color: gray; padding: 3px 8px; border-radius: 5px;'>{status}</span>"

def show():
    st.title("Dashboard de Inspeções EPI")

    # Carregar dados
    df_pendentes, df_nunca = carregar_dados()

    # Seleção filtros (adapte colunas para seu dataset)
    gerentes = ['Todos'] + sorted(df_pendentes['GERENTE_IMEDIATO'].dropna().unique().tolist())
    gerente_sel = st.selectbox("Selecione Gerente", gerentes)

    coord_col = 'COORDENADOR' if 'COORDENADOR' in df_pendentes.columns else None
    if coord_col:
        coordenadores = ['Todos'] + sorted(df_pendentes[coord_col].dropna().unique().tolist())
        coord_sel = st.multiselect("Selecione Coordenador(s)", coordenadores, default=['Todos'])
    else:
        coord_sel = ['Todos']

    # Filtra pendentes (exemplo filtro simples, adapte conforme necessidade)
    pendentes = df_pendentes.copy()
    if gerente_sel != 'Todos':
        pendentes = pendentes[pendentes['GERENTE_IMEDIATO'] == gerente_sel]

    if coord_col and 'Todos' not in coord_sel:
        pendentes = pendentes[pendentes[coord_col].isin(coord_sel)]

    # Filtra técnicos nunca inspecionados - só filtra se colunas existirem
    nunca_filtrado = df_nunca.copy()
    if 'GERENTE_IMEDIATO' in nunca_filtrado.columns and gerente_sel != 'Todos':
        nunca_filtrado = nunca_filtrado[nenhuma['GERENTE_IMEDIATO'] == gerente_sel]

    if coord_col and 'Todos' not in coord_sel and coord_col in nunca_filtrado.columns:
        nunca_filtrado = nunca_filtrado[nenhuma[coord_col].isin(coord_sel)]

    st.subheader("Técnicos Pendentes de Inspeção")
    st.write(f"Quantidade: {len(pendentes)}")
    if not pendentes.empty:
        # Exemplo badge na coluna Status_Final
        pendentes['Status_Color'] = pendentes['Status_Final'].fillna('Pendente').apply(badge_status)
        st.write(pendentes.style.format({'Status_Color': lambda x: x}).hide_columns([]), unsafe_allow_html=True)

        btn_pendentes = st.download_button(
            label="Exportar Pendentes para Excel",
            data=exportar_excel(pendentes),
            file_name="pendentes_inspecao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhum técnico pendente encontrado.")

    st.subheader("Técnicos Nunca Inspecionados")
    st.write(f"Quantidade: {len(nunca_filtrado)}")
    if not nunca_filtrado.empty:
        st.write(nunca_filtrado)

        btn_nunca = st.download_button(
            label="Exportar Técnicos Nunca Inspecionados",
            data=exportar_excel(nunca_filtrado),
            file_name="tecnicos_nunca_inspecionados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhum técnico nunca inspecionado encontrado.")

if __name__ == "__main__":
    show()
