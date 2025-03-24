# Use uma imagem base com Python
FROM python:latest

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos para o contêiner
COPY pyproject.toml poetry.lock ./

# Instala o Poetry
RUN pip install poetry

# Instala as dependências do projeto
RUN poetry install --no-root

# Copia o restante dos arquivos
COPY . .

# Define o comando padrão para rodar o Streamlit
CMD ["poetry", "run", "streamlit", "run", "app.py"]
