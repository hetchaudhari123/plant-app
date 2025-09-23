# Dockerfile for app_service
FROM python:3.11.2-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run Gunicorn + Uvicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app_service:app", "--bind", "0.0.0.0:8001", "--workers", "4"]
