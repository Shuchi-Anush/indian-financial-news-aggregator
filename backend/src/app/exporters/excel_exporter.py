import os
import tempfile
import uuid
from typing import AsyncGenerator, Sequence

import openpyxl  # type: ignore
from sqlalchemy.engine.row import Row

from app.exporters.base import BaseExporter


class ExcelExporter(BaseExporter):
    """Writes rows to an Excel workbook safely and yields the file path."""

    async def export(self, rows_generator: AsyncGenerator[Sequence[Row], None]) -> str:
        # Create a write-only workbook for memory safety
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet(title="Articles")

        headers = ["id", "title", "source_name", "published_at", "author", "summary", "url"]
        ws.append(headers)

        # We cannot easily auto-size columns or freeze panes in write_only mode with openpyxl
        # but we can do some basic optimizations. Write_only mode is required to prevent memory spikes.

        async for chunk in rows_generator:
            for row in chunk:
                r_id = getattr(row, "id", "")
                title = getattr(row, "title", "")
                source_name = getattr(row, "source_name", "")

                pub = getattr(row, "published_at", None)
                pub_str = pub.isoformat() if pub else ""

                author = getattr(row, "author", "")
                summary = getattr(row, "summary", "")
                url = getattr(row, "url", "")

                ws.append(
                    [
                        str(r_id) if r_id else "",
                        title or "",
                        source_name or "",
                        pub_str,
                        author or "",
                        summary or "",
                        url or "",
                    ]
                )

        fd, path = tempfile.mkstemp(suffix=".xlsx", prefix=f"export_{uuid.uuid4().hex}_")
        os.close(fd)  # Close it so openpyxl can write
        wb.save(path)
        return path
