@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    st.write("🕵️‍♀️ Colunas encontradas no arquivo:", df.columns.tolist())

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

    # 1️⃣ TABELA COM INSPEÇÃO HISTÓRICA
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby([tecnico_col, produto_col], as_index=False)
        .last()
    )

    ultimas.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)

    ultimas['Status_Final'] = ultimas['Status_Final'].str.upper()

    hoje = pd.Timestamp.now().normalize()
    ultimas['Dias_Sem_Inspecao'] = (hoje - ultimas['Data_Inspecao']).dt.days
    ultimas['Vencido'] = ultimas['Dias_Sem_Inspecao'] > 180

    # 2️⃣ TABELA DE PENDENTES REAIS (sem histórico de inspeção)
    nunca_inspecionados = df[df['Data_Inspecao'].isna()]
    nunca_inspecionados = nunca_inspecionados.drop_duplicates(subset=[tecnico_col, produto_col])
    nunca_inspecionados.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)
    nunca_inspecionados['Status_Final'] = nunca_inspecionados['Status_Final'].str.upper()
    nunca_inspecionados['Data_Inspecao'] = pd.NaT
    nunca_inspecionados['Dias_Sem_Inspecao'] = None
    nunca_inspecionados['Vencido'] = True  # por padrão

    return ultimas, nunca_inspecionados
    st.markdown("---")
    num_pendentes = pendentes_reais.shape[0]

    badge_html = f"""
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
        <span style='font-size: 18px;'>🔍 <strong>Análise de Risco</strong>: Técnicos + Produtos nunca inspecionados</span>
        <span style='
            background-color: #e63946;
            color: white;
            padding: 4px 10px;
            border-radius: 16px;
            font-weight: bold;
            font-size: 13px;
        '>{num_pendentes} pendentes</span>
    </div>
    """

    st.markdown(badge_html, unsafe_allow_html=True)

    with st.expander("Ver detalhes dos pendentes reais", expanded=False):
        st.dataframe(pendentes_reais.reset_index(drop=True), height=300)

        st.download_button(
            label="📥 Baixar pendentes reais (nunca inspecionados)",
            data=exportar_excel(pendentes_reais),
            file_name="pendentes_nunca_inspecionados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
