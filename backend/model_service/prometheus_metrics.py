from prometheus_client import (
    CollectorRegistry,
    multiprocess,
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from fastapi import Request
from fastapi.responses import Response
import time
import re

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)


REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

MODEL_PREDICTION_LATENCY = Histogram(
    "model_prediction_latency_seconds",
    "Time taken to process a prediction in the model service",
    ["model_name"],  # optional labels
)


MODEL_PREDICTIONS = Counter(
    "model_predictions_total", "Number of predictions processed", ["model_name"]
)

MODEL_PREDICTIONS_FAILED = Counter(
    "model_predictions_failed_total",
    "Number of failed predictions",  # rem
    ["model_name"],
)


PATH_PATTERNS = [
    (r"^/predict/[^/]+$", "/predict/{model_name}"),
    (r"^/models/alias/[^/]+$", "/models/alias/{alias}"),
    (r"^/models/[^/]+$", "/models/{model_id}"),
]


# -------------------------
# Middleware
# -------------------------
async def prometheus_middleware(request: Request, call_next):
    # Skip /metrics endpoint
    if request.url.path == "/metrics":
        return await call_next(request)

    # Start timer
    start_time = time.perf_counter()
    response = await call_next(request)
    resp_time = time.perf_counter() - start_time

    # Normalize dynamic paths to prevent high cardinality
    path = request.url.path
    for pattern, replacement in PATH_PATTERNS:
        if re.match(pattern, path):
            path = replacement
            break  # stop after first match

    # Update HTTP request metrics
    REQUEST_COUNT.labels(
        method=request.method, endpoint=path, status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(method=request.method, endpoint=path).observe(resp_time)

    return response


# -------------------------
# /metrics endpoint
# -------------------------
async def metrics_endpoint():
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
