# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --no-cache -r requirements.txt --target /build/site-packages

# Stage 2: Runtime image
FROM python:3.13-slim AS runner

WORKDIR /app

RUN groupadd --system --gid 10001 appgroup \
    && useradd --system --uid 10001 --gid appgroup --no-create-home appuser

COPY --from=builder /build/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /build/site-packages/bin /usr/local/bin

COPY backend/app/ ./app/
COPY backend/alembic.ini ./
COPY backend/migrations/ ./migrations/

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
