import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("OPENCLAW_PROXY_API_KEY", "test-key")
os.environ.setdefault("FINTABLO_API_TOKEN", "test-token")
os.environ.setdefault("ALLOWED_CLIENT_IPS", "testclient")

from app.main import app, get_fintablo_client  # noqa: E402


class StubFintabloClient:
    async def get_accounts(self):
        return {"status": 200, "items": []}

    async def get_transactions(self, *args, **kwargs):
        return {"status": 200, "items": []}

    async def get_balances(self, *args, **kwargs):
        return {"status": 200, "items": []}

    async def get_cashflow(self, *args, **kwargs):
        return {"status": 200, "totals": {"income": 0, "outcome": 0, "transfer": 0}}

    async def get_categories(self):
        return {"status": 200, "items": []}


@pytest.fixture
def client():
    app.dependency_overrides[get_fintablo_client] = lambda: StubFintabloClient()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
