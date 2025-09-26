# ---- Stage 1: Build wheels ----
FROM python:3.11.2-slim AS builder

WORKDIR /app

# Configure pip timeout (15 minutes = 900s)
ENV PIP_DEFAULT_TIMEOUT=900

# Install build deps (needed to compile some libs like scipy, lxml, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Upgrade pip + build wheels
RUN pip install --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- Stage 2: Final image ----
FROM python:3.11.2-slim

WORKDIR /app

# Configure pip timeout (15 minutes = 900s)
ENV PIP_DEFAULT_TIMEOUT=900

# Install only runtime deps (curl, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install them
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

EXPOSE 8002

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8002", "--workers", "4"]
