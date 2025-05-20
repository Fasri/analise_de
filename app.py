import pandas as pd 
import streamlit as st
import os
from io import BytesIO
import datetime
from transform_tempo_real import transform_tempo_real

# Definir os caminhos dos arquivos
ARQUIVO_CONSOLIDACAO = "consolidacao.xlsx"
ARQUIVO_TEMPO_REAL = "final_tempo_real.xlsx"
QUANTIDADE_PROCESSOS_PJE = "qunt_processos_pje.xlsx"


def obter_data_arquivo(caminho):
    """Retorna a data de modificação do arquivo."""
    if os.path.exists(caminho):
        timestamp = os.path.getmtime(caminho)
        return datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
    return None

# Título e descrição na página principal
st.title("📊 Sistema de Monitoramento de Processos")

# Mostrar informações dos arquivos logo de início
st.subheader("📁 Arquivos Disponíveis")
col1, col2 , col3 = st.columns(3)
with col1:
    data_tempo_real = obter_data_arquivo(ARQUIVO_TEMPO_REAL)
    st.markdown(f"**`{ARQUIVO_TEMPO_REAL}`**: {data_tempo_real or 'Arquivo não encontrado'}")

with col2:
    data_consolidacao = obter_data_arquivo(ARQUIVO_CONSOLIDACAO)
    st.markdown(f"**`{ARQUIVO_CONSOLIDACAO}`**: {data_consolidacao or 'Arquivo não encontrado'}")

with col3:
    data_quantidade = obter_data_arquivo(QUANTIDADE_PROCESSOS_PJE)
    st.markdown(f"**`{QUANTIDADE_PROCESSOS_PJE}`**: {data_quantidade or 'Arquivo não encontrado'}")

# Sidebar com menu
st.sidebar.title("📌 MENU PRINCIPAL")
opcao = st.sidebar.radio("Escolha uma opção:", ["Processos em tempo real", "Análise de processos parados", "Quantidades de processos no PJE", "Notificação de processos"])

# --- Processos em tempo real ---
if opcao == "Processos em tempo real":
    st.subheader("📈 Processos em Tempo Real")

    if data_tempo_real:
        st.write(f"🕒 Última atualização: **{data_tempo_real}**")
        escolha = st.radio("O que deseja fazer?", ["Baixar", "Fazer Upload"])

        if escolha == "Baixar":
            with open(ARQUIVO_TEMPO_REAL, "rb") as file:
                st.download_button("📥 Baixar Arquivo", file, file_name="tempo_real.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            uploaded_file = st.file_uploader("📤 Envie um novo arquivo XLSX", type=["xlsx"])
            if uploaded_file is not None:
                novo_arquivo = "novo_tempo_real.xlsx"
                with open(novo_arquivo, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.info("📊 Processando o novo arquivo...")
                try:
                    processado_path = transform_tempo_real(novo_arquivo)
                    with open(processado_path, "rb") as file:
                        st.download_button("📥 Baixar Arquivo Processado", file, file_name="processado_tempo_real.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.success("✅ Arquivo processado com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro ao processar o arquivo: {e}")
    else:
        st.error("🚨 O arquivo `tempo_real.xlsx` não foi encontrado!")

# --- Análise de processos parados ---
elif opcao == "Análise de processos parados":
    st.subheader("📉 Análise de Processos Parados")

    if not data_consolidacao:
        st.error("🚨 O arquivo `consolidacao.xlsx` não foi encontrado!")
        st.stop()

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
        df_filtro_30 = df[(df["Tempo na Contadoria"] > 30) & (df["Cumprimento"] == "pendente")]

        df_sem_calculista = df_filtro[df_filtro["Calculista"].isna()]
        df_sem_calculista = df_sem_calculista[["Núcleo", "Posição Geral","Posição Prioridade", "Número do processo", "Vara", "Data Remessa Contadoria", "Prioridade", "Tempo na Contadoria"]]

        df_filtro_30 = df_filtro_30[["Núcleo", "Posição Geral","Posição Prioridade", "Número do processo", "Vara", "Data Remessa Contadoria", "Prioridade", "Calculista", "Tempo na Contadoria", "Tempo com o Contador"]]

        df_total = pd.DataFrame({
            "Total": [len(df_sem_calculista), len(df_filtro_30)]
        }, index=["Sem Calculista", "Com Calculista"])

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_sem_calculista.to_excel(writer, sheet_name="Sem Calculista", index=False)
            df_filtro_30.to_excel(writer, sheet_name="Mais de 30", index=False)
            df_total.to_excel(writer, sheet_name="Resumo", index=True)
        output.seek(0)
        return output, len(df_sem_calculista), len(df_filtro_30), df_sem_calculista, df_filtro_30

    if st.button("🔄 Processar Arquivo"):
        try:
            output, total_sem_calculista, total_mais_30, df_sem_calculista, df_filtro_30 = processar_tabela(ARQUIVO_CONSOLIDACAO)
            st.subheader("🔍 Resumo dos Processos")
            st.write(f"📌 **Total de processos com mais de 15 dias sem calculista:** {total_sem_calculista}")
            st.dataframe(df_sem_calculista)
            st.bar_chart(df_sem_calculista["Núcleo"].value_counts(), use_container_width=True)            
            st.write(f"📌 **Total de processos com mais de 30 dias:** {total_mais_30}")
            st.dataframe(df_filtro_30)
            st.scatter_chart(df_filtro_30["Núcleo"].value_counts(), use_container_width=True)
            st.bar_chart(df_filtro_30["Núcleo"].value_counts(), use_container_width=True)         
            st.download_button("📥 Baixar Arquivo Processado", output, file_name="processado_consolidacao.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {e}")

# --- Quantidades de processos no PJE ---
elif opcao == "Quantidades de processos no PJE":
    st.subheader("📊 Quantidades de Processos no PJE")
    df = pd.read_excel("qunt_processos_pje.xlsx")
    df["data"] = pd.to_datetime(df["data"])
    df["data"] = df["data"].dt.strftime("%d/%m/%Y")
    
    st.table(df)

    #grafico scatter
    st.subheader("📈 Gráfico de Processos no PJE")
                 
    st.write("Gráfico de dispersão dos processos no PJE ao longo do tempo.")
    st.scatter_chart(df, x="nucleo", y="quantidade", use_container_width=True)    
    st.bar_chart(df, x="nucleo", y="quantidade", use_container_width=True)
 