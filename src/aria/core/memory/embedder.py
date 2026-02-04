"""Persian embedding utilities for ARIA memory.

Optimized for speed with:
- GPU acceleration (CUDA)
- Batch processing
- Model caching
- FP16 precision
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    import numpy as np

from aria.utils.logging import get_logger

logger = get_logger(__name__)


class PersianEmbedder:
    """Persian text embeddings using Tooka-SBERT-V2-Large.
    
    Optimizations:
    - GPU acceleration when available
    - FP16 precision for faster inference
    - Batch processing for multiple texts
    - LRU cache for repeated queries
    """

    def __init__(
        self,
        model_name: str = "PartAI/Tooka-SBERT-V2-Large",
        fallback_model: str = "PartAI/Tooka-SBERT",
        dimensions: int = 1024,
        *,
        use_gpu: bool = True,
        use_fp16: bool = True,
    ) -> None:
        """Initialize Persian embedder with Tooka-SBERT model."""
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.dimensions = dimensions
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.use_fp16 = use_fp16 and self.use_gpu
        self._model = None
        self._loaded = False
        self._cache: dict[str, list[float]] = {}

    def load(self) -> None:
        """Load the embedder model (lazy)."""
        if self._loaded:
            return

        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        device = "cuda" if self.use_gpu else "cpu"

        try:
            logger.info("Loading embedder", model_name=self.model_name, device=device)
            self._model = SentenceTransformer(
                self.model_name,
                device=device,
            )
            # Enable FP16 for faster inference on GPU
            if self.use_fp16:
                self._model.half()
            self._loaded = True
            logger.info("Embedder loaded", model_name=self.model_name, device=device)
        except (OSError, ValueError, ImportError) as exc:
            logger.warning("Embedder load failed, using fallback", error=str(exc))
            self._model = SentenceTransformer(self.fallback_model, device=device)
            if self.use_fp16:
                self._model.half()
            self._loaded = True
            logger.info("Embedder loaded", model_name=self.fallback_model, device=device)

    def unload(self) -> None:
        """Unload the model to free memory."""
        self._model = None
        self._loaded = False

    def embed(self, texts: str | list[str], *, normalize: bool = True) -> np.ndarray:
        """Generate embeddings for a text or list of texts."""
        import numpy as np  # noqa: PLC0415, F401

        self.load()
        if isinstance(texts, str):
            texts = [texts]

        return self._model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )

    def embed_single(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        return self.embed(text)[0].tolist()

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        from sentence_transformers.util import cos_sim  # noqa: PLC0415

        emb1 = self.embed(text1)
        emb2 = self.embed(text2)
        return float(cos_sim(emb1, emb2)[0][0])

    def find_most_similar(
        self,
        query: str,
        candidates: list[str],
        top_k: int = 5,
    ) -> list[tuple[int, str, float]]:
        """Find the most similar candidates for a query."""
        from sentence_transformers.util import cos_sim  # noqa: PLC0415

        query_emb = self.embed(query)
        candidate_embs = self.embed(candidates)
        scores = cos_sim(query_emb, candidate_embs)[0]

        indices = scores.argsort(descending=True)[:top_k]
        return [(int(idx), candidates[idx], float(scores[idx])) for idx in indices]


_embedder_instance: PersianEmbedder | None = None


def get_embedder() -> PersianEmbedder:
    """Return a singleton embedder instance."""
    global _embedder_instance  # noqa: PLW0603
    if _embedder_instance is None:
        _embedder_instance = PersianEmbedder()
    return _embedder_instance
