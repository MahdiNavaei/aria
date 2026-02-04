"""Redis configuration models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RedisConfig(BaseModel):
    """Redis configuration for state and cache."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    ttl_defaults: dict[str, int] = Field(
        default_factory=lambda: {
            "session_state": 86400,
            "working_memory": 14400,
            "cache": 3600,
            "llm_cache": 900,
        },
    )
    key_prefixes: dict[str, str] = Field(
        default_factory=lambda: {
            "session": "session",
            "memory": "memory",
            "cache": "cache",
            "flag": "flag",
        },
    )
