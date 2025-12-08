FROM python:3.11-slim

WORKDIR /app

# Copiar solo archivos necesarios (excluir package.json, etc.)
COPY requirements.txt .
COPY runtime.txt .
COPY api/ ./api/
COPY src/ ./src/
COPY pyproject.toml .
COPY nixpacks.toml .
COPY railway.toml .

# Instalar dependencias
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Exponer puerto
EXPOSE $PORT

# Comando de inicio
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8080"]

