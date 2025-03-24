import os
import pandas as pd
import glob
from datetime import datetime

def transform_tempo_real(arquivo=None):
    """
    Processa um arquivo XLSX fornecido ou usa o mais recente disponível na pasta "data".
    """
    # Caminho da pasta onde os arquivos são armazenados
    data_folder = os.path.join(os.getcwd(), "data")
    os.makedirs(data_folder, exist_ok=True)  # Garante que a pasta exista
    
    # Se um arquivo foi fornecido, usamos ele, caso contrário, buscamos o mais recente
    if arquivo:
        file_path = arquivo
    else:
        list_of_files = glob.glob(os.path.join(data_folder, "*.xlsx"))
        if list_of_files:
            file_path = max(list_of_files, key=os.path.getctime)
        else:
            raise FileNotFoundError("Nenhum arquivo .xlsx encontrado na pasta de dados!")
    
    # Carregar a planilha e excluir a primeira linha
    df = pd.read_excel(file_path)
    
    # Selecionar colunas necessárias
    df_selected = df[['unidade_judiciaria', 'npu', 'data_entrada_tarefa_atual', 'dias_aguardando_tarefa', 
                      'prioridade', 'lista_prioridades', 'contadoria']]
    
    # Renomear colunas
    df_selected.columns = ['vara', 'processo', 'data', 'dias', 'prioridade', 'lista_prioridades', 'nucleo']
    df_selected = df_selected[['nucleo', 'processo', 'vara', 'data', 'dias', 'prioridade', 'lista_prioridades']]
    
    # Função para determinar a prioridade
    def determinar_prioridade(lista_prioridades):
        if pd.isna(lista_prioridades):
            return "Sem prioridade"
        prioridades = lista_prioridades.split(';')
        super_prioridades = ["Pessoa idosa (80+)", "Doença terminal", "Pessoa com deficiência", "Deficiente físico"]
        return "Super prioridade" if any(p.strip() in super_prioridades for p in prioridades) else "Prioridade Legal"
    
    df_selected['prioridades'] = df_selected['lista_prioridades'].apply(determinar_prioridade)
    df_selected = df_selected.drop(columns=['prioridade', 'lista_prioridades']).drop_duplicates(subset=['processo', 'data'])
    
    # Formatando a data
    def formatar_data(data):
        if pd.isna(data):
            return None
        primeira_data = data.split(',')[0].strip().replace("'", "")
        data_formatada = pd.to_datetime(primeira_data, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        return data_formatada.strftime('%d/%m/%Y') if data_formatada is not pd.NaT else None
    
    df_selected['data'] = df_selected['data'].apply(formatar_data)
    df_selected["dias"] = pd.to_numeric(df_selected["dias"], errors="coerce")
    df_selected = df_selected.dropna(subset=["dias"])  # Remove valores NaN na coluna "dias"


    print("TESTE")
    # Substituir nomes dos núcleos
    substituicoes = {
        **{f'{i}ª CONTADORIA DE CÁLCULOS JUDICIAIS': f'{i}ª CCJ' for i in range(1, 7)},
        **{f'{i}ª CONTADORIA DE CUSTAS': f'{i}ª CC' for i in range(1, 8)}
    }
    df_selected['nucleo'] = df_selected['nucleo'].replace(substituicoes)
    
    # Criar resumo
    quantidade_processos = df_selected['nucleo'].value_counts().reset_index()
    quantidade_processos.columns = ['nucleo', 'quantidade']
    quantidade_processos['data'] = datetime.now().strftime('%d/%m/%Y')
    
    # Criar e salvar o arquivo Excel
    output_path = 'final_tempo_real.xlsx'
    with pd.ExcelWriter(output_path) as writer:
        for nucleo in df_selected['nucleo'].unique():
            df_selected[df_selected['nucleo'] == nucleo].sort_values(by='dias').to_excel(writer, sheet_name=nucleo or "Sem_Nucleo", index=False)
        quantidade_processos.to_excel(writer, sheet_name='QUANTIDADE', index=False)
        df_selected.to_excel(writer, sheet_name='CONSOLIDADO', index=False)
    
    return output_path
