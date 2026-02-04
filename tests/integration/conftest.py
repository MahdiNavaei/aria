import asyncio
from collections.abc import AsyncIterator

import pytest
import redis.asyncio as redis
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from aria.adapters.kafka.event_bus import EventBus
from aria.adapters.kafka.topics import ensure_topics
from aria.adapters.redis.state_store import StateStore
from aria.config import get_settings


@pytest.fixture(scope="session")
async def kafka_ready() -> bool:
    settings = get_settings().kafka
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.bootstrap_servers)
    try:
        await asyncio.wait_for(admin.start(), timeout=3)
        await asyncio.wait_for(admin.list_topics(), timeout=3)
    except Exception:  # noqa: BLE001
        pytest.skip("Kafka is not available")
    finally:
        await admin.close()

    await ensure_topics()
    return True


@pytest.fixture(scope="session")
async def redis_ready() -> bool:
    settings = get_settings().redis
    client = redis.Redis(
        host=settings.host,
        port=settings.port,
        db=settings.db,
        password=settings.password,
        decode_responses=True,
    )
    try:
        await asyncio.wait_for(client.ping(), timeout=3)
    except Exception:  # noqa: BLE001
        pytest.skip("Redis is not available")
    finally:
        await client.aclose()
    return True


@pytest.fixture(scope="session")
async def test_topic(kafka_ready: bool) -> str:
    settings = get_settings().kafka
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.bootstrap_servers)
    try:
        await asyncio.wait_for(admin.start(), timeout=3)
        existing = await asyncio.wait_for(admin.list_topics(), timeout=3)
        if "test.topic.v1" not in existing:
            await asyncio.wait_for(
                admin.create_topics(
                    [
                        NewTopic(
                            name="test.topic.v1",
                            num_partitions=1,
                            replication_factor=1,
                        ),
                    ],
                ),
                timeout=3,
            )
    finally:
        await admin.close()
    return "test.topic.v1"


@pytest.fixture
async def event_bus(kafka_ready: bool) -> AsyncIterator[EventBus]:
    bus = EventBus()
    await bus.connect()
    try:
        yield bus
    finally:
        await bus.disconnect()


@pytest.fixture
async def state_store(redis_ready: bool) -> AsyncIterator[StateStore]:
    store = StateStore()
    await store.connect()
    try:
        yield store
    finally:
        await store.disconnect()
