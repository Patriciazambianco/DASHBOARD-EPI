import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Simulando dados
np.random.seed(42)
n = 200
data = pd.DataFrame({
    'Tecnico': np.random.choice(['Ana', 'Bruno', 'Carla', 'Diego'], n),
    'Produto': np.random.choice(['Produto A', 'Produto B', 'Produto C'], n),
    'Data_Inspecao': pd.to_datetime('2025-01-01') + pd.to_timedelta(np.random.randint(0, 150, n), unit='D'),
    'Status': np.random.choice(['OK', 'Pendente'], n, p=[0.75, 0.25]),
    'Dias_Desde_Inspecao': np.random.randint(0, 200, n)
})

# --- Sidebar filtros ---
st.sidebar.header("Filtros")
tecnicos = st.sidebar.multiselect("Técnicos", options=data['Tecnico'].unique(), default=data['Tecnico'].unique())
produtos = st.sidebar.multiselect("Produtos", options=data['Produto'].unique(), default=data['Produto'].unique())

data_min = data['Data_Inspecao'].min()
data_max = data['Data_Inspecao'].max()
data_slider = st.sidebar.slider("Período da Inspeção", value=(data_min, data_max), min_value=data_min, max_value=data_max)

status_filtro = st.sidebar.multiselect("Status", options=data['Status'].unique(), default=data['Status'].unique())

# --- Filtragem ---
df_filtrado = data[
    (data['Tecnico'].isin(tecnicos)) &
    (data['Produto'].isin(produtos)) &
    (data['Status'].isin(status_filtro)) &
    (data['Data_Inspecao'] >= pd.to_datetime(data_slider[0])) &
    (data['Data_Inspecao'] <= pd.to_datetime(data_slider[1]))
]

# --- Cabeçalho ---
st.title("📊 Dashboard de Inspeções Aprimorado")
st.markdown(f"**Período selecionado:** {data_slider[0].date()} até {data_slider[1].date()}")

# --- KPIs ---
total_inspec = df_filtrado.shape[0]
pct_ok = (df_filtrado['Status'] == 'OK').mean() * 100 if total_inspec > 0 else 0
pendencias = (df_filtrado['Status'] == 'Pendente').sum()
media_dias = df_filtrado['Dias_Desde_Inspecao'].mean() if total_inspec > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Inspeções", total_inspec)
col2.metric("Checklists OK (%)", f"{pct_ok:.1f}%")
col3.metric("Pendências", pendencias)
col4.metric("Média Dias Desde Inspeção", f"{media_dias:.1f}")

# --- Gráficos ---
with st.container():
    col1, col2 = st.columns(2)

    # Linha: inspeções por data
    inspec_por_dia = df_filtrado.groupby('Data_Inspecao').size().reset_index(name='Qtd')
    fig_linha = px.line(inspec_por_dia, x='Data_Inspecao', y='Qtd', title='Inspeções ao longo do tempo')
    col1.plotly_chart(fig_linha, use_container_width=True)

    # Pizza: Status geral
    status_counts = df_filtrado['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Qtd']
    fig_pizza = px.pie(status_counts, values='Qtd', names='Status', title='Distribuição de Status', color='Status',
                       color_discrete_map={'OK': 'green', 'Pendente': 'red'})
    col2.plotly_chart(fig_pizza, use_container_width=True)

# --- Alertas Dinâmicos ---
st.subheader("🚨 Alertas Dinâmicos")

criticos = df_filtrado[(df_filtrado['Status'] == 'Pendente') & (df_filtrado['Dias_Desde_Inspecao'] > 180)]
moderados = df_filtrado[(df_filtrado['Status'] == 'Pendente') & (df_filtrado['Dias_Desde_Inspecao'].between(90, 180))]
leves = df_filtrado[(df_filtrado['Status'] == 'Pendente') & (df_filtrado['Dias_Desde_Inspecao'] < 90)]

col1, col2, col3 = st.columns(3)
col1.metric("Pendências Críticas (>180 dias)", criticos.shape[0])
col2.metric("Pendências Moderadas (90-180 dias)", moderados.shape[0])
col3.metric("Pendências Recentes (<90 dias)", leves.shape[0])

if criticos.shape[0] > 0:
    with st.expander("Ver Pendências Críticas"):
        st.dataframe(criticos)

# --- Insights Textuais ---
st.subheader("💡 Insights")
if total_inspec == 0:
    st.write("Nenhuma inspeção encontrada para os filtros selecionados. Tente ajustar os filtros.")
else:
    maior_pendencia = df_filtrado.groupby('Tecnico')['Status'].apply(lambda x: (x=='Pendente').sum()).idxmax()
    qtd_maior_pendencia = df_filtrado.groupby('Tecnico')['Status'].apply(lambda x: (x=='Pendente').sum()).max()
    st.markdown(f"- Técnico com mais pendências: **{maior_pendencia}** ({qtd_maior_pendencia} pendências)")
    st.markdown(f"- Média de dias desde a última inspeção: **{media_dias:.1f} dias**")
    if pct_ok < 80:
        st.warning("Atenção! Percentual de checklists OK está abaixo de 80%.")
    else:
        st.success("Ótimo! Percentual de checklists OK está acima de 80%.")

# --- Tabela detalhada ---
st.subheader("📋 Detalhes das Inspeções")
st.dataframe(df_filtrado.reset_index(drop=True), height=300)
