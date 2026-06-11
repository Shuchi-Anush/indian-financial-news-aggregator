# Validation Methodology

The Indian Financial News Aggregator relies on aggressive validation rather than aspirational assertions.

## Validation Tiers
1. **Static Validation**: Syntax, imports, memory boundaries (`ruff`, `mypy`).
2. **Database Validation**: Isolation tests, deadlock tests (`test_db_validation.py`).
3. **Chaos Validation**: Pipeline resilience against malformed inputs (`test_ingestion_chaos.py`).
4. **API Brutalization**: Protocol boundary hardening (`test_api_brutalization.py`).

## Continuous Integration Workflow
All changes must pass:
```bash
uv run mypy .
uv run ruff check .
uv run pytest
```
If `pytest` hangs, it indicates a leaked async session or overlapping database transaction. 

## Expected Outputs
The pipeline is designed to gracefully degrade. Validation tests explicitly assert that the API remains reachable (returning HTTP 200/404/422) regardless of the background state of the DB or the ingestion loop.

## Operational Significance
A failing chaos test means an external publisher can crash our orchestrator. A failing API brutalization test means a scraper can OOM (Out-of-Memory) our FastAPI worker. Both are P0 release blockers.
