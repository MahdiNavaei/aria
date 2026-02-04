"""Ollama LLM client implementation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ollama import AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from aria.config import get_settings
from aria.core.llm.base import LLMClient, LLMResponse, Message, ModelRole
from aria.core.memory import get_embedder
from aria.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaClient(LLMClient):
    """Ollama LLM client with basic retry and rate limiting."""

    def __init__(self) -> None:
        """Initialize Ollama client."""
        settings = get_settings().llm
        self._settings = settings
        self._base_url = settings.ollama.base_url or settings.base_url
        self._client = AsyncClient(host=self._base_url)
        self._semaphore = asyncio.Semaphore(4)

    def _get_model(self, role: ModelRole) -> str:
        """Get model name for given role."""
        models = self._settings.ollama.models
        role_map = {
            ModelRole.BRAIN: models.brain,
            ModelRole.BRAIN_PERSIAN: models.brain_persian,
            ModelRole.BRAIN_PERSIAN_REASONING: models.brain_persian_reasoning,
            ModelRole.CODER: models.coder,
            ModelRole.EYE: models.eye,
            ModelRole.ML: models.embedding or models.ml,
            ModelRole.AUDIO: models.audio,
        }
        model = role_map.get(role) or self._settings.model_name

        legacy_role = self._settings.roles.get(role.value)
        if legacy_role and legacy_role.model_name:
            model = legacy_role.model_name

        return model

    def _resolve_options(
        self,
        role: ModelRole,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Resolve Ollama options for given role."""
        options = self._settings.ollama.options.model_dump(exclude_none=True)
        options.update({"temperature": temperature, "num_predict": max_tokens})

        override = self._settings.ollama.model_options.get(role.value)
        if override:
            options.update(override.model_dump(exclude_none=True))

        legacy_role = self._settings.roles.get(role.value)
        if legacy_role:
            if legacy_role.temperature is not None:
                options["temperature"] = legacy_role.temperature
            if legacy_role.max_tokens is not None:
                options["num_predict"] = legacy_role.max_tokens

        return options

    async def generate(
        self,
        messages: list[Message],
        role: ModelRole = ModelRole.BRAIN,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,  # noqa: ANN401
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        model = self._get_model(role)
        options = self._resolve_options(role, temperature, max_tokens)

        ollama_messages = []
        for msg in messages:
            payload = {"role": msg.role, "content": msg.content}
            if msg.images:
                payload["images"] = msg.images
            ollama_messages.append(payload)

        retries = kwargs.get("retries", 2)
        async with self._semaphore:
            for attempt in range(retries + 1):
                try:
                    response = await self._client.chat(
                        model=model,
                        messages=ollama_messages,
                        options=options,
                    )
                    tokens_used = int(response.get("eval_count", 0))
                    finish_reason = response.get("done_reason") or "stop"
                    return LLMResponse(
                        content=response["message"]["content"],
                        model=model,
                        tokens_used=tokens_used,
                        finish_reason=finish_reason,
                    )
                except (ConnectionError, TimeoutError, ValueError) as exc:
                    if attempt >= retries:
                        logger.exception("Ollama request failed", model=model)
                        raise
                    delay = 0.5 * (attempt + 1)
                    logger.warning(
                        "Ollama request retry",
                        attempt=attempt + 1,
                        delay=delay,
                        model=model,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)

        msg = "Ollama request failed"
        raise RuntimeError(msg)

    async def generate_stream(
        self,
        messages: list[Message],
        role: ModelRole = ModelRole.BRAIN,
        **kwargs: Any,  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """Stream completion tokens from Ollama."""
        model = self._get_model(role)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        options = self._resolve_options(role, temperature, max_tokens)

        ollama_messages = []
        for msg in messages:
            payload = {"role": msg.role, "content": msg.content}
            if msg.images:
                payload["images"] = msg.images
            ollama_messages.append(payload)

        async with self._semaphore:
            async for chunk in self._client.chat(
                model=model,
                messages=ollama_messages,
                options=options,
                stream=True,
            ):
                content = chunk.get("message", {}).get("content")
                if content:
                    yield content

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text using Ollama or fallback."""
        model = self._get_model(ModelRole.ML)
        embedder = get_embedder()

        if model and "Tooka" in model:
            return embedder.embed_single(text)

        async with self._semaphore:
            try:
                response = await self._client.embeddings(model=model, prompt=text)
                return response.get("embedding", [])
            except (ConnectionError, TimeoutError, ValueError, KeyError) as exc:
                logger.warning(
                    "Ollama embeddings failed, using local embedder",
                    error=str(exc),
                )
                return embedder.embed_single(text)
