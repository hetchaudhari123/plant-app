# ---- Stage 1: Build dependencies ----
FROM python:3.11.2-slim AS builder

# Set working directory
WORKDIR /app

# Upgrade pip, setuptools, wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and filter out unwanted packages
COPY requirements.txt .

# Filter out torch and pywin packages, then build wheels with a timeout
RUN grep -aiv -E 'pywin|torch|torchvision|torchaudio' requirements.txt > filtered_requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r filtered_requirements.txt --timeout=600

# ---- Stage 2: Final image ----
FROM python:3.11.2-slim

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU directly with a timeout
RUN pip install --no-cache-dir torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cpu --timeout=600

# Copy pre-built wheels from builder
COPY --from=builder /app/wheels /wheels

# Install dependencies from wheels and clean up in the same layer
RUN pip install --no-cache-dir /wheels/* --timeout=600 && \
    rm -rf /wheels ~/.cache/pip

# Copy source code
COPY . .

# Expose port
EXPOSE 8002

# Run Gunicorn + Uvicorn
# Create Prometheus multiprocess directory
RUN mkdir -p /tmp/prometheus_multiproc

CMD ["gunicorn","-k", "uvicorn.workers.UvicornWorker","main:app","--bind", "0.0.0.0:8002","--workers", "4","--access-logfile", "-","--error-logfile", "-","--log-level", "debug"]