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
    
     # Carregar a planilha e excluir a primeira linha
    df = pd.read_excel(file_path)

    # Verificar o número de colunas no DataFrame
    num_colunas = df.shape[1]
    print(f"Número de colunas no DataFrame: {num_colunas}")

    #selecionar colunas 

    df_selected = df[['unidade_judiciaria', 'npu', 'data_entrada_tarefa_atual', 'dias_aguardando_tarefa', 
                    'prioridade', 'lista_prioridades', 'contadoria']]

   


    # Renomear as colunas e reorganizar a ordem
    novas = ['vara', 'processo', 'data', 'dias', 'prioridade', 'lista_prioridades', 'nucleo']
    df_selected.columns = novas[:len(df_selected.columns)]
    df_selected = df_selected[['nucleo','processo', 'vara', 'data', 'dias', 'prioridade', 'lista_prioridades']]

    
    # Função para determinar a prioridade
    def determinar_prioridade(lista_prioridades):
        if pd.isna(lista_prioridades):
            return "Sem prioridade"
        prioridades = lista_prioridades.split(';')
        super_prioridades = ["Pessoa idosa (80+)", "Doença terminal", "Pessoa com deficiência", "Deficiente físico"]
        for prioridade in prioridades:
            if prioridade.strip() in super_prioridades:
                return "Super prioridade"
        return "Prioridade Legal"

    # Criar a nova coluna 'prioridades'
    df_selected['prioridades'] = df_selected['lista_prioridades'].apply(determinar_prioridade)

    df_selected = df_selected.drop(columns=['prioridade','lista_prioridades'])

    df_selected = df_selected.drop_duplicates(subset=['processo', 'data'])

    
    df_selected = df_selected[["nucleo","processo","vara","data","prioridades","dias"]] # Reorganizar as colunas
    df_selected =df_selected.fillna("") # Preencher as celulas vazias com vazio

    # Retirar tudo depois da virgula da coluna dias
    df_selected["dias"] = df_selected["dias"].str.split(",").str[0]

    # Função para tratar a coluna de data
    def formatar_data(data):
        if pd.isna(data):
            return None
        primeira_data = data.split(',')[0].strip().replace("'","")
        data_formatada = pd.to_datetime(primeira_data, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if data_formatada is pd.NaT:
            return None
        return data_formatada.strftime('%d/%m/%Y')

    # Aplicar a função de formatação de data
    df_selected['data'] = df_selected['data'].apply(formatar_data)

    # Criar um dicionário com as substituições para Contadoria de Cálculos Judiciais
    substituicoes_ccj = {
        '1ª CONTADORIA DE CÁLCULOS JUDICIAIS': '1ª CCJ',
        '2ª CONTADORIA DE CÁLCULOS JUDICIAIS': '2ª CCJ',
        '3ª CONTADORIA DE CÁLCULOS JUDICIAIS': '3ª CCJ',
        '4ª CONTADORIA DE CÁLCULOS JUDICIAIS': '4ª CCJ',
        '5ª CONTADORIA DE CÁLCULOS JUDICIAIS': '5ª CCJ',
        '6ª CONTADORIA DE CÁLCULOS JUDICIAIS': '6ª CCJ'
    }

    # Criar um dicionário com as substituições para Contadoria de Custas
    substituicoes_cc = {
        '1ª CONTADORIA DE CUSTAS': '1ª CC',
        '2ª CONTADORIA DE CUSTAS': '2ª CC',
        '3ª CONTADORIA DE CUSTAS': '3ª CC',
        '4ª CONTADORIA DE CUSTAS': '4ª CC',
        '5ª CONTADORIA DE CUSTAS': '5ª CC',
        '6ª CONTADORIA DE CUSTAS': '6ª CC',
        '7ª CONTADORIA DE CUSTAS': '7ª CC'
    }

    # Combinar os dois dicionários
    todas_substituicoes = {**substituicoes_ccj, **substituicoes_cc}

    # Fazer as substituições
    df_selected['nucleo'] = df_selected['nucleo'].replace(todas_substituicoes)

    # Verificar o resultado
    print("\nValores únicos na coluna Núcleo após as substituições:")
    print(df_selected['nucleo'].unique())

    # Obter os núcleos únicos
    nucleos = sorted(df_selected['nucleo'].unique())

    # Calcular a quantidade de processos por núcleo
    quantidade_processos = df_selected['nucleo'].value_counts().reset_index()
    quantidade_processos.columns = ['nucleo', 'quantidade']
    quantidade_processos['data'] = datetime.now().strftime('%d/%m/%Y')
    quantidade_processos = quantidade_processos[['data', 'nucleo','quantidade']]

    # Criar e salvar o arquivo Excel
    output_path = 'final_tempo_real.xlsx'
    with pd.ExcelWriter(output_path) as writer:
        for nucleo in df_selected['nucleo'].unique():
            df_selected[df_selected['nucleo'] == nucleo].sort_values(by='dias').to_excel(writer, sheet_name=nucleo or "Sem_Nucleo", index=False)
        quantidade_processos.to_excel(writer, sheet_name='QUANTIDADE', index=False)
        df_selected.to_excel(writer, sheet_name='CONSOLIDADO', index=False)
    
    return output_path
