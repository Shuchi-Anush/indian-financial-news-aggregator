# Architecture Diagrams

## Ingestion Flow

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler
    participant Orchestrator as IngestionOrchestrator
    participant Collector as RSSCollector
    participant DB as PostgreSQL

    Scheduler->>Orchestrator: trigger run_ingestion_cycle()
    Orchestrator->>DB: pg_try_advisory_lock()
    alt Lock Acquired
        Orchestrator->>DB: create pipeline_run record
        Orchestrator->>Collector: collect(active_sources)
        Collector->>External: httpx.get(feed.url)
        External-->>Collector: XML payload
        Collector->>Orchestrator: List[CanonicalArticle]
        Orchestrator->>DB: ON CONFLICT DO NOTHING (batch insert)
        Orchestrator->>DB: REFRESH MATERIALIZED VIEW
        Orchestrator->>DB: update pipeline_run (status=SUCCESS)
        Orchestrator->>DB: pg_advisory_unlock()
    else Lock Failed
        Orchestrator-->>Scheduler: Abort (Another worker is processing)
    end
```

## Enrichment Lifecycle

```mermaid
flowchart TD
    Raw[Raw XML Item] --> Extract[Extract Title/Link/Date]
    Extract --> Canonicalize[Canonicalize URL]
    Canonicalize --> Hash[SHA-256 (Title+Body)]
    Hash --> Enrich[Regex Dictionary Scan]
    Enrich --> Match1{Keyword Match?}
    Match1 -- Yes --> Tag1[Assign Category/Sector]
    Match1 -- No --> Tag2[Assign 'OTHER']
    Enrich --> DB[Insert into articles table]
```

## Resilience Lifecycle (Circuit Breaker)

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> CLOSED : HTTP 200 (Success)
    CLOSED --> OPEN : HTTP 500 / Timeout > Threshold
    OPEN --> HALF_OPEN : Time elapsed
    HALF_OPEN --> CLOSED : HTTP 200 (Success)
    HALF_OPEN --> OPEN : HTTP 500 / Timeout
```
