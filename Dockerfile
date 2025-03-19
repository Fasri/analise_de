FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Executar Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
