"""Centralized typed configuration loaded from environment variables.

A single `settings` instance is the source of truth for every runtime
parameter the backend / user-api consume. Eager validation on import means
misconfiguration (missing secret, invalid port) crashes the process at
startup rather than during a request.

The host-side orchestrator `start_all.py` keeps its own minimal `.env`
parser -- it runs before any container exists and only needs the secrets
it forwards to Kubernetes. This module is for code that runs *inside* the
backend container.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Persistence
    database_url: str = Field(
        ...,
        description="SQLAlchemy URL, e.g. postgresql+psycopg2://user:pass@host:5432/db",
    )

    # Auth -- min length protects against trivially weak HS256 keys.
    auth_secret: str = Field(
        ...,
        min_length=16,
        description="HS256 signing key shared by user-api and backend",
    )

    # Operational
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # IBKR TWS connection
    ibkr_host: str = Field(default="127.0.0.1")
    ibkr_port: int = Field(default=7496, ge=1, le=65535)


settings = Settings()
