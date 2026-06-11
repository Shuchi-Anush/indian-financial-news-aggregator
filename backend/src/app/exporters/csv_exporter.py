import csv
import io
from typing import AsyncGenerator, Sequence

from sqlalchemy.engine.row import Row

from app.exporters.base import BaseExporter


class CSVExporter(BaseExporter):
    """Streams rows as CSV in a memory-safe, chunked manner."""

    async def export(
        self, rows_generator: AsyncGenerator[Sequence[Row], None]
    ) -> AsyncGenerator[str, None]:
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        headers = ["id", "title", "source_name", "published_at", "author", "summary", "url"]
        writer.writerow(headers)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        async for chunk in rows_generator:
            for row in chunk:
                # We expect the repository to yield rows that contain the projected columns.
                # Specifically: id, title, source_name, published_at, author, summary, url
                # Some fields might be None.

                # We safely fetch fields using getattr because the row might not contain 'summary'
                # if the default list projection was used. Wait, for export, we need the summary!
                # I need to ensure the export projection includes summary.

                r_id = getattr(row, "id", "")
                title = getattr(row, "title", "")
                source_name = getattr(row, "source_name", "")

                pub = getattr(row, "published_at", None)
                pub_str = pub.isoformat() if pub else ""

                author = getattr(row, "author", "")
                summary = getattr(row, "summary", "")
                url = getattr(row, "url", "")

                writer.writerow(
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
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
