"""Kafka topic definitions for ARIA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from aria.config import KafkaConfig, get_settings
from aria.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = get_logger(__name__)

AGENT_COMMAND_TOPIC = "agent.command.v1"
AGENT_PLAN_TOPIC = "agent.plan.v1"
HAND_EXECUTION_TOPIC = "hand.execution.v1"
HAND_OBSERVATION_TOPIC = "hand.observation.v1"
EYE_PERCEPTION_TOPIC = "eye.perception.v1"
HUMAN_ACTION_TOPIC = "human.action.v1"
LEARNING_ARTIFACT_TOPIC = "learning.artifact.v1"
AGENT_ERROR_TOPIC = "agent.error.v1"
SESSION_LIFECYCLE_TOPIC = "session.lifecycle.v1"
DLQ_TOPIC = "dlq.v1"


@dataclass(frozen=True)
class TopicSpec:
    """Topic specification for initialization."""

    partitions: int
    replication_factor: int
    retention_ms: int | None = None


TOPIC_SPECS: dict[str, TopicSpec] = {
    AGENT_COMMAND_TOPIC: TopicSpec(partitions=1, replication_factor=1, retention_ms=604800000),
    AGENT_PLAN_TOPIC: TopicSpec(partitions=2, replication_factor=1, retention_ms=604800000),
    HAND_EXECUTION_TOPIC: TopicSpec(partitions=4, replication_factor=1, retention_ms=604800000),
    HAND_OBSERVATION_TOPIC: TopicSpec(partitions=4, replication_factor=1, retention_ms=2592000000),
    EYE_PERCEPTION_TOPIC: TopicSpec(partitions=2, replication_factor=1, retention_ms=604800000),
    HUMAN_ACTION_TOPIC: TopicSpec(partitions=2, replication_factor=1, retention_ms=2592000000),
    LEARNING_ARTIFACT_TOPIC: TopicSpec(partitions=2, replication_factor=1, retention_ms=-1),
    AGENT_ERROR_TOPIC: TopicSpec(partitions=1, replication_factor=1, retention_ms=2592000000),
    SESSION_LIFECYCLE_TOPIC: TopicSpec(partitions=2, replication_factor=1, retention_ms=604800000),
    DLQ_TOPIC: TopicSpec(partitions=1, replication_factor=1, retention_ms=2592000000),
}


def _topic_configs_from_settings(settings: KafkaConfig) -> dict[str, TopicSpec]:
    overrides: dict[str, TopicSpec] = {}
    for name, cfg in settings.topics.items():
        overrides[name] = TopicSpec(
            partitions=cfg.partitions,
            replication_factor=cfg.replication_factor,
            retention_ms=cfg.retention_ms,
        )
    return overrides


def resolve_topic_specs(settings: KafkaConfig | None = None) -> dict[str, TopicSpec]:
    """Resolve topic specs from defaults and config overrides."""
    settings = settings or get_settings().kafka
    overrides = _topic_configs_from_settings(settings)
    merged = dict(TOPIC_SPECS)
    merged.update(overrides)
    return merged


def build_new_topics(settings: KafkaConfig | None = None) -> list[NewTopic]:
    """Build NewTopic definitions from topic specs."""
    specs = resolve_topic_specs(settings)
    topics: list[NewTopic] = []
    for name, spec in specs.items():
        topic_configs = {}
        if spec.retention_ms is not None:
            topic_configs["retention.ms"] = str(spec.retention_ms)
        topics.append(
            NewTopic(
                name=name,
                num_partitions=spec.partitions,
                replication_factor=spec.replication_factor,
                topic_configs=topic_configs,
            ),
        )
    return topics


async def ensure_topics(existing_topics: Iterable[str] | None = None) -> list[str]:
    """Ensure Kafka topics exist and create missing ones."""
    settings = get_settings().kafka
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.bootstrap_servers)
    created: list[str] = []
    await admin.start()
    try:
        existing = set(existing_topics or await admin.list_topics())
        new_topics = build_new_topics(settings)
        topics_to_create = [t for t in new_topics if t.name not in existing]
        if topics_to_create:
            await admin.create_topics(topics_to_create)
            created = [topic.name for topic in topics_to_create]
            logger.info("Kafka topics created", topics=created)
        else:
            logger.info("Kafka topics already exist")
    finally:
        await admin.close()
    return created
