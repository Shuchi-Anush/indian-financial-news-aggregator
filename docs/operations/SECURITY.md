# Security Posture

## Principles
- **No Raw SQL**: All DB access goes through SQLAlchemy 2.0 `select()`, `insert()`, `update()`, enforcing parameterized queries natively.
- **Type Coercion**: Pydantic validates boundaries on all API inputs (e.g., limits, base64 cursors).

## Attack Vectors & Mitigations

### 1. SQL Injection
**Symptom**: Malformed cursor strings or search queries (`?q='; DROP TABLE`).
**Mitigation**: The `keyset_cursor` is Base64 decoded, validated as a Pydantic Model (UUID + DateTime), and injected as parameter bindings. The `q` query string relies strictly on `to_tsquery` parameterization. No raw string interpolation exists in the repository.

### 2. Export Memory Exhaustion (DDoS)
**Symptom**: Attacker requests `GET /articles/export/csv?limit=500000000`.
**Mitigation**: The router explicitly limits max bounds. Data is yielded as a `StreamingResponse`. The memory bound is firmly restricted to the chunk size of the database cursor, not the size of the request.

### 3. Malicious XML Payloads (Billion Laughs Attack)
**Symptom**: `RSSCollector` parses an XML feed heavily nested with entity expansions, draining host CPU/Memory.
**Mitigation**: `feedparser` relies on standard Python XML libraries which are heavily hardened against standard entity expansion attacks.

## Debugging Security Failures
If Pydantic denies a request, it throws an `HTTP 422`. This is logged automatically.
```bash
grep '422' /var/log/fastapi.log
```
Check if the requests originate from a single IP, indicating an enumeration or fuzzing attack.
