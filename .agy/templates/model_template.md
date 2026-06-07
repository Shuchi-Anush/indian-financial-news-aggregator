# Model Template

Use this pattern when creating a new SQLAlchemy ORM model.

## File Location

`backend/src/app/models/{entity_name}.py`

## Template

```python
"""ORM model for {EntityName}."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EntityName(TimestampMixin, Base):
    """Describe what this entity represents."""

    __tablename__ = "entity_names"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<EntityName(id={self.id}, name={self.name!r})>"
```

## Checklist

- [ ] File named `{entity_name}.py` (singular, snake_case)
- [ ] `__tablename__` is plural snake_case
- [ ] Uses `Mapped[]` + `mapped_column()` (SQLAlchemy 2.0 style)
- [ ] Inherits `TimestampMixin` for `created_at` / `updated_at`
- [ ] UUID primary key with `gen_random_uuid()` server default
- [ ] `__repr__` method for debugging
- [ ] Model re-exported from `models/__init__.py`
