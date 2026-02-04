"""LLM client exports and factory."""

from __future__ import annotations

from aria.config import get_settings
from aria.core.llm.base import LLMClient, LLMResponse, Message, ModelRole
from aria.core.llm.ollama import OllamaClient
from aria.utils.logging import get_logger

logger = get_logger(__name__)

_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Return a singleton LLM client based on configuration."""
    global _llm_client  # noqa: PLW0603
    if _llm_client is not None:
        return _llm_client

    settings = get_settings().llm
    if settings.provider == "ollama":
        _llm_client = OllamaClient()
    elif settings.provider == "openai":
        from aria.core.llm.openai import OpenAIClient  # noqa: PLC0415

        _llm_client = OpenAIClient()
    else:
        msg = f"Unsupported LLM provider: {settings.provider}"
        raise ValueError(msg)

    logger.info("LLM client initialized", provider=settings.provider)
    return _llm_client


__all__ = [
    "LLMClient",
    "LLMResponse",
    "Message",
    "ModelRole",
    "get_llm_client",
]
