"""Prometheus-compatible real-time operational metrics.

Replaces DB-backed mock metrics with true runtime telemetry using
prometheus_client. Counters, Gauges, and Histograms are defined here
and exposed via the /metrics endpoint.
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# --- Ingestion Metrics ---
PIPELINE_RUNS_TOTAL = Counter(
    "pipeline_runs_total", "Total number of pipeline ingestion runs executed"
)
ARTICLES_FETCHED_TOTAL = Counter(
    "articles_fetched_total", "Total number of raw articles fetched from sources"
)
ARTICLES_INGESTED_TOTAL = Counter(
    "articles_ingested_total",
    "Total number of articles successfully ingested and saved",
    ["source_slug"],
)
ARTICLES_DEDUPLICATED_TOTAL = Counter(
    "articles_deduplicated_total", "Total number of articles skipped as duplicates", ["source_slug"]
)
ARTICLES_FAILED_TOTAL = Counter(
    "articles_failed_total",
    "Total number of articles that failed processing",
    ["source_slug", "stage"],
)

# --- Source Health Metrics ---
SOURCE_HEALTH_FAILURES_TOTAL = Counter(
    "source_health_failures_total",
    "Total number of feed source fetch/parse failures",
    ["source_slug", "error_type"],
)
SOURCE_CIRCUIT_BREAKER_STATE = Gauge(
    "source_circuit_breaker_state",
    "Current state of the circuit breaker (0=Closed, 1=Half-Open, 2=Open)",
    ["source_slug"],
)

# --- Duration & Latency Metrics ---
PIPELINE_RUN_DURATION_SECONDS = Histogram(
    "pipeline_run_duration_seconds",
    "Duration of pipeline ingestion runs in seconds",
    buckets=(1.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0, float("inf")),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests to the FastAPI endpoints",
    ["method", "endpoint", "status_code"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
)
ANALYTICS_VIEWS_REFRESH_DURATION = Histogram(
    "analytics_views_refresh_duration_seconds",
    "Duration of materialized views refresh",
    buckets=(0.5, 1.0, 5.0, 10.0, 30.0, 60.0, float("inf")),
)

async def export_metrics() -> tuple[bytes, str]:
    """Generate Prometheus-formatted metrics."""
    # generate_latest is synchronous but very fast since it just formats memory registry
    data = generate_latest()
    return data, CONTENT_TYPE_LATEST

class RegistryWrapper:
    """Wrapper to maintain compatibility with existing registry.inc/observe calls."""
    
    def inc(self, metric_name: str, amount: int | float = 1, labels: dict[str, str] | None = None) -> None:
        metric = globals().get(metric_name.upper())
        if metric:
            if labels:
                metric.labels(**labels).inc(amount)
            else:
                metric.inc(amount)

    def observe(self, metric_name: str, value: int | float, labels: dict[str, str] | None = None) -> None:
        metric = globals().get(metric_name.upper())
        if metric:
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

    def set_gauge(self, metric_name: str, value: int | float, labels: dict[str, str] | None = None) -> None:
        metric = globals().get(metric_name.upper())
        if metric:
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

registry = RegistryWrapper()
