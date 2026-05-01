from __future__ import annotations

import logging
import time
import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.fintablo_client import FintabloClient, UpstreamServiceError
from app.logging_config import configure_logging
from app.schemas import HealthResponse
from app.security import verify_api_key, verify_client_ip

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("fintablo_proxy")

app = FastAPI(title="Fintablo Read-only Proxy", version="1.0.0")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "request_failed endpoint=%s status_code=500 duration_ms=%s request_id=%s",
            request.url.path,
            elapsed_ms,
            request_id,
        )
        raise

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request_complete endpoint=%s status_code=%s duration_ms=%s request_id=%s",
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    response.headers["X-Request-ID"] = request_id
    return response


def get_fintablo_client() -> FintabloClient:
    return FintabloClient()


ReadOnlyGuard = [Depends(verify_api_key), Depends(verify_client_ip)]


@app.exception_handler(UpstreamServiceError)
async def upstream_exception_handler(
    request: Request, exc: UpstreamServiceError
) -> JSONResponse:
    _ = (request, exc)
    return JSONResponse(
        status_code=502,
        content={"detail": "Upstream service error", "status_code": 502},
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/accounts", dependencies=ReadOnlyGuard)
async def accounts(
    client: Annotated[FintabloClient, Depends(get_fintablo_client)],
) -> Any:
    return await client.get_accounts()


@app.get("/transactions", dependencies=ReadOnlyGuard)
async def transactions(
    client: Annotated[FintabloClient, Depends(get_fintablo_client)],
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    account_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return await client.get_transactions(date_from, date_to, account_id, limit, offset)


@app.get("/balances", dependencies=ReadOnlyGuard)
async def balances(
    client: Annotated[FintabloClient, Depends(get_fintablo_client)],
    date: date | None = Query(default=None),
    account_id: str | None = Query(default=None),
) -> Any:
    return await client.get_balances(date, account_id)


@app.get("/cashflow", dependencies=ReadOnlyGuard)
async def cashflow(
    client: Annotated[FintabloClient, Depends(get_fintablo_client)],
    date_from: date = Query(...),
    date_to: date = Query(...),
) -> Any:
    return await client.get_cashflow(date_from, date_to)


@app.get("/categories", dependencies=ReadOnlyGuard)
async def categories(
    client: Annotated[FintabloClient, Depends(get_fintablo_client)],
) -> Any:
    return await client.get_categories()
