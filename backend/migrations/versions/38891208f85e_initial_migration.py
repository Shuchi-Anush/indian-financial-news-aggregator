"""Initial migration

Revision ID: 38891208f85e
Revises:
Create Date: 2026-06-10 21:28:19.338529

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "38891208f85e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
