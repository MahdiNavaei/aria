"""LLM Model Warmup Service - Preload ALL models to eliminate cold start.

Preloads:
- Ollama models (LLM, VLM)
- Embedding model (Tooka-SBERT)
- STT model (whisper-persian) - optional
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

import httpx

from aria.utils.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Ollama models to preload (in order of priority)
PRELOAD_OLLAMA_MODELS = [
    "aria-persian-chat",  # Primary chat model
    "aria-brain",         # Planning model
]

OLLAMA_BASE_URL = "http://localhost:11434"


def warmup_embedding_model() -> bool:
    """Preload Tooka-SBERT embedding model.
    
    Returns:
        True if loaded successfully
    """
    start = time.time()
    logger.info("🔥 Warming up embedding model (Tooka-SBERT)")
    
    try:
        from aria.core.memory import get_embedder  # noqa: PLC0415
        
        embedder = get_embedder()
        embedder.load()
        
        # Do a test embedding to ensure it's fully loaded
        _ = embedder.embed_single("test")
        
        elapsed = time.time() - start
        logger.info(f"✅ Embedding model warmed up in {elapsed:.1f}s")
        return True
        
    except Exception as e:  # noqa: BLE001
        logger.error(f"❌ Failed to warm up embedding model: {e}")
        return False


def warmup_stt_model() -> bool:
    """Preload whisper-persian STT model (optional).
    
    Returns:
        True if loaded successfully
    """
    start = time.time()
    logger.info("🔥 Warming up STT model (whisper-persian)")
    
    try:
        from aria.core.voice.stt import get_stt  # noqa: PLC0415
        
        stt = get_stt()
        stt.load()
        
        elapsed = time.time() - start
        logger.info(f"✅ STT model warmed up in {elapsed:.1f}s")
        return True
        
    except Exception as e:  # noqa: BLE001
        logger.warning(f"⚠️ STT model warmup skipped: {e}")
        return False


async def warmup_model(model: str, timeout: float = 120.0) -> bool:
    """Preload a single model into memory.
    
    Args:
        model: Model name to preload
        timeout: Maximum time to wait for model to load
        
    Returns:
        True if model was loaded successfully
    """
    start = time.time()
    logger.info(f"🔥 Warming up model: {model}")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Send a minimal request to load the model
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": "hi",
                    "stream": False,
                    "options": {
                        "num_predict": 1,  # Generate only 1 token (fast)
                    },
                    "keep_alive": -1,  # Keep loaded forever
                },
            )
            
            if response.status_code == 200:
                elapsed = time.time() - start
                logger.info(f"✅ Model {model} warmed up in {elapsed:.1f}s")
                return True
            else:
                logger.error(f"❌ Failed to warm up {model}: {response.status_code}")
                return False
                
    except httpx.TimeoutException:
        logger.error(f"❌ Timeout warming up {model}")
        return False
    except httpx.ConnectError:
        logger.error(f"❌ Cannot connect to Ollama for {model}")
        return False
    except Exception as e:
        logger.error(f"❌ Error warming up {model}: {e}")
        return False


async def warmup_all_models(
    ollama_models: list[str] | None = None,
    *,
    include_embedding: bool = True,
    include_stt: bool = False,
) -> dict[str, bool]:
    """Preload all models into memory.
    
    Args:
        ollama_models: List of Ollama models. Defaults to PRELOAD_OLLAMA_MODELS.
        include_embedding: Preload embedding model (recommended).
        include_stt: Preload STT model (optional, takes more memory).
        
    Returns:
        Dict mapping model name to success status
    """
    if ollama_models is None:
        ollama_models = PRELOAD_OLLAMA_MODELS
    
    total_models = len(ollama_models) + int(include_embedding) + int(include_stt)
    logger.info(f"🚀 Starting warmup for {total_models} models...")
    start = time.time()
    
    results = {}
    
    # 1. Ollama models
    for model in ollama_models:
        results[model] = await warmup_model(model)
    
    # 2. Embedding model
    if include_embedding:
        results["tooka-sbert"] = warmup_embedding_model()
    
    # 3. STT model (optional)
    if include_stt:
        results["whisper-persian"] = warmup_stt_model()
    
    elapsed = time.time() - start
    success = sum(results.values())
    logger.info(f"🏁 Warmup complete: {success}/{total_models} models in {elapsed:.1f}s")
    
    return results


def warmup_sync(
    ollama_models: list[str] | None = None,
    *,
    include_embedding: bool = True,
    include_stt: bool = False,
) -> dict[str, bool]:
    """Synchronous wrapper for warmup_all_models."""
    return asyncio.run(warmup_all_models(
        ollama_models,
        include_embedding=include_embedding,
        include_stt=include_stt,
    ))


async def check_model_loaded(model: str) -> bool:
    """Check if a model is currently loaded in memory.
    
    Args:
        model: Model name to check
        
    Returns:
        True if model is loaded
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/ps")
            if response.status_code == 200:
                data = response.json()
                loaded_models = [m.get("name", "") for m in data.get("models", [])]
                return any(model in m for m in loaded_models)
    except Exception:
        pass
    return False


async def ensure_model_loaded(model: str) -> bool:
    """Ensure a model is loaded, warming it up if necessary.
    
    Args:
        model: Model name to ensure is loaded
        
    Returns:
        True if model is now loaded
    """
    if await check_model_loaded(model):
        logger.debug(f"Model {model} already loaded")
        return True
    
    return await warmup_model(model)


# CLI interface
if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("ARIA Model Warmup Service")
    print("=" * 50)
    
    # Parse arguments
    include_stt = "--stt" in sys.argv
    models = [m for m in sys.argv[1:] if not m.startswith("--")] or None
    
    print(f"\nPreloading:")
    print(f"  - Ollama models: {models or PRELOAD_OLLAMA_MODELS}")
    print(f"  - Embedding: Yes")
    print(f"  - STT: {'Yes' if include_stt else 'No (use --stt to enable)'}")
    print()
    
    results = warmup_sync(models, include_embedding=True, include_stt=include_stt)
    
    print("\n" + "=" * 50)
    print("Results:")
    for model, success in results.items():
        status = "Loaded" if success else "Failed"
        print(f"  {model}: {status}")
    print("=" * 50)
