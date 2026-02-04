"""Kafka adapter for ARIA event bus."""

from aria.adapters.kafka.consumer import EventConsumer
from aria.adapters.kafka.event_bus import EventBus, get_event_bus
from aria.adapters.kafka.topics import (
    AGENT_COMMAND_TOPIC,
    AGENT_ERROR_TOPIC,
    AGENT_PLAN_TOPIC,
    DLQ_TOPIC,
    EYE_PERCEPTION_TOPIC,
    HAND_EXECUTION_TOPIC,
    HAND_OBSERVATION_TOPIC,
    HUMAN_ACTION_TOPIC,
    LEARNING_ARTIFACT_TOPIC,
    SESSION_LIFECYCLE_TOPIC,
    TOPIC_SPECS,
)

__all__ = [
    "AGENT_COMMAND_TOPIC",
    "AGENT_ERROR_TOPIC",
    "AGENT_PLAN_TOPIC",
    "DLQ_TOPIC",
    "EYE_PERCEPTION_TOPIC",
    "HAND_EXECUTION_TOPIC",
    "HAND_OBSERVATION_TOPIC",
    "HUMAN_ACTION_TOPIC",
    "LEARNING_ARTIFACT_TOPIC",
    "SESSION_LIFECYCLE_TOPIC",
    "TOPIC_SPECS",
    "EventBus",
    "EventConsumer",
    "get_event_bus",
]
