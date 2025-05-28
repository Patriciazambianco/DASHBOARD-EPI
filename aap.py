# Instala Streamlit e ngrok
!pip install streamlit
!pip install pyngrok
!pip install pandas plotly openpyxl

# Cria um arquivo app.py com código básico (ajuste seu código aqui)
code = """
import streamlit as st
import pandas as pd
import plotly.express as px

st.title('Dashboard EPI - Upload e gráficos')

uploaded_file = st.file_uploader("📁 Envie seu arquivo Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    st.write(df.head())

    # Exemplo de gráfico
    fig = px.bar(df, x=df.columns[0], y=df.columns[1])
    st.plotly_chart(fig)
else:
    st.write("Envie um arquivo para começar.")
"""

with open("app.py", "w") as f:
    f.write(code)

# Importa ngrok e streamlit
from pyngrok import ngrok
import threading
import os

# Função para rodar o Streamlit
def run_streamlit():
    os.system('streamlit run app.py')

# Libera a porta 8501 para o túnel ngrok
public_url = ngrok.connect(port=8501)
print(f"Streamlit será exposto no link: {public_url}")

# Roda o Streamlit em background numa thread
threading.Thread(target=run_streamlit).start()


