# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

# Install uv compiler tool
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install system compilation packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies via uv
COPY pyproject.toml ./
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --no-cache -r requirements.txt --target /build/site-packages

# Stage 2: Runtime image
FROM python:3.13-slim AS runner

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /build/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /build/site-packages/bin /usr/local/bin

# Copy app code
COPY app/ ./app/

# Expose API runtime port
EXPOSE 8000

# Run FastAPI app via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
