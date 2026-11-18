# ==============================================================================
# Dockerfile Multi-Stage para RetailFlow E-Commerce (FastAPI)
# ==============================================================================

# Estágio 1: Builder (Compilação e resolução de dependências)
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# Estágio 2: Runtime (Imagem final enxuta e segura)
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Instalar dependências de sistema mínimas para execução e healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criação de usuário não-root por segurança
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copiar dependências instaladas do builder
COPY --from=builder /install /usr/local

# Copiar código da aplicação
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup scripts/ /app/scripts/
COPY --chown=appuser:appgroup migrations/ /app/migrations/
COPY --chown=appuser:appgroup alembic.ini /app/alembic.ini

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
