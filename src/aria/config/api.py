"""API configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CORSConfig(BaseModel):
    """CORS configuration."""

    enabled: bool = True
    origins: list[str] = Field(default_factory=list)


class WebSocketConfig(BaseModel):
    """WebSocket configuration."""

    ping_interval: int = 30
    max_connections: int = 100


class APIConfig(BaseModel):
    """Top-level API configuration."""

    model_config = ConfigDict(extra="ignore")

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    reload: bool = True
    cors: CORSConfig = Field(default_factory=CORSConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)
