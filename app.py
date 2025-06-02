import streamlit as st
import pandas as pd
import io

# Função para exportar DataFrame para Excel e retornar bytes para download
def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
        # Nada de writer.save() aqui, o with já faz isso
    return output.getvalue()

# Função para formatar badges coloridos
def badge_color(text, color):
    return f'<span style="background-color:{color};color:white;padding:3px 8px;border-radius:8px;">{text}</span>'

# Função principal do app
def show():
    st.title("Dashboard de Inspeções EPI")

    # Simule a leitura dos dados (substitua pelo seu Excel)
    # Espera-se um DataFrame com pelo menos: Técnico, Produto, Data_Inspeção, Coordenador, Gerente, etc.
    df = pd.read_excel("seus_dados.xlsx")

    # Última inspeção por Técnico + Produto
    ultimas = (df.dropna(subset=['Data_Inspeção'])
                .sort_values('Data_Inspeção')
                .groupby(['Técnico', 'Produto'])
                .last()
                .reset_index())

    # Técnicos que NUNCA foram inspecionados (left join pra pegar só os que não têm inspeção)
    tecnico_produto = df[['Técnico', 'Produto']].drop_duplicates()

    # Criar df com chave para merge
    ultimas_chave = ultimas[['Técnico', 'Produto']].copy()

    nunca = tecnico_produto.merge(ultimas_chave, on=['Técnico', 'Produto'], how='left', indicator=True)
    nunca = nunca[nenhuma := nunca['_merge'] == 'left_only'].drop(columns=['_merge'])

    # Agora pegamos os dados completos dos técnicos que nunca foram inspecionados
    # Se quiser, traga mais colunas de df original
    nunca_completo = df.merge(nunca[['Técnico', 'Produto']], on=['Técnico', 'Produto'], how='inner').drop_duplicates(subset=['Técnico', 'Produto'])

    # Badges para status
    ultimas['Status'] = ultimas['Data_Inspeção'].apply(lambda d: badge_color('Inspecionado', '#28a745'))
    nunca_completo['Status'] = badge_color('Nunca Inspecionado', '#dc3545')

    # Mostrar tabelas
    st.subheader("Últimas Inspeções Realizadas")
    st.write(ultimas.style.format({'Status': lambda x: x}).hide_columns(['Status']), unsafe_allow_html=True)

    st.subheader("Técnicos que Nunca Foram Inspecionados")
    st.write(nunca_completo.style.format({'Status': lambda x: x}), unsafe_allow_html=True)

    # Botões para exportar Excel
    if st.button("Exportar Últimas Inspeções"):
        excel_data = exportar_excel(ultimas)
        st.download_button(label="Baixar Últimas Inspeções", data=excel_data, file_name='ultimas_inspecoes.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    if st.button("Exportar Técnicos Nunca Inspecionados"):
        excel_data = exportar_excel(nunca_completo)
        st.download_button(label="Baixar Nunca Inspecionados", data=excel_data, file_name='tecnicos_nunca_inspecionados.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == "__main__":
    show()
