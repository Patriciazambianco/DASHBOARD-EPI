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

    # Últimas inspeções por Técnico+Produto
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby([tecnico_col, produto_col], as_index=False)
        .last()
    )
    ultimas.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)
    ultimas['Status_Final'] = ultimas['Status_Final'].str.upper()

    hoje = pd.Timestamp.now().normalize()
    ultimas['Dias_Sem_Inspecao'] = (hoje - ultimas['Data_Inspecao']).dt.days
    ultimas['Vencido'] = ultimas['Dias_Sem_Inspecao'] > 180

    pares_inspecionados = set(zip(ultimas['TECNICO'], ultimas['PRODUTO']))

    # Nunca inspecionados: linhas com Data_Inspecao vazia e que não estão em ultimas
    nunca_inspecionados = df[df['Data_Inspecao'].isna()].copy()
    nunca_inspecionados.rename(columns={tecnico_col: 'TECNICO', produto_col: 'PRODUTO'}, inplace=True)
    nunca_inspecionados = nunca_inspecionados.drop_duplicates(subset=['TECNICO', 'PRODUTO'])
    nunca_inspecionados = nunca_inspecionados[
        ~nunca_inspecionados[['TECNICO', 'PRODUTO']].apply(tuple, axis=1).isin(pares_inspecionados)
    ]

    nunca_inspecionados['Status_Final'] = nunca_inspecionados['Status_Final'].str.upper()
    nunca_inspecionados['Data_Inspecao'] = pd.NaT
    nunca_inspecionados['Dias_Sem_Inspecao'] = None
    nunca_inspecionados['Vencido'] = True

    return ultimas, nunca_inspecionados


def exportar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendentes')
    return buffer.getvalue()


def plot_pie_chart(df, group_col, title_prefix):
    grouped = df.groupby(group_col)['Status_Final'].value_counts().unstack(fill_value=0)
    if 'OK' in grouped.columns and 'PENDENTE' in grouped.columns:
        grouped = grouped[['OK', 'PENDENTE']]

    charts = []
    for grupo in grouped.index:
        valores = grouped.loc[grupo]
        fig = px.pie(
            names=valores.index,
            values=valores.values,
            color=valores.index,
            color_discrete_map={'OK': '#2a9d8f', 'PENDENTE': '#e76f51'},
            hole=0.4,
            title=f"{title_prefix}: {grupo}"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=250, showlegend=False)
        charts.append(fig)
    return charts


def color_metric(label, value, color):
    st.markdown(f"""
        <div style='
            padding:8px; 
            border-radius:8px; 
            background-color:{color}; 
            color:white; 
            text-align:center;
            font-family:sans-serif;
            font-size:13px;
            '>
            <h5 style='margin-bottom:4px'>{label}</h5>
            <h3 style='margin-top:0'>{value:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)


def show():
    st.title("📊 Dashboard de Inspeções EPI")

    ultimas, nunca_inspecionados = carregar_dados()
    if ultimas.empty and nunca_inspecionados.empty:
        st.warning("Nenhum dado para mostrar!")
        return

    # Filtros básicos baseados nas últimas inspeções
    gerentes = sorted(ultimas['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", ["Todos"] + gerentes)

    if gerente_sel != "Todos":
        ultimas_filtrado = ultimas[ultimas['GERENTE_IMEDIATO'] == gerente_sel]
        nunca_filtrado = nunca_inspecionados[nunca_inspecionados['GERENTE_IMEDIATO'] == gerente_sel]
    else:
        ultimas_filtrado = ultimas.copy()
        nunca_filtrado = nunca_inspecionados.copy()

    coordenadores = sorted(ultimas_filtrado['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    ultimas_filtrado = ultimas_filtrado[ultimas_filtrado['COORDENADOR'].isin(coord_sel)]
    nunca_filtrado = nunca_filtrado[outra_filtrado['COORDENADOR'].isin(coord_sel)]

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        ultimas_filtrado = ultimas_filtrado[ultimas_filtrado['Vencido']]
        nunca_filtrado = nunca_filtrado[never_filtrado['Vencido']]  # sempre True, mas mantemos pra padrão

    # Exibir download para os pendentes (status "PENDENTE" nas últimas inspeções)
    df_pendentes = ultimas_filtrado[ultimas_filtrado['Status_Final'] == 'PENDENTE']
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Métricas
    total = ultimas_filtrado.shape[0] if ultimas_filtrado.shape[0] > 0 else 1
    pct_pendentes = (ultimas_filtrado['Status_Final'] == 'PENDENTE').sum() / total * 100
    pct_ok = (ultimas_filtrado['Status_Final'] == 'OK').sum() / total * 100

    num_tecnicos = ultimas_filtrado['TECNICO'].nunique()
    tecnicos_inspecionaram = ultimas_filtrado[ultimas_filtrado['Data_Inspecao'].notnull()]['TECNICO'].nunique()
    pct_tecnicos_inspecionaram = tecnicos_inspecionaram / num_tecnicos * 100 if num_tecnicos > 0 else 0
    pct_tecnicos_nao_inspecionaram = 100 - pct_tecnicos_inspecionaram

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color_metric("% OK", pct_ok, "#2a9d8f")
    with col2:
        color_metric("% Pendentes", pct_pendentes, "#e76f51")
    with col3:
        color_metric("% Técnicos com Inspeção", pct_tecnicos_inspecionaram, "#f4a261")
    with col4:
        color_metric("% Técnicos sem Inspeção", pct_tecnicos_nao_inspecionaram, "#e76f51")

    st.markdown("---")

    st.subheader("🍕 Status das Últimas Inspeções por Gerente")
    graficos_gerente = plot_pie_chart(ultimas_filtrado, 'GERENTE_IMEDIATO', "Gerente")
    for i in range(0, len(graficos_gerente), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_gerente[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("🍕 Status das Últimas Inspeções por Coordenador")
    graficos_coord = plot_pie_chart(ultimas_filtrado, 'COORDENADOR', "Coordenador")
    for i in range(0, len(graficos_coord), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_coord[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 Técnicos que nunca foram inspecionados")
    st.dataframe(nunca_filtrado[['TECNICO', 'PRODUTO', 'GERENTE_IMEDIATO', 'Status_Final']].reset_index(drop=True))


if __name__ == "__main__":
    show()
