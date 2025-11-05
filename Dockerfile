# Etapa 1 — imagem base leve
FROM python:3.12-slim

# Define diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos essenciais
COPY ./cmd ./cmd
COPY ./internal ./internal
COPY ./scripts ./scripts
COPY ./data ./data
COPY ./monitor_websocket.html ./monitor_websocket.html
COPY requirements.txt ./requirements.txt

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Exponha a porta do servidor
EXPOSE 4000

# Comando padrão do container
CMD ["uvicorn", "cmd.main:app", "--host", "0.0.0.0", "--port", "4000", "--reload"]
