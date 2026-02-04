"""Kafka configuration models."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class TopicConfig(BaseModel):
    """Kafka topic configuration."""

    partitions: int = 1
    replication_factor: int = 1
    retention_ms: int | None = None


class KafkaConfig(BaseModel):
    """Kafka/Redpanda configuration."""

    bootstrap_servers: list[str] = Field(default_factory=lambda: ["localhost:9092"])
    topics: dict[str, TopicConfig] = Field(default_factory=dict)
    consumer_group: str = "aria-dev"
    auto_offset_reset: str = "earliest"

    @field_validator("bootstrap_servers", mode="before")
    @classmethod
    def _parse_bootstrap_servers(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
