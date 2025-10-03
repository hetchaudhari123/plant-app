# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (only for wheels)
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends build-essential gcc g++ && \
#     rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements (split torch separately to control install)
COPY requirements_without_torch.txt .

# Build wheels for non-torch deps
RUN pip wheel --no-cache-dir --wheel-dir /wheels_others -r requirements_without_torch.txt

# ---- Stage 2: Final Image ----
FROM python:3.11-slim

WORKDIR /app

# Only minimal runtime deps (needed by torch for OpenMP support)
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends libgomp1 && \
#     rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU directly (lighter than building wheels)
RUN pip install --no-cache-dir torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cpu

# Copy wheels for other deps
COPY --from=builder /wheels_others /wheels_others

# Install remaining deps
RUN pip install --no-cache-dir /wheels_others/* && rm -rf /wheels_others ~/.cache/pip

# Copy app
COPY . .

EXPOSE 8002

# Use Gunicorn with Uvicorn workers
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8002", "--workers", "4"]
CMD gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT --workers 1
