import pandas as pd
import streamlit as st
import os
from io import BytesIO
import datetime
from transform_tempo_real import transform_tempo_real

# Definir os caminhos dos arquivos
ARQUIVO_CONSOLIDACAO = "consolidacao.xlsx"
ARQUIVO_TEMPO_REAL = "final_tempo_real.xlsx"

def obter_data_arquivo(caminho):
    """Retorna a data de modificação do arquivo."""
    if os.path.exists(caminho):
        timestamp = os.path.getmtime(caminho)
        return datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
    return None

st.title("📊 Bem-vindo ao Sistema de Monitoramento de Processos")
st.write("Olá! O que você quer fazer hoje?")

# Menu inicial
opcao = st.radio("Escolha uma opção:", ["Processos em tempo real", "Análise de processos parados"])

if opcao == "Processos em tempo real":
    data_tempo_real = obter_data_arquivo(ARQUIVO_TEMPO_REAL)
    
    if data_tempo_real:
        st.write(f"📂 O arquivo `tempo_real.xlsx` foi atualizado em: **{data_tempo_real}**")
        escolha = st.radio("Deseja baixar o arquivo ou fazer upload de um novo?", ["Baixar", "Fazer Upload"])
        
        if escolha == "Baixar":
            with open(ARQUIVO_TEMPO_REAL, "rb") as file:
                st.download_button("📥 Baixar Arquivo", file, file_name="tempo_real.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            uploaded_file = st.file_uploader("Envie um novo arquivo XLSX", type=["xlsx"])
            if uploaded_file is not None:
                novo_arquivo = "novo_tempo_real.xlsx"
                with open(novo_arquivo, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.write("📊 Processando o novo arquivo...")
               
                
                with open( transform_tempo_real(novo_arquivo), "rb") as file:
                    st.download_button("📥 Baixar Arquivo Processado", file, file_name="processado_tempo_real.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.success("✅ Arquivo processado com sucesso!")
               
    else:
        st.write("🚨 O arquivo `tempo_real.xlsx` não foi encontrado!")
   
elif opcao == "Análise de processos parados":
    data_consolidacao = obter_data_arquivo(ARQUIVO_CONSOLIDACAO)
    if data_consolidacao:
        st.write(f"📂 O arquivo `consolidacao.xlsx` foi atualizado em: **{data_consolidacao}**")
    else:
        st.write("🚨 O arquivo `consolidacao.xlsx` não foi encontrado!")
        st.stop()

    # Função para processar a tabela
    def processar_tabela(caminho_arquivo):
        df = pd.read_excel(caminho_arquivo)

        colunas_necessarias = ["Tempo na Contadoria", "Tempo com o Contador", "Cumprimento", "Calculista"]
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                st.error(f"A coluna '{coluna}' não foi encontrada no arquivo.")
                return None

        df["Tempo na Contadoria"] = pd.to_numeric(df["Tempo na Contadoria"], errors="coerce")
        df["Tempo com o Contador"] = pd.to_numeric(df["Tempo com o Contador"], errors="coerce")
        df["Cumprimento"] = df["Cumprimento"].astype(str).str.lower()

        df_filtro = df[(df["Tempo na Contadoria"] > 15) & (df["Cumprimento"] == "pendente")]
        df_filtro_calculista = df[(df["Tempo na Contadoria"] > 30) & (df["Cumprimento"] == "pendente")]
        
        df_sem_calculista = df_filtro[df_filtro["Calculista"].isna()]
        df_com_calculista = df_filtro_calculista[df_filtro_calculista["Calculista"].notna()]

        df_total = pd.DataFrame({
            "Total": [len(df_sem_calculista), len(df_com_calculista)]
        }, index=["Sem Calculista", "Com Calculista"])

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_sem_calculista.to_excel(writer, sheet_name="Sem Calculista", index=False)
            df_com_calculista.to_excel(writer, sheet_name="Com Calculista", index=False)
            df_total.to_excel(writer, sheet_name="Resumo", index=True)
        output.seek(0)
        return output, len(df_sem_calculista), len(df_com_calculista)

    if st.button("🔄 Processar Arquivo"):
        try:
            output, total_sem_calculista, total_com_calculista = processar_tabela(ARQUIVO_CONSOLIDACAO)
            st.subheader("🔍 Resumo dos Processos")
            st.write(f"📌 **Total de processos com mais de 15 dias sem calculista:** {total_sem_calculista}")
            st.write(f"📌 **Total de processos atribuídos a mais de 30 dias:** {total_com_calculista}")
            st.download_button("📥 Baixar Arquivo Processado", data=output, file_name="processos_filtrados.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
