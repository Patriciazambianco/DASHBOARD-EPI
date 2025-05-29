{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "mount_file_id": "1HctDrwGuGYG4awnq4o7qopdFXYxCVRiU",
      "authorship_tag": "ABX9TyOYNgIkpxZIrDWX5LFVjYhP",
      "include_colab_link": True
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
        "<a href=\"https://colab.research.google.com/github/Patriciazambianco/DASHBOARD-EPI/blob/main/streamlit_app.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "import streamlit as st\n",
        "import pandas as pd\n",
        "\n",
        "st.title(\"Relatório de EPI - Painel Interativo\")\n",
        "\n",
        "# Upload do arquivo CSV com os dados de EPI\n",
        "uploaded_file = st.file_uploader(\"Envie seu arquivo CSV com os dados de EPI\", type=[\"csv\"])\n",
        "\n",
        "if uploaded_file:\n",
        "    df = pd.read_csv(uploaded_file)\n",
        "\n",
        "    # Mostrar dados originais\n",
        "    st.subheader(\"Dados Originais\")\n",
        "    st.dataframe(df)\n",
        "\n",
        "    # Remover duplicados por técnico e produto, mantendo a última data de inspeção\n",
        "    # Se houver data, pega a última; mantém linhas sem data também\n",
        "    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')\n",
        "\n",
        "    # Ordena por técnico, produto e data decrescente\n",
        "    df = df.sort_values(['TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'], ascending=[True, True, False])\n",
        "\n",
        "    # Remove duplicados mantendo a primeira aparição (última data)\n",
        "    df_unique = df.drop_duplicates(subset=['TECNICO', 'PRODUTO_SIMILAR'], keep='first')\n",
        "\n",
        "    st.subheader(\"Dados sem duplicados - Última Inspeção por Técnico e Produto\")\n",
        "    st.dataframe(df_unique)\n",
        "\n",
        "    # Filtro por Coordenador (se a coluna existir)\n",
        "    if 'COORDENADOR_IMEDIATO' in df_unique.columns:\n",
        "        coordenadores = df_unique['COORDENADOR_IMEDIATO'].dropna().unique()\n",
        "        selecionado = st.selectbox(\"Filtrar por Coordenador\", options=[\"Todos\"] + list(coordenadores))\n",
        "        if selecionado != \"Todos\":\n",
        "            df_unique = df_unique[df_unique['COORDENADOR_IMEDIATO'] == selecionado]\n",
        "            st.write(f\"Filtrando por Coordenador: {selecionado}\")\n",
        "            st.dataframe(df_unique)\n",
        "\n",
        "    # Ranking de coordenadores por quantidade de registros\n",
        "    if 'COORDENADOR_IMEDIATO' in df_unique.columns:\n",
        "        ranking = df_unique['COORDENADOR_IMEDIATO'].value_counts()\n",
        "        st.subheader(\"Ranking de Coordenadores (por quantidade de registros)\")\n",
        "        st.bar_chart(ranking)\n",
        "\n",
        "else:\n",
        "    st.info(\"Por favor, envie o arquivo CSV para gerar o relatório.\")\n"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/"
        },
        "id": "nco3Z-rr3IO1",
        "outputId": "b23e64ab-f704-4b4b-93a3-658cb29319b8"
      },
      "execution_count": 5,
      "outputs": [
        {
          "output_type": "stream",
          "name": "stderr",
          "text": [
            "2025-05-29 16:25:28.877 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.879 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.880 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.881 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.886 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.888 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.889 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.891 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:25:28.892 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n"
          ]
        }
      ]
    }
  ]
}
