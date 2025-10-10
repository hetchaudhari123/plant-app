# ---- Stage 1: Build dependencies ----
FROM python:3.11.2-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements and build wheels, filtering out pywin packages
COPY requirements.txt .

# Run pip wheel with an increased timeout of 60 seconds
RUN grep -a -iv 'pywin' requirements.txt > filtered_requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r filtered_requirements.txt --timeout=60

# ---- Stage 2: Final image ----
FROM python:3.11.2-slim

# Set working directory
WORKDIR /app

# Install curl (runtime dependency) and clean apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels from builder
COPY --from=builder /app/wheels /wheels

# Install dependencies from wheels + gunicorn
# Added timeout here for consistency, though it's less critical when installing from local files
RUN pip install --no-cache /wheels/* --timeout=600

# Copy source code
COPY . .

# Run Gunicorn + Uvicorn
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
# Create Prometheus multiprocess directory
RUN mkdir -p /tmp/prometheus_multiproc

# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-"]
CMD ["gunicorn","-k", "uvicorn.workers.UvicornWorker","main:app","--bind", "0.0.0.0:8000","--workers", "4","--access-logfile", "-","--error-logfile", "-","--log-level", "debug"]
