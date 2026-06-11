# Monitoring & Observability

This backend natively supports Prometheus monitoring.

## Endpoint Interpretation
The `/metrics` endpoint exposes several custom Prometheus gauges and counters generated via the `prometheus-client` package.

### Key Metrics
1. `pipeline_runs_total` (Counter): Indicates how many scheduled ingestion passes occurred.
2. `articles_ingested_total` (Counter): Measures absolute volume of successfully stored records.
3. `articles_deduplicated_total` (Counter): Measures hashes intercepted as duplicates. High rates indicate redundant fetch cadences.
4. `articles_failed_total` (Counter): Measures normalization drops or catastrophic parser failures.
5. `pipeline_run_duration_seconds` (Summary): The end-to-end execution time of the `run_ingestion_cycle`. If this starts pushing >300 seconds, the ingestion frequency overlaps.
6. `source_circuit_breaker_state_total` (Gauge): By `source_id` and `state`. Values are `open` or `closed`.

## Prometheus Integration Strategy
- **Scraping Configuration**: In your `prometheus.yml`, define a target pointing to `backend:8000/metrics` with a scrape interval of `15s`.
- **Grafana Preparation**: Use these metrics to plot "Circuit Breaker Status" (alerts if any gauge equals `OPEN`) and "Pipeline Duration Growth" to observe system degradation.

## Log Interpretation
We utilize `structlog` for predictable, searchable JSON logs.
- `pipeline_finished` keys contain `duration_sec`, `failed_sources`, `status`.
- Filter logs where `level=error` and `event=circuit_breaker_tripped` to detect banned URLs.
