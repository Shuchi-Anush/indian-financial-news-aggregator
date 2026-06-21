import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
from app.db.session import get_db
from unittest.mock import AsyncMock, MagicMock

client = TestClient(app)

async def override_get_db():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

def test_admin_routes_require_auth():
    # Without auth
    response = client.get("/admin/pipeline/status")
    assert response.status_code in (401, 403)
    
    # With wrong auth
    response = client.get("/admin/pipeline/status", headers={"X-API-Key": "wrong"})
    assert response.status_code in (401, 403)

def test_admin_routes_with_valid_auth():
    settings = get_settings()
    response = client.get("/admin/pipeline/status", headers={"X-API-Key": settings.admin_api_key})
    assert response.status_code not in (401, 403)

