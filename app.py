import streamlit as st
import pandas as pd
from io import BytesIO

# Função para carregar dados com cache
@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx")
    return df

# Dicionário de normalização dos produtos
normalizar_produto = {
    'CONE DE SINALIZACAO': 'CONE',
    'DETECTOR DE TENSAO': 'DETECTOR DE TENSAO',
    'LUVA DE BORRACHA': 'LUVA CLASSE 0',
    'LUVA SEGURANCA PROTECAO ELETRICA': 'LUVA CLASSE 0',
    'LUVA DE COBERTURA': 'LUVA COBERTURA',
    'OCULOS DE PROTECAO': 'OCULOS',
    'OCULOS DE SEGURANCA': 'OCULOS',
    'OCULOS DE PROTECAO TIPO RJ': 'OCULOS',
    'LUVA PROTECAO VAQUETA': 'LUVA VAQUETA',
    'CINTO SEGURANCA TIPO PARAQUEDISTA': 'CINTO PARAQUEDISTA',
    'CINTO SEGURANCA TIPO PARAQUEDISTA/ALPINISTA': 'CINTO PARAQUEDISTA',
    'TALABARTE': 'TALABARTE',
    'KIT PARA LINHA DE VIDA': 'KIT RESGATE'
}

def padronizar_categoria_produto(produto):
    for chave in normalizar_produto:
        if chave in produto:
            return normalizar_produto[chave]
    return produto

# Função para exportar como Excel
def exportar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendencias')
    output.seek(0)
    return output

def show():
    st.title("📋 Dashboard de Inspeções de EPI")

    df = carregar_dados()
    df['PRODUTO_SIMILAR'] = df['PRODUTO_SIMILAR'].astype(str).str.upper()
    df['CATEGORIA_PRODUTO'] = df['PRODUTO_SIMILAR'].apply(padronizar_categoria_produto)

    # Última inspeção por técnico + categoria
    df_inspecao = df.dropna(subset=['DATA_INSPECAO'])
    ultimas = df_inspecao.sort_values('DATA_INSPECAO').drop_duplicates(subset=['IDTEL_TECNICO', 'CATEGORIA_PRODUTO'], keep='last')

    # Todas as combinações possíveis Técnico + Categoria
    todos = df[['IDTEL_TECNICO', 'TÉCNICO', 'CATEGORIA_PRODUTO', 'COORDENADOR']].drop_duplicates()

    # Técnicos que NUNCA foram inspecionados para determinada categoria
    pendentes = todos.merge(ultimas[['IDTEL_TECNICO', 'CATEGORIA_PRODUTO']],
                            on=['IDTEL_TECNICO', 'CATEGORIA_PRODUTO'], how='left', indicator=True)
    pendentes = pendentes[pendentes['_merge'] == 'left_only'].drop(columns=['_merge'])

    st.subheader("📌 Técnicos com EPIs Ainda Não Inspecionados")
    st.dataframe(pendentes, use_container_width=True)

    st.download_button(
        label="⬇️ Baixar Pendentes em Excel",
        data=exportar_excel(pendentes),
        file_name="pendencias_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("✅ Últimas Inspeções por Técnico + EPI")
    st.dataframe(ultimas[['IDTEL_TECNICO', 'TÉCNICO', 'CATEGORIA_PRODUTO', 'DATA_INSPECAO']], use_container_width=True)

    st.download_button(
        label="⬇️ Baixar Inspecionados em Excel",
        data=exportar_excel(ultimas),
        file_name="inspecionados_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == '__main__':
    show()
