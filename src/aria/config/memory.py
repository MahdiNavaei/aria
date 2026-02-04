"""Memory configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QdrantConfig(BaseModel):
    """Qdrant vector store configuration."""

    host: str = "localhost"
    port: int = 6333
    collection_name: str = "aria_memories"


class VectorStoreSettings(BaseModel):
    """Vector store settings for Mem0."""

    provider: str = "qdrant"
    config: QdrantConfig = Field(default_factory=QdrantConfig)


class EmbedderConfig(BaseModel):
    """Embedder configuration."""

    model_name: str = "PartAI/Tooka-SBERT-V2-Large"
    embedding_dims: int = 1024
    max_sequence_length: int = 512
    persian_support: bool = True


class EmbedderFallbackConfig(BaseModel):
    """Fallback embedder configuration."""

    provider: str = "sentence_transformers"
    model_name: str = "PartAI/Tooka-SBERT"


class EmbedderSettings(BaseModel):
    """Embedder settings wrapper."""

    provider: str = "sentence_transformers"
    config: EmbedderConfig = Field(default_factory=EmbedderConfig)
    fallback: EmbedderFallbackConfig | None = None


class LLMRuntimeConfig(BaseModel):
    """LLM runtime configuration for Mem0."""

    model: str = "aria-brain"
    temperature: float = 0.1


class LLMSettings(BaseModel):
    """LLM provider settings for Mem0."""

    provider: str = "ollama"
    config: LLMRuntimeConfig = Field(default_factory=LLMRuntimeConfig)


class Mem0Settings(BaseModel):
    """Mem0-specific settings."""

    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    embedder: EmbedderSettings = Field(default_factory=EmbedderSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


class WorkingTierConfig(BaseModel):
    """Working memory tier configuration."""

    backend: str = "redis"
    ttl: int = 3600
    max_items: int = 100


class EpisodicTierConfig(BaseModel):
    """Episodic memory tier configuration."""

    backend: str = "mem0"
    retention_days: int = 90


class SemanticTierConfig(BaseModel):
    """Semantic memory tier configuration."""

    backend: str = "mem0"
    retention_days: int = -1


class MemoryTiers(BaseModel):
    """Memory tier settings."""

    working: WorkingTierConfig = Field(default_factory=WorkingTierConfig)
    episodic: EpisodicTierConfig = Field(default_factory=EpisodicTierConfig)
    semantic: SemanticTierConfig = Field(default_factory=SemanticTierConfig)


class MemoryConfig(BaseModel):
    """Top-level memory configuration."""

    model_config = ConfigDict(extra="ignore")

    provider: str = "mem0"
    mem0: Mem0Settings = Field(default_factory=Mem0Settings)
    tiers: MemoryTiers = Field(default_factory=MemoryTiers)
