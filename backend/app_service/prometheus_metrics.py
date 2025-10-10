from fastapi import Request
from prometheus_client import (
    CollectorRegistry,
    multiprocess,
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi.responses import Response
import time

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

# -------------------------
# HTTP metrics
# -------------------------
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# -------------------------
# Business metrics
# -------------------------
SIGNUPS_DONE = Counter("signups_done_total", "Number of successful signups")
ACTIVE_SESSIONS = Gauge(
    "active_sessions", "Current number of active sessions"
)  # error here
LOGIN_SUCCESS = Counter("login_success_total", "Number of successful logins")
LOGINS_FAILED = Counter("logins_failed_total", "Number of failed logins")
PREDICTION_REQUESTS = Counter(
    "prediction_requests_total",
    "Total number of prediction requests received",
    ["model_name"],
)
PREDICTION_FAILED = Counter(
    "prediction_failed_total",
    "Total number of failed prediction requests received",
    ["model_name"],
)  # check rem
PREDICTION_LATENCY = Histogram(
    "prediction_latency_seconds", "Time spent on prediction", ["model_name"]
)
ACCOUNTS_DELETED = Counter(
    "accounts_deleted_total", "Total number of user accounts deleted"
)
# ...add other metrics here


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
    if path.startswith("/predict/"):
        # Replace anything after /predict/ with a placeholder
        path = "/predict/{model_name}"

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
