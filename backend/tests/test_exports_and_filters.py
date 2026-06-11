import pytest
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from app.schemas.article_schemas import ArticleFilters
from app.utils.cursor import CursorEngine
from app.exporters.csv_exporter import CSVExporter
from app.exporters.excel_exporter import ExcelExporter

def test_article_filters_validation():
    # Test valid dates
    f = ArticleFilters(
        date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_to=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )
    assert f.published_after < f.published_before
    
    # Test invalid dates
    with pytest.raises(ValueError):
        ArticleFilters(
            date_from=datetime(2026, 1, 2, tzinfo=timezone.utc),
            date_to=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )

    # Test valid search
    f2 = ArticleFilters(q="market crash")
    assert f2.search == "market crash"
    
    # Test invalid search (too short)
    with pytest.raises(ValueError):
        ArticleFilters(q="a")

def test_cursor_engine():
    pub = datetime(2026, 6, 11, tzinfo=timezone.utc)
    u = uuid.uuid4()
    
    # Without rank
    encoded = CursorEngine.encode_cursor(pub, u)
    decoded = CursorEngine.decode_cursor(encoded)
    assert decoded["published_at"] == pub
    assert decoded["id"] == u
    assert decoded["rank"] is None
    
    # With rank
    encoded_rank = CursorEngine.encode_cursor(pub, u, 1.23)
    decoded_rank = CursorEngine.decode_cursor(encoded_rank)
    assert decoded_rank["rank"] == 1.23
    
    # Invalid
    with pytest.raises(Exception):
        CursorEngine.decode_cursor("invalid-base64-!")

class MockRow:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def __getattr__(self, name):
        return None

async def mock_rows_generator() -> AsyncGenerator[list[MockRow], None]:
    yield [
        MockRow(id=uuid.uuid4(), title="Test 1", source_name="ET", published_at=datetime(2026, 1, 1, tzinfo=timezone.utc), summary="Sum 1", author="A1", url="http://1"),
        MockRow(id=uuid.uuid4(), title="Test 2", source_name="MC", published_at=None, summary=None, author=None, url=None)
    ]

@pytest.mark.asyncio
async def test_csv_exporter():
    exporter = CSVExporter()
    gen = exporter.export(mock_rows_generator())
    
    results = []
    async for chunk in gen:
        results.append(chunk)
        
    full_csv = "".join(results)
    assert "id,title,source_name,published_at,author,summary,url" in full_csv
    assert "Test 1" in full_csv
    assert "Test 2" in full_csv

@pytest.mark.asyncio
async def test_excel_exporter():
    import os
    exporter = ExcelExporter()
    path = await exporter.export(mock_rows_generator())
    
    assert os.path.exists(path)
    assert path.endswith(".xlsx")
    os.remove(path)
