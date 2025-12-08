FROM python:3.11-slim

WORKDIR /app

# Copiar solo archivos necesarios (excluir package.json, node_modules, etc.)
COPY requirements.txt .
COPY runtime.txt .
COPY api/ ./api/
COPY src/ ./src/
COPY pyproject.toml .

# Instalar dependencias
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Exponer puerto (Railway inyecta $PORT como variable de entorno)
EXPOSE 8080

# Comando de inicio (Railway inyecta $PORT como variable de entorno)
# Usar shell form para que $PORT se expanda correctamente
CMD ["sh", "-c", "uvicorn api.index:app --host 0.0.0.0 --port ${PORT:-8080}"]

