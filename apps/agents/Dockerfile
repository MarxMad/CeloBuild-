FROM python:3.11-slim

WORKDIR /app

# Copiar solo archivos necesarios (excluir package.json, etc.)
COPY requirements.txt .
COPY api/ ./api/
COPY src/ ./src/
COPY pyproject.toml .

# Instalar dependencias
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Exponer puerto (Railway usa variable $PORT)
EXPOSE 8080

# Comando de inicio (Railway inyecta $PORT como variable de entorno)
CMD uvicorn api.index:app --host 0.0.0.0 --port ${PORT:-8080}

