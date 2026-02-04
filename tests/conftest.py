import asyncio
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(".env.test")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_session_id():
    """Generate unique session ID for tests."""
    return f"test_{uuid.uuid4().hex[:8]}"
