from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="production", alias="APP_ENV")
    openclaw_proxy_api_key: str = Field(alias="OPENCLAW_PROXY_API_KEY")
    fintablo_api_token: str = Field(alias="FINTABLO_API_TOKEN")
    fintablo_base_url: str = Field(
        default="https://api.fintablo.ru",
        alias="FINTABLO_BASE_URL",
    )
    allowed_client_ips: str = Field(default="", alias="ALLOWED_CLIENT_IPS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    request_timeout_seconds: float = 15.0

    @property
    def allowed_client_ip_set(self) -> set[str]:
        return {ip.strip() for ip in self.allowed_client_ips.split(",") if ip.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
