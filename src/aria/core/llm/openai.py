"""OpenAI LLM client implementation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from aria.config import get_settings
from aria.core.llm.base import LLMClient, LLMResponse, Message, ModelRole
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient(LLMClient):
    """OpenAI client wrapper with basic retries."""

    def __init__(self) -> None:
        """Initialize OpenAI client."""
        settings = get_settings().llm
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url or None,
        )
        self._semaphore = asyncio.Semaphore(4)

    def _get_model(self, role: ModelRole) -> str:
        """Get model name for given role."""
        legacy_role = self._settings.roles.get(role.value)
        if legacy_role and legacy_role.model_name:
            return legacy_role.model_name
        return self._settings.model_name

    def _build_message_payload(self, msg: Message) -> dict[str, Any]:
        """Build OpenAI message payload with vision support.

        For messages with images, uses the multi-content format required
        by OpenAI's vision API (GPT-4 Vision, etc.).

        Args:
            msg: Message object potentially containing images

        Returns:
            OpenAI-compatible message dict

        """
        # If no images, use simple format
        if not msg.images:
            return {"role": msg.role, "content": msg.content}

        # Build multi-content format for vision
        content: list[dict[str, Any]] = []

        # Add text content first
        if msg.content:
            content.append({"type": "text", "text": msg.content})

        # Add images (base64 or URL)
        for image in msg.images:
            if image.startswith(("http://", "https://")):
                # URL-based image
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image},
                })
            else:
                # Base64-encoded image (assume PNG if no prefix)
                if image.startswith("data:"):
                    data_url = image
                else:
                    data_url = f"data:image/png;base64,{image}"
                content.append({
                    "type": "image_url",
                    "image_url": {"url": data_url},
                })

        return {"role": msg.role, "content": content}

    async def generate(
        self,
        messages: list[Message],
        role: ModelRole = ModelRole.BRAIN,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,  # noqa: ANN401
    ) -> LLMResponse:
        """Generate completion using OpenAI."""
        model = self._get_model(role)
        payload = [self._build_message_payload(msg) for msg in messages]

        retries = kwargs.get("retries", 2)
        async with self._semaphore:
            for attempt in range(retries + 1):
                try:
                    response = await self._client.chat.completions.create(
                        model=model,
                        messages=payload,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    choice = response.choices[0]
                    tokens = response.usage.total_tokens if response.usage else 0
                    return LLMResponse(
                        content=choice.message.content or "",
                        model=model,
                        tokens_used=tokens,
                        finish_reason=choice.finish_reason or "stop",
                    )
                except (ConnectionError, TimeoutError, ValueError) as exc:
                    if attempt >= retries:
                        logger.exception("OpenAI request failed", model=model)
                        raise
                    delay = 0.5 * (attempt + 1)
                    logger.warning(
                        "OpenAI request retry",
                        attempt=attempt + 1,
                        delay=delay,
                        model=model,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)

        msg = "OpenAI request failed"
        raise RuntimeError(msg)

    async def generate_stream(
        self,
        messages: list[Message],
        role: ModelRole = ModelRole.BRAIN,
        **kwargs: Any,  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """Stream completion tokens from OpenAI."""
        model = self._get_model(role)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        payload = [self._build_message_payload(msg) for msg in messages]

        async with self._semaphore:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=payload,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text using OpenAI."""
        model = self._get_model(ModelRole.ML)
        async with self._semaphore:
            response = await self._client.embeddings.create(model=model, input=text)
        return response.data[0].embedding
