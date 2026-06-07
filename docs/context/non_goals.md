# Non-Goals

Things this project explicitly will NOT do. If someone proposes these, point them here.

## Architecture Non-Goals

- **Microservices** — this is a single-process monolith. No service mesh, no inter-service communication.
- **Event-driven architecture** — no message queues (Kafka, RabbitMQ, Redis Streams), no event sourcing, no CQRS.
- **Kubernetes** — Docker Compose on a single host. No Helm charts, no pod autoscaling.
- **Multi-database** — PostgreSQL only. No MongoDB "for articles" or Redis "for caching".
- **GraphQL** — REST API only. GraphQL adds complexity without corresponding value at this scale.

## Feature Non-Goals

- **User accounts / authentication** — no login, no user management, no RBAC. The API is open.
- **Real-time streaming** — no WebSocket feeds, no SSE. Batch collection only.
- **Sentiment analysis / NLP** — no AI-powered article classification, entity extraction, or sentiment scoring.
- **Full-text search engine** — no Elasticsearch or Solr. PostgreSQL `LIKE` / `to_tsvector` is sufficient.
- **Notification system** — no email alerts, no push notifications, no Slack integration.
- **Content scraping** — no headless browser scraping. RSS feeds and public APIs only (for now).
- **Multi-language support** — English-language Indian financial news only.
- **Historical backfill** — no archival scraping of past articles. We collect going forward.

## Process Non-Goals

- **Full CI/CD pipeline** — no automated deployment. Manual `docker compose up --build`.
- **Monitoring stack** — no Prometheus, Grafana, or alerting. Structured logs are sufficient.
- **Load testing** — not designed for high-concurrency. Demo-grade traffic only.
- **Mobile app** — the `frontend/mobile/` directory exists for future planning only.
- **Multi-tenant** — single instance, single dataset.
