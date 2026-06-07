# Service Template

Use this pattern when creating a new service class.

## File Location

`backend/src/app/services/{domain}_service.py`

## Template

```python
"""Service layer for {domain} operations."""

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.schemas.entity import EntityCreate, EntityRead, EntityFilter

log = structlog.get_logger()


class EntityService:
    """Handles all {domain} business logic and database access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, entity_id: uuid.UUID) -> Entity | None:
        result = await self.db.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, filters: EntityFilter) -> list[Entity]:
        query = select(Entity)
        # Apply filters...
        if filters.is_active is not None:
            query = query.where(Entity.is_active == filters.is_active)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: EntityCreate) -> Entity:
        entity = Entity(**data.model_dump())
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        log.info("entity_created", entity_id=str(entity.id))
        return entity
```

## Dependency Injection

```python
# In api/dependencies.py or inline in routes
from app.db.session import get_db

async def get_entity_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EntityService:
    return EntityService(db)
```

## Checklist

- [ ] File named `{domain}_service.py`
- [ ] Class receives `AsyncSession` in constructor
- [ ] Uses structlog with structured key-value logging
- [ ] Returns Pydantic schemas or ORM objects (routes handle serialization)
- [ ] No route-level concerns (no `Request`, no `Response` objects)
- [ ] Service re-exported from `services/__init__.py`
