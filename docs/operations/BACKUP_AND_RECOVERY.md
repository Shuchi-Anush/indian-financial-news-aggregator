# Backup and Recovery

## Strategy
As an aggregation platform, we do not author original content. The source of truth is external publishers. However, restoring the database prevents re-triggering thousands of HTTP requests across publishers.

### Database Backups (Logical Dumps)
We recommend daily logical backups of PostgreSQL.
```bash
# Execute backup
docker exec -t db_container_name pg_dumpall -c -U myuser > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql
```

## Recovery Procedures

### Restoring from Dump
**Symptom**: Data corruption or accidental `DROP TABLE` execution.
**Probable Root Causes**: Operator error or catastrophic storage failure.

**Debugging/Recovery Commands**:
1. Shut down the backend container to prevent new inserts from interfering with the restore:
   ```bash
   docker compose stop backend
   ```
2. Drop and recreate the database schema to ensure clean slate (or use `-c` clean flags with `pg_restore`).
3. Stream the dump back:
   ```bash
   cat dump_*.sql | docker exec -i db_container_name psql -U myuser -d mydb
   ```
4. Restart the backend container.
   ```bash
   docker compose start backend
   ```

### Migration Recovery
**Symptom**: An Alembic upgrade partially failed, leaving the `alembic_version` table out of sync with actual schema states.
**Recovery Procedures**:
Do NOT guess schema changes manually.
Use `alembic current` to identify the recognized state. If the state is broken, forcibly update `alembic_version` to the actual hash of the DB schema, then write a new migration. Alternatively, downgrade if possible.
