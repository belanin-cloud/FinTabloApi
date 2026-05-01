from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.config import get_settings

FINTABLO_ENDPOINTS = {
    "accounts": "/v1/moneybag",
    "transactions": "/v1/transaction",
    "balances": "/v1/moneybag",
    "cashflow": "/v1/transaction",
    "categories": "/v1/category",
}


class UpstreamServiceError(Exception):
    """Raised when Fintablo is unavailable or returns an error."""


class FintabloClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.fintablo_base_url.rstrip("/")
        self.timeout = self.settings.request_timeout_seconds

    async def get(self, endpoint_key: str, params: dict[str, Any] | None = None) -> Any:
        endpoint = FINTABLO_ENDPOINTS[endpoint_key]
        headers = {"Authorization": f"Bearer {self.settings.fintablo_api_token}"}
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
            if response.status_code >= 400:
                raise UpstreamServiceError()
            return response.json()
        except (httpx.HTTPError, ValueError):
            raise UpstreamServiceError() from None

    async def get_accounts(self) -> Any:
        return await self.get("accounts")

    async def get_transactions(
        self,
        date_from: date | None,
        date_to: date | None,
        account_id: str | None,
        limit: int,
        offset: int,
    ) -> Any:
        page = (offset // limit) + 1
        params: dict[str, Any] = {"pageSize": limit, "page": page}
        if date_from:
            params["dateFrom"] = date_from.strftime("%d.%m.%Y")
        if date_to:
            params["dateTo"] = date_to.strftime("%d.%m.%Y")
        if account_id:
            params["moneybagId"] = account_id
        return await self.get("transactions", params=params)

    async def get_balances(self, account_id: str | None) -> Any:
        payload = await self.get("balances")
        if not account_id:
            return payload
        if not isinstance(payload, dict):
            return payload
        items = payload.get("items", [])
        filtered_items = [item for item in items if str(item.get("id")) == str(account_id)]
        payload["items"] = filtered_items
        return payload

    async def get_cashflow(self, date_from: date, date_to: date) -> Any:
        payload = await self.get(
            "cashflow",
            params={
                "dateFrom": date_from.strftime("%d.%m.%Y"),
                "dateTo": date_to.strftime("%d.%m.%Y"),
                "pageSize": 1000,
                "page": 1,
            },
        )
        items = payload.get("items", []) if isinstance(payload, dict) else []
        summary = {"income": 0.0, "outcome": 0.0, "transfer": 0.0}
        for item in items:
            group = item.get("group")
            value = float(item.get("value", 0))
            if group in summary:
                summary[group] += value

        return {
            "status": 200,
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
            "totals": summary,
            "itemsCount": len(items),
        }

    async def get_categories(self) -> Any:
        return await self.get("categories")
