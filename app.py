import pandas as pd
import streamlit as st
from io import BytesIO

# Caminho do arquivo dentro do contêiner
ARQUIVO_LOCAL = "consolidacao.xlsx"  # Ajuste conforme necessário

# Função para processar a tabela
def processar_tabela(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo)

    # Verificar se todas as colunas necessárias existem
    colunas_necessarias = ["Tempo na Contadoria", "Tempo com o Contador", "Cumprimento", "Calculista"]
    for coluna in colunas_necessarias:
        if coluna not in df.columns:
            st.error(f"A coluna '{coluna}' não foi encontrada no arquivo.")
            return None

    # Garantir que 'Tempo na Contadoria' e 'Tempo com o Contador' sejam numéricos
    df["Tempo na Contadoria"] = pd.to_numeric(df["Tempo na Contadoria"], errors="coerce")
    df["Tempo com o Contador"] = pd.to_numeric(df["Tempo com o Contador"], errors="coerce")

    # Filtrar processos com mais de 15 dias e pendentes
    df_filtro = df[(df["Tempo na Contadoria"] > 15) & (df["Cumprimento"].str.lower() == "pendente")]

    # Filtrar processos com mais de 15 dias com calculista e pendentes
    df_filtro_calculista = df[(df["Tempo na Contadoria"] > 30) & (df["Cumprimento"].str.lower() == "pendente")]

    # Dividir entre com e sem calculista
    df_sem_calculista = df_filtro[df_filtro["Calculista"].isna()]
    df_com_calculista = df_filtro_calculista[df_filtro_calculista["Calculista"].notna()]

    # Criar DataFrame com total de processos
    df_total = pd.DataFrame({
        "Total": [len(df_sem_calculista), len(df_com_calculista)]
    }, index=["Sem Calculista", "Sem_Calculo"])

    # Salvar em BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_sem_calculista.to_excel(writer, sheet_name="Sem Calculista", index=False)
        df_filtro_calculista.to_excel(writer, sheet_name="Sem_Calculo", index=False)
        df_total.to_excel(writer, sheet_name="Resumo", index=True)
    
    output.seek(0)  # Voltar ao início do arquivo
    
    return output, len(df_sem_calculista), len(df_com_calculista)

# Interface no Streamlit
st.title("📊 Processo Alerta ⚠️ – Analise de processos parados")
st.write("O arquivo Consolidação é atualizado as 12h00 e as 00h00.")

if st.button("🔄 Processar Arquivo"):
    try:
        output, total_sem_calculista, total_com_calculista = processar_tabela(ARQUIVO_LOCAL)

        # Exibir resumo dos dados
        st.subheader("🔍 Resumo dos Processos")
        st.write(f"📌 **Total de processos com mais de 15 dias sem calculista:** {total_sem_calculista}")
        st.write(f"📌 **Total de processos atribuidos a mais de 15 dias:** {total_com_calculista}")

        # Botão para baixar o arquivo processado
        st.download_button(
            label="📥 Baixar Arquivo Processado",
            data=output,
            file_name="processos_filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
