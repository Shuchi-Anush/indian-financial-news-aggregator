# Migration Safety Rules

## Alembic Workflow
1. Use `uv run alembic revision --autogenerate`.
2. Inspect the output. **Alembic frequently hallucinates `drop_index` or misses Enum changes.**

## Enum Downgrades
If you alter an Enum column back to a VARCHAR, PostgreSQL will fail during downgrade unless explicit casting is provided.
**Forbidden**:
```python
op.alter_column('articles', 'sentiment', type_=sa.String(32))
```
**Required**:
```python
op.alter_column('articles', 'sentiment', type_=sa.String(32), postgresql_using='sentiment::sentimentlabel')
```

## Immutable History
Once a migration is merged into `main`, you cannot edit it. You must issue a new migration to patch the schema forward.
