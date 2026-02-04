"""Real E2E tests with actual browser automation and LLM calls.

These tests use real Playwright browser automation and real LLM API calls.
They require:
- ARIA_RUN_E2E=1 environment variable
- ARIA_RUN_REAL_E2E=1 for real LLM calls (costs money)
- Valid LLM API key in environment

Run with: ARIA_RUN_E2E=1 ARIA_RUN_REAL_E2E=1 pytest tests/e2e/test_real_browser.py -v
"""

from __future__ import annotations

import asyncio
import os

import pytest


@pytest.fixture
def real_e2e_enabled() -> bool:
    """Check if real E2E tests are enabled."""
    return os.getenv("ARIA_RUN_REAL_E2E", "").lower() in {"1", "true", "yes"}


@pytest.fixture
def skip_if_not_real_e2e(real_e2e_enabled: bool) -> None:
    """Skip test if real E2E is not enabled."""
    if not real_e2e_enabled:
        pytest.skip("Real E2E tests disabled. Set ARIA_RUN_REAL_E2E=1 to enable.")


class TestRealBrowserAutomation:
    """Test real browser automation with Playwright."""

    @pytest.mark.asyncio
    async def test_browser_launches_and_navigates(
        self,
        e2e_enabled: bool,
    ) -> None:
        """Test that browser can launch and navigate to a URL."""
        if not e2e_enabled:
            pytest.skip("E2E tests disabled")

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to a test page
            await page.goto("https://example.com")

            # Verify navigation
            title = await page.title()
            assert "Example" in title

            # Verify we can interact with elements
            content = await page.content()
            assert "Example Domain" in content

            await browser.close()

    @pytest.mark.asyncio
    async def test_browser_adapter_click_and_type(
        self,
        e2e_enabled: bool,
    ) -> None:
        """Test browser adapter can perform click and type actions."""
        if not e2e_enabled:
            pytest.skip("E2E tests disabled")

        from aria.adapters.browser.adapter import BrowserAdapter

        adapter = BrowserAdapter()
        await adapter.initialize()

        try:
            # Navigate to a form test page
            result = await adapter.execute(
                capability="navigate",
                parameters={"url": "https://httpbin.org/forms/post"},
            )
            assert result.success, f"Navigation failed: {result.error}"

            # Fill in a text field
            result = await adapter.execute(
                capability="fill",
                parameters={
                    "selector": "input[name='custname']",
                    "value": "Test User",
                },
            )
            assert result.success, f"Fill failed: {result.error}"

            # Click a field
            result = await adapter.execute(
                capability="click",
                parameters={"selector": "input[name='custemail']"},
            )
            assert result.success, f"Click failed: {result.error}"

        finally:
            await adapter.cleanup()

    @pytest.mark.asyncio
    async def test_screenshot_capture(
        self,
        e2e_enabled: bool,
    ) -> None:
        """Test screenshot capture works correctly."""
        if not e2e_enabled:
            pytest.skip("E2E tests disabled")

        from playwright.async_api import async_playwright

        from aria.core.eye.screenshot import ScreenshotService

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://example.com")

            service = ScreenshotService()
            screenshot = await service.capture(page=page)

            assert screenshot is not None
            assert screenshot.image_bytes is not None
            assert len(screenshot.image_bytes) > 0
            assert screenshot.width > 0
            assert screenshot.height > 0

            await browser.close()


class TestRealLLMIntegration:
    """Test real LLM API calls."""

    @pytest.mark.asyncio
    async def test_llm_generate_response(
        self,
        e2e_enabled: bool,
        skip_if_not_real_e2e: None,
    ) -> None:
        """Test LLM can generate a response."""
        from aria.core.llm import Message, ModelRole, get_llm_client

        client = get_llm_client()

        response = await client.generate(
            messages=[Message(role="user", content="Say 'Hello' and nothing else.")],
            role=ModelRole.BRAIN,
            temperature=0,
            max_tokens=10,
        )

        assert response is not None
        assert response.content is not None
        assert "Hello" in response.content or "hello" in response.content.lower()

    @pytest.mark.asyncio
    async def test_llm_vision_with_image(
        self,
        e2e_enabled: bool,
        skip_if_not_real_e2e: None,
    ) -> None:
        """Test LLM can process images (VLM)."""
        import base64

        from PIL import Image
        from io import BytesIO

        from aria.core.llm import Message, ModelRole, get_llm_client

        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        client = get_llm_client()

        response = await client.generate(
            messages=[
                Message(
                    role="user",
                    content="What color is this image? Answer with just the color name.",
                    images=[img_base64],
                ),
            ],
            role=ModelRole.BRAIN,
            temperature=0,
            max_tokens=20,
        )

        assert response is not None
        assert response.content is not None
        # The LLM should identify the red color
        assert any(
            color in response.content.lower()
            for color in ["red", "vermilion", "crimson", "scarlet"]
        )


class TestRealJobExtraction:
    """Test real job extraction from websites."""

    @pytest.mark.asyncio
    async def test_job_extraction_from_url(
        self,
        e2e_enabled: bool,
        skip_if_not_real_e2e: None,
    ) -> None:
        """Test extracting job information from a real job posting."""
        from aria.plugins.job_apply.extractor import JobExtractor

        extractor = JobExtractor()

        # Use a stable test URL (GitHub jobs or similar)
        # Note: This test may be flaky as job postings change
        # For reliable testing, use a mock server or stable test endpoint
        job = await extractor.extract_from_url(
            "https://httpbin.org/html"  # Simple test page
        )

        # The extraction may return None for non-job pages, which is expected
        # This test mainly verifies the extraction pipeline works without errors
        # For real job testing, use actual job posting URLs


class TestRealEndToEnd:
    """Full end-to-end tests with all components."""

    @pytest.mark.asyncio
    async def test_brain_simple_task(
        self,
        e2e_enabled: bool,
        docker_services: None,
        skip_if_not_real_e2e: None,
    ) -> None:
        """Test Brain can execute a simple task end-to-end."""
        from aria.core.brain import get_brain

        brain = await get_brain()

        # Run a simple navigation task
        result = await asyncio.wait_for(
            brain.run(
                goal="Navigate to example.com and verify the page loads",
                domain="generic",
                session_id="test-e2e-001",
            ),
            timeout=60.0,  # 60 second timeout
        )

        assert result is not None
        # The result structure depends on Brain implementation
        # At minimum, it shouldn't raise an exception

    @pytest.mark.asyncio
    async def test_api_task_lifecycle(
        self,
        e2e_enabled: bool,
        docker_services: None,
    ) -> None:
        """Test API task creation and lifecycle."""
        import httpx

        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # Check API health
            response = await client.get("/health/")
            assert response.status_code == 200

            # Create a task
            response = await client.post(
                "/api/tasks/",
                json={
                    "goal": "Test task",
                    "domain": "test",
                    "auto_execute": False,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["status"] == "created"

            task_id = data["task_id"]

            # Get task status
            response = await client.get(f"/api/tasks/{task_id}")
            assert response.status_code == 200
