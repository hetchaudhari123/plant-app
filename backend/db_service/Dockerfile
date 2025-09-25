# ---- Stage 1: Build dependencies ----
FROM python:3.11.2-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# ---- Stage 2: Final image ----
FROM python:3.11.2-slim

# Set working directory
WORKDIR /app

# Install curl (and clean up cache to keep image small)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels from builder
COPY --from=builder /app/wheels /wheels

# Install dependencies from wheels + gunicorn
RUN pip install --no-cache /wheels/* && \
    pip install --no-cache gunicorn
# Copy source code
COPY . .

# Run Gunicorn + Uvicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8001", "--workers", "4"]
