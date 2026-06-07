# API Route Template

Use this pattern when creating a new route module.

## File Location

`backend/src/app/api/routes/{domain}.py`

## Template

```python
"""API routes for {domain}."""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.common import PaginatedResponse
from app.services.entity_service import EntityService

router = APIRouter(prefix="/{domain}", tags=["{domain}"])


async def get_entity_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EntityService:
    return EntityService(db)


@router.get("", response_model=PaginatedResponse[EntityRead])
async def list_entities(
    service: Annotated[EntityService, Depends(get_entity_service)],
):
    """List all entities."""
    return await service.get_all()


@router.get("/{entity_id}", response_model=EntityRead)
async def get_entity(
    entity_id: uuid.UUID,
    service: Annotated[EntityService, Depends(get_entity_service)],
):
    """Get a single entity by ID."""
    entity = await service.get_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return entity


@router.post("", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    data: EntityCreate,
    service: Annotated[EntityService, Depends(get_entity_service)],
):
    """Create a new entity."""
    return await service.create(data)
```

## Registration

Add to `api/__init__.py`:
```python
from app.api.routes.entity import router as entity_router
v1_router.include_router(entity_router)
```

## Checklist

- [ ] File named `{domain}.py` (plural entity name)
- [ ] Router with `prefix` and `tags`
- [ ] All logic delegated to service — route body is 3-5 lines
- [ ] `response_model` declared on every route
- [ ] `Annotated[Service, Depends()]` for dependency injection
- [ ] Docstrings on every route handler (feeds OpenAPI docs)
- [ ] Router registered in `api/__init__.py`
