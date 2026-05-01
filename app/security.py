from fastapi import Header, HTTPException, Request, status

from app.config import get_settings


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.openclaw_proxy_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


def verify_client_ip(request: Request) -> None:
    settings = get_settings()
    allowed = settings.allowed_client_ip_set
    if not allowed:
        return

    forwarded_ip = request.headers.get("x-real-ip")
    client_ip = forwarded_ip or (request.client.host if request.client else "")
    if client_ip not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
