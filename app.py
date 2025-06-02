import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Dashboard de EPI", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    col_tec = [col for col in df.columns if 'TECNICO' in col.upper()]
    col_prod = [col for col in df.columns if 'PRODUTO' in col.upper()]
    col_data = [col for col in df.columns if 'INSPECAO' in col.upper()]

    if not col_tec or not col_prod or not col_data:
        st.error("❌ Verifique se o arquivo contém colunas de TÉCNICO, PRODUTO e INSPEÇÃO.")
        return pd.DataFrame(), pd.DataFrame()

    tecnico_col = col_tec[0]
    produto_col = col_prod[0]
    data_col = col_data[0]

    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'Status_Final'
    }, inplace=True)

    df['Data_Inspecao'] = pd.to_datetime(df[data_col], errors='coerce')

    # Base técnica-produto única
    base = df[[tecnico_col, produto_col]].drop_duplicates()

    # Inspeções feitas: pegar última inspeção por técnico-produto
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
          .sort_values('Data_Inspecao')
          .groupby([tecnico_col, produto_col], as_index=False)
          .last()
    )

    # Pendentes = base menos os que já têm inspeção
    pendentes = base.merge(
        ultimas[[tecnico_col, produto_col]],
        on=[tecnico_col, produto_col],
        how='left',
        indicator=True
    )
    pendentes = pendentes[pendentes['_merge'] == 'left_only'].drop(columns=['_merge'])

    # Criar df pendentes completo com dados do df original (para exibir e exportar)
    pendentes = pendentes.merge(df, on=[tecnico_col, produto_col], how='left')

    # Técnicos que nunca inspecionaram NENHUM produto
    tecnicos_com_inspecao = ultimas[tecnico_col].unique()
    tecnicos_base = df[tecnico_col].unique()
    tecnicos_nunca = [tec for tec in tecnicos_base if tec not in tecnicos_com_inspecao]
    nunca_inspecionados = df[df[tecnico_col].isin(tecnicos_nunca)].drop_duplicates(subset=[tecnico_col, produto_col])

    # Renomear colunas pra padronizar depois
    ultimas.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)
    pendentes.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)
    nunca_inspecionados.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)

    ultimas['Status_Final'] = ultimas['Status_Final'].str.upper()
    pendentes['Status_Final'] = pendentes['Status_Final'].str.upper()
    nunca_inspecionados['Status_Final'] = nunca_inspecionados['Status_Final'].str.upper()

    # Calcular colunas extras para ultimas inspeções
    hoje = pd.Timestamp.now().normalize()
    ultimas['Dias_Sem_Inspecao'] = (hoje - ultimas['Data_Inspecao']).dt.days
    ultimas['Vencido'] = ultimas['Dias_Sem_Inspecao'] > 180

    return ultimas, pendentes, nunca_inspecionados

def exportar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
        writer.save()
    return buffer.getvalue()

def color_status_badge(status):
    if status == "PENDENTE":
        return "🔴 PENDENTE"
    elif status == "OK":
        return "🟢 OK"
    else:
        return status

def show():
    st.title("📊 Dashboard de Inspeções EPI")

    ultimas, pendentes, nunca_inspecionados = carregar_dados()
    if ultimas.empty and pendentes.empty and nunca_inspecionados.empty:
        return

    # Filtros simples por gerente e coordenador (opcional)
    gerentes = sorted(ultimas['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", ["Todos"] + gerentes)

    if gerente_sel != "Todos":
        ultimas_f = ultimas[ultimas['GERENTE_IMEDIATO'] == gerente_sel]
        pendentes_f = pendentes[pendentes['GERENTE_IMEDIATO'] == gerente_sel]
        nunca_f = nunca_inspecionados[never_inspecionados['GERENTE_IMEDIATO'] == gerente_sel]
    else:
        ultimas_f = ultimas.copy()
        pendentes_f = pendentes.copy()
        nunca_f = nunca_inspecionados.copy()

    coordenadores = sorted(ultimas_f['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    ultimas_f = ultimas_f[ultimas_f['COORDENADOR'].isin(coord_sel)]
    pendentes_f = pendentes_f[pendentes_f['COORDENADOR'].isin(coord_sel)]
    nunca_f = nunca_f[nunca_f['COORDENADOR'].isin(coord_sel)]

    # Mostrar só vencidos > 180 dias?
    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        ultimas_f = ultimas_f[ultimas_f['Vencido'] == True]

    # Criar badges coloridos
    ultimas_f['Status_Colorido'] = ultimas_f['Status_Final'].apply(color_status_badge)
    pendentes_f['Status_Colorido'] = pendentes_f['Status_Final'].apply(color_status_badge)
    nunca_f['Status_Colorido'] = nunca_f['Status_Final'].apply(color_status_badge)

    st.subheader("✅ Últimas Inspeções Realizadas")
    st.dataframe(ultimas_f)

    st.subheader("⚠️ Técnicos e Produtos PENDENTES (Nunca Inspecionados)")
    st.dataframe(pendentes_f)

    st.subheader("❌ Técnicos que Nunca Realizaram Inspeção")
    st.dataframe(nunca_f)

    st.download_button(
        label="📥 Baixar Últimas Inspeções (.xlsx)",
        data=exportar_excel(ultimas_f),
        file_name="ultimas_inspecoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(pendentes_f),
        file_name="pendentes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.download_button(
        label="📥 Baixar Técnicos Nunca Inspecionados (.xlsx)",
        data=exportar_excel(nunca_f),
        file_name="tecnicos_nunca_inspecionados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    show()
