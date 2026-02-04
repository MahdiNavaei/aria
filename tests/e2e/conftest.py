"""E2E test fixtures and configuration.

E2E tests require:
- ARIA_RUN_E2E=1 to run any E2E tests
- ARIA_RUN_REAL_E2E=1 to run tests with real LLM API calls (costs money)
- Docker services running for full integration tests

Run E2E tests:
    ARIA_RUN_E2E=1 pytest tests/e2e/ -v

Run with real LLM calls:
    ARIA_RUN_E2E=1 ARIA_RUN_REAL_E2E=1 pytest tests/e2e/ -v
"""

from __future__ import annotations

import os
import subprocess
import time

import pytest


@pytest.fixture(scope="session")
def e2e_enabled() -> bool:
    """Return True when E2E tests are explicitly enabled."""
    return os.getenv("ARIA_RUN_E2E", "").lower() in {"1", "true", "yes"}


@pytest.fixture(scope="session")
def real_e2e_enabled() -> bool:
    """Return True when real E2E tests (with actual API calls) are enabled."""
    return os.getenv("ARIA_RUN_REAL_E2E", "").lower() in {"1", "true", "yes"}


@pytest.fixture
def skip_if_not_e2e(e2e_enabled: bool) -> None:
    """Skip test if E2E is not enabled."""
    if not e2e_enabled:
        pytest.skip("E2E tests disabled. Set ARIA_RUN_E2E=1 to enable.")


@pytest.fixture
def skip_if_not_real_e2e(e2e_enabled: bool, real_e2e_enabled: bool) -> None:
    """Skip test if real E2E (with API calls) is not enabled."""
    if not e2e_enabled:
        pytest.skip("E2E tests disabled. Set ARIA_RUN_E2E=1 to enable.")
    if not real_e2e_enabled:
        pytest.skip("Real E2E tests disabled. Set ARIA_RUN_REAL_E2E=1 to enable.")


@pytest.fixture(scope="session")
def docker_services(e2e_enabled: bool):
    """Ensure Docker services are running for E2E tests.

    This starts the docker-compose services and waits for them to be ready.
    """
    if not e2e_enabled:
        pytest.skip("E2E tests disabled. Set ARIA_RUN_E2E=1 to enable.")

    # Check if docker is available
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            pytest.skip("Docker not available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("Docker not available")

    # Start services
    try:
        subprocess.run(
            ["docker", "compose", "up", "-d"],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Failed to start Docker services: {e}")
    except subprocess.TimeoutExpired:
        pytest.skip("Docker compose startup timed out")

    # Wait for services to be ready
    time.sleep(10)

    yield

    # Optionally stop services after tests (commented out to allow inspection)
    # subprocess.run(["docker", "compose", "down"], check=False)


@pytest.fixture
def api_url() -> str:
    """Get the API URL for testing."""
    return os.getenv("ARIA_API_URL", "http://localhost:8000")


@pytest.fixture
def ws_url() -> str:
    """Get the WebSocket URL for testing."""
    return os.getenv("ARIA_WS_URL", "ws://localhost:8000/ws")
