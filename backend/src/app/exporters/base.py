import abc
from typing import Any, AsyncGenerator, Sequence

from sqlalchemy.engine.row import Row


class BaseExporter(abc.ABC):
    """Base interface for all exporters."""

    @abc.abstractmethod
    def export(self, rows_generator: AsyncGenerator[Sequence[Row], None]) -> Any:
        """
        Consumes an async generator of Row chunks and returns or yields the exported data.
        """
        pass
