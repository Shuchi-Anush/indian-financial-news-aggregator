# ADR-001: Manual Pipeline Triggering

**Status:** Accepted  
**Date:** 2026-06-07  
**Context:** Pipeline runs need a triggering mechanism.

## Decision

Pipeline runs are triggered manually via `POST /api/v1/pipeline/run`. No built-in scheduler (APScheduler, background loops, etc.) in the initial phase.

## Rationale

- Simplest possible trigger mechanism — no scheduler state to manage
- Easy to test and debug (deterministic runs)
- External scheduling (cron, systemd timer, or manual curl) provides the same capability with zero application-level complexity
- Adding a scheduler later is additive — no need to design for it now

## Consequences

- Pipeline does not auto-collect on an interval
- Operators must configure external cron if automatic collection is needed
- Example cron: `*/30 * * * * curl -X POST http://localhost:8000/api/v1/pipeline/run`

## Alternatives Considered

1. **APScheduler** — adds dependency, scheduler state, shutdown handling complexity
2. **Background asyncio task** — risk of memory leaks, harder to monitor
3. **Celery** — massively over-engineered for a single-process monolith
