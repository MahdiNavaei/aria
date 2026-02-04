"""CLI entry for initializing Kafka topics."""

import asyncio

from aria.adapters.kafka.init_topics import init_topics


if __name__ == "__main__":
    asyncio.run(init_topics())
