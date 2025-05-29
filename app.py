{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "mount_file_id": "1HctDrwGuGYG4awnq4o7qopdFXYxCVRiU",
      "authorship_tag": "ABX9TyPnXvW4ZguMMOHMDyDKkU7A",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/Patriciazambianco/DASHBOARD-EPI/blob/main/app.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "import streamlit as st\n",
        "import pandas as pd\n",
        "import plotly.express as px\n",
        "\n",
        "st.set_page_config(page_title=\"Dashboard EPI\", layout=\"wide\")\n",
        "\n",
        "st.title(\"🛡️ Relatório de EPI - Painel Interativo\")\n",
        "\n",
        "uploaded_file = st.file_uploader(\"📁 Envie seu arquivo CSV com os dados de EPI\", type=[\"csv\"])\n",
        "\n",
        "if uploaded_file:\n",
        "    df = pd.read_csv(uploaded_file)\n",
        "    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')\n",
        "\n",
        "    st.subheader(\"📊 Dados Originais\")\n",
        "    st.dataframe(df)\n",
        "\n",
        "    # Última inspeção por técnico e produto\n",
        "    df = df.sort_values(['TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'], ascending=[True, True, False])\n",
        "    df_unique = df.drop_duplicates(subset=['TECNICO', 'PRODUTO_SIMILAR'], keep='first')\n",
        "\n",
        "    # Define se está pendente (sem data ou >180 dias)\n",
        "    hoje = pd.Timestamp.today()\n",
        "    df_unique['STATUS'] = df_unique['DATA_INSPECAO'].apply(\n",
        "        lambda x: 'PENDENTE' if pd.isna(x) or (hoje - x).days > 180 else 'OK'\n",
        "    )\n",
        "\n",
        "    # Filtros (sidebar pra liberar espaço!)\n",
        "    st.sidebar.header(\"🔎 Filtros\")\n",
        "    gerente = st.sidebar.selectbox(\"Filtrar por Gerente\", options=[\"Todos\"] + sorted(df_unique['GERENTE_IMEDIATO'].dropna().unique()))\n",
        "    coordenador = st.sidebar.selectbox(\"Filtrar por Coordenador\", options=[\"Todos\"] + sorted(df_unique['COORDENADOR_IMEDIATO'].dropna().unique()))\n",
        "\n",
        "    if gerente != \"Todos\":\n",
        "        df_unique = df_unique[df_unique['GERENTE_IMEDIATO'] == gerente]\n",
        "    if coordenador != \"Todos\":\n",
        "        df_unique = df_unique[df_unique['COORDENADOR_IMEDIATO'] == coordenador]\n",
        "\n",
        "    # KPIs\n",
        "    total_registros = df_unique.shape[0]\n",
        "    total_ok = df_unique[df_unique['STATUS'] == 'OK'].shape[0]\n",
        "    total_pendente = total_registros - total_ok\n",
        "    pct_ok = (total_ok / total_registros * 100) if total_registros > 0 else 0\n",
        "\n",
        "    st.subheader(\"✅ Visão Geral\")\n",
        "    col1, col2, col3 = st.columns(3)\n",
        "    col1.metric(\"Total de Registros\", total_registros)\n",
        "    col2.metric(\"Com EPI OK\", total_ok)\n",
        "    col3.metric(\"Pendentes\", total_pendente)\n",
        "\n",
        "    st.progress(pct_ok / 100)\n",
        "\n",
        "    # Gráfico de situação\n",
        "    status_count = df_unique['STATUS'].value_counts().reset_index()\n",
        "    fig_status = px.pie(status_count, names='index', values='STATUS', title='Distribuição de Situação EPI')\n",
        "    st.plotly_chart(fig_status, use_container_width=True)\n",
        "\n",
        "    # Ranking por coordenador\n",
        "    st.subheader(\"🏆 Registros por Coordenador\")\n",
        "    coord_count = df_unique['COORDENADOR_IMEDIATO'].value_counts().reset_index()\n",
        "    coord_count.columns = ['COORDENADOR', 'QTD']\n",
        "    fig_coord = px.bar(coord_count, x='COORDENADOR', y='QTD', title='Quantidade por Coordenador')\n",
        "    st.plotly_chart(fig_coord, use_container_width=True)\n",
        "\n",
        "    # Mostrar dados finais\n",
        "    with st.expander(\"📋 Visualizar dados filtrados\"):\n",
        "        st.dataframe(df_unique)\n",
        "\n",
        "else:\n",
        "    st.info(\"👆 Envie um arquivo CSV para visualizar o painel.\")\n"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/"
        },
        "id": "taGOBZWE-Frb",
        "outputId": "e0a20324-934f-427a-c806-96ddc0ab9946"
      },
      "execution_count": null,
      "outputs": [
        {
          "output_type": "stream",
          "name": "stderr",
          "text": [
            "2025-05-29 16:55:31.982 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.984 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.986 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.987 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.989 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.990 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.992 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.993 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.996 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:55:31.997 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n"
          ]
        }
      ]
    }
  ]
}