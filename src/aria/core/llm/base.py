"""LLM client interfaces for ARIA."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class ModelRole(str, Enum):
    """Role determines which model to use."""

    BRAIN = "brain"
    BRAIN_PERSIAN = "brain_persian"
    BRAIN_PERSIAN_REASONING = "brain_persian_reasoning"
    EYE = "eye"
    ML = "ml"
    CODER = "coder"
    AUDIO = "audio"


class Message(BaseModel):
    """Chat message for LLMs."""

    role: str
    content: str
    images: list[str] | None = None


class LLMResponse(BaseModel):
    """Standard LLM response payload."""

    content: str
    model: str
    tokens_used: int = Field(default=0, ge=0)
    finish_reason: str = "stop"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        role: ModelRole = ModelRole.BRAIN,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,  # noqa: ANN401
    ) -> LLMResponse:
        """Generate a completion."""

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        role: ModelRole = ModelRole.BRAIN,
        **kwargs: Any,  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text."""

    async def generate_text(
        self,
        prompt: str,
        role: ModelRole = ModelRole.BRAIN,
        **kwargs: Any,  # noqa: ANN401
    ) -> str:
        """Generate text from a single prompt."""
        response = await self.generate([Message(role="user", content=prompt)], role=role, **kwargs)
        return response.content
