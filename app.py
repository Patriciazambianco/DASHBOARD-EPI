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

    base = df[[tecnico_col, produto_col]].drop_duplicates()

    # Linhas com inspeção (última inspeção por técnico+produto)
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby([tecnico_col, produto_col], as_index=False)
        .last()
    )

    final = pd.merge(base, ultimas, on=[tecnico_col, produto_col], how='left')

    final.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)

    final['Status_Final'] = final['Status_Final'].astype(str).str.upper()

    hoje = pd.Timestamp.now().normalize()
    final['Dias_Sem_Inspecao'] = (hoje - final['Data_Inspecao']).dt.days
    final['Vencido'] = final['Dias_Sem_Inspecao'] > 180

    # Técnicos que NUNCA tiveram inspeção (Data_Inspecao é NaT)
    nunca = final[final['Data_Inspecao'].isna()].copy()

    return final, nunca

def exportar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
        # writer.save()  <-- REMOVIDO, pois dentro do 'with' não precisa
    return buffer.getvalue()

def plot_pie_chart(df, group_col, title_prefix):
    grouped = df.groupby(group_col)['Status_Final'].value_counts().unstack(fill_value=0)
    for status in ['OK', 'PENDENTE']:
        if status not in grouped.columns:
            grouped[status] = 0
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

    final, nunca = carregar_dados()
    if final.empty and nunca.empty:
        st.warning("Nenhum dado disponível para exibir.")
        return

    gerentes = sorted(final['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", ["Todos"] + gerentes)

    if gerente_sel != "Todos":
        final_filtrado = final[final['GERENTE_IMEDIATO'] == gerente_sel]
        nunca_filtrado = nunca[nunca['GERENTE_IMEDIATO'] == gerente_sel]
    else:
        final_filtrado = final.copy()
        nunca_filtrado = nunca.copy()

    coordenadores = sorted(final_filtrado['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    final_filtrado = final_filtrado[final_filtrado['COORDENADOR'].isin(coord_sel)]
    nunca_filtrado = nunca_filtrado[nunca_filtrado['COORDENADOR'].isin(coord_sel)]

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        final_filtrado = final_filtrado[final_filtrado['Vencido']]

    df_pendentes = final_filtrado[final_filtrado['Status_Final'] == 'PENDENTE']

    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="📥 Baixar Técnicos Nunca Inspecionados (.xlsx)",
        data=exportar_excel(nunca_filtrado),
        file_name="tecnicos_nunca_inspecionados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    total = final_filtrado.shape[0] if final_filtrado.shape[0] > 0 else 1
    pct_pendentes = (final_filtrado['Status_Final'] == 'PENDENTE').sum() / total * 100
    pct_ok = (final_filtrado['Status_Final'] == 'OK').sum() / total * 100

    num_tecnicos = final_filtrado['TECNICO'].nunique()
    tecnicos_inspecionaram = final_filtrado[final_filtrado['Data_Inspecao'].notnull()]['TECNICO'].nunique()
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

    st.subheader("🍕 Status das Inspeções por Gerente")
    graficos_gerente = plot_pie_chart(final_filtrado, 'GERENTE_IMEDIATO', "Gerente")
    for i in range(0, len(graficos_gerente), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_gerente[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("🍕 Status das Inspeções por Coordenador")
    graficos_coord = plot_pie_chart(final_filtrado, 'COORDENADOR', "Coordenador")
    for i in range(0, len(graficos_coord), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_coord[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 Dados detalhados - Inspeções")
    st.dataframe(final_filtrado.reset_index(drop=True), height=400)

    st.markdown("---")

    st.subheader("📋 Técnicos Nunca Inspecionados")
    st.dataframe(nunca_filtrado.reset_index(drop=True), height=300)

if __name__ == "__main__":
    show()
