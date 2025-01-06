import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.main import app

client = TestClient(app)

TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="module", autouse=True)
def setup_cleanup_worker():
    # Create and assign a mock cleanup worker to the app state
    app.state.cleanup_worker = MagicMock()
    yield
    # Clean up after tests (if needed)
    del app.state.cleanup_worker


@pytest.mark.asyncio
async def test_update_cleanup_interval():
    response = client.put("/api/v1/schedule/interval/1")
    assert response.status_code == 200
    # Verify that `set_interval` was called with the correct value
    app.state.cleanup_worker.set_interval.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_update_cleanup_period():
    response = client.put("/api/v1/schedule/period/1")
    assert response.status_code == 200
    # Verify that `set_period` was called with the correct value
    app.state.cleanup_worker.set_period.assert_called_once_with(1)
