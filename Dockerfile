FROM python:3.13.0-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos do projeto para o contêiner
COPY . /app

# Instalar o Poetry
RUN pip install poetry

# Instalar as dependências via Poetry
RUN poetry install --no-root

# Expor a porta para o Streamlit
EXPOSE 8080

# Rodar o Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

