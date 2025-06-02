import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Dashboard Inspeção EPI", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    # Detectar colunas técnicas, produtos e data inspeção automaticamente
    col_tec = [col for col in df.columns if 'TECNICO' in col.upper()]
    col_prod = [col for col in df.columns if 'PRODUTO' in col.upper()]
    col_data = [col for col in df.columns if 'INSPECAO' in col.upper()]

    tecnico_col = col_tec[0]
    produto_col = col_prod[0]
    data_col = col_data[0]

    # Renomear colunas para padrão
    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'COORDENADOR': 'COORDENADOR',
        'SITUAÇÃO CHECK LIST': 'Status_Final'
    }, inplace=True)

    df['Data_Inspecao'] = pd.to_datetime(df[data_col], errors='coerce')

    # Base completa único técnico+produto
    base = df[[tecnico_col, produto_col, 'GERENTE_IMEDIATO', 'COORDENADOR']].drop_duplicates()

    # Técnicos que já fizeram pelo menos 1 inspeção em qualquer produto
    tecnicos_inspecionados = df[df['Data_Inspecao'].notnull()][tecnico_col].unique()

    # Última inspeção por técnico+produto
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby([tecnico_col, produto_col], as_index=False)
        .last()
    )

    # Juntar base completa com últimas inspeções (left join)
    final = pd.merge(base, ultimas, on=[tecnico_col, produto_col], how='left', suffixes=('', '_ult'))

    # Ajustar nomes colunas para padrão visual
    final.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)

    # Função para status final considerando técnicos com ou sem inspeção em outros produtos
    def status_final(row):
        if pd.notnull(row['Data_Inspecao']):
            return row['Status_Final'].upper() if pd.notnull(row['Status_Final']) else 'OK'
        else:
            if row['TECNICO'] in tecnicos_inspecionados:
                return 'PENDENTE'
            else:
                return 'NUNCA INSPECIONADO'

    final['Status_Final'] = final.apply(status_final, axis=1)

    hoje = pd.Timestamp.now().normalize()
    final['Dias_Sem_Inspecao'] = (hoje - final['Data_Inspecao']).dt.days
    final['Vencido'] = final['Dias_Sem_Inspecao'] > 180

    return final

def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
        writer.save()
    processed_data = output.getvalue()
    return processed_data

def cor_badge(status):
    if status == "OK":
        return 'background-color: #4CAF50; color: white; font-weight: bold;'  # verde
    elif status == "PENDENTE":
        return 'background-color: #FFC107; color: black; font-weight: bold;'  # amarelo
    elif status == "NUNCA INSPECIONADO":
        return 'background-color: #f44336; color: white; font-weight: bold;'  # vermelho
    else:
        return ''

def style_df(df):
    return df.style.applymap(lambda x: cor_badge(x) if x in ["OK", "PENDENTE", "NUNCA INSPECIONADO"] else '', subset=['Status_Final'])

def show():
    st.title("Dashboard Inspeção EPI")

    df = carregar_dados()

    # Filtros básicos
    gerente_sel = st.multiselect("Selecione Gerente(s)", options=df['GERENTE_IMEDIATO'].unique(), default=df['GERENTE_IMEDIATO'].unique())
    coord_sel = st.multiselect("Selecione Coordenador(es)", options=df['COORDENADOR'].unique(), default=df['COORDENADOR'].unique())

    df_filtrado = df[
        (df['GERENTE_IMEDIATO'].isin(gerente_sel)) &
        (df['COORDENADOR'].isin(coord_sel))
    ]

    st.subheader("Técnicos com Última Inspeção")
    ultimas = df_filtrado[df_filtrado['Status_Final'] != 'NUNCA INSPECIONADO']
    st.dataframe(style_df(ultimas), use_container_width=True)

    st.download_button(
        label="Exportar Últimas Inspeções para Excel",
        data=exportar_excel(ultimas),
        file_name='ultimas_inspecoes.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.subheader("Técnicos Nunca Inspecionados")
    nunca = df_filtrado[df_filtrado['Status_Final'] == 'NUNCA INSPECIONADO']
    st.dataframe(style_df(nunca), use_container_width=True)

    st.download_button(
        label="Exportar Técnicos Nunca Inspecionados para Excel",
        data=exportar_excel(nunca),
        file_name='tecnicos_nunca_inspecionados.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == "__main__":
    show()
