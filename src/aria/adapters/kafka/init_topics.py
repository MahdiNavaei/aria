"""Kafka topic initialization utilities."""

from __future__ import annotations

from aiokafka.admin import AIOKafkaAdminClient

from aria.adapters.kafka.topics import build_new_topics
from aria.config import get_settings
from aria.utils.logging import get_logger

logger = get_logger(__name__)


async def init_topics() -> None:
    """Create required Kafka topics if they do not exist."""
    settings = get_settings().kafka
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.bootstrap_servers)

    await admin.start()
    try:
        existing = await admin.list_topics()
        new_topics = build_new_topics(settings)
        topics_to_create = [t for t in new_topics if t.name not in existing]
        if topics_to_create:
            await admin.create_topics(topics_to_create)
            logger.info("Topics created", topics=[t.name for t in topics_to_create])
        else:
            logger.info("All topics already exist")
    finally:
        await admin.close()


async def check_kafka_health() -> bool:
    """Check if Kafka is reachable."""
    settings = get_settings().kafka
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.bootstrap_servers)
    healthy = False
    try:
        await admin.start()
        await admin.list_topics()
    except OSError as exc:
        logger.exception("Kafka health check failed", error=str(exc))
    else:
        healthy = True
    finally:
        await admin.close()
    return healthy


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_topics())
