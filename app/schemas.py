from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class UpstreamErrorResponse(BaseModel):
    detail: str = "Upstream service error"
    status_code: int = 502
