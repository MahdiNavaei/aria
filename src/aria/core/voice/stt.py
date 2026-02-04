"""Persian Speech-to-Text using whisper-persian-v4.

This model is safetensors-based and works with transformers (not Ollama).

Optimizations:
- GPU acceleration (CUDA)
- FP16 precision for 2x faster inference
- BetterTransformer for optimized attention
- Batch decoding
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# Whisper sample rate requirement
WHISPER_SAMPLE_RATE = 16000


class PersianSTT:
    """Persian Speech-to-Text engine using whisper-persian-v4.
    
    Optimizations applied:
    - CUDA acceleration when available
    - FP16 precision (2x faster on GPU)
    - Flash attention if available
    - Optimized generation parameters
    """

    def __init__(
        self,
        model_name: str = "nezamisafa/whisper-persian-v4",
        device: str | None = None,
        *,
        use_fp16: bool = True,
        use_flash_attention: bool = True,
    ) -> None:
        """Initialize the Persian STT engine.

        Args:
            model_name: HuggingFace model name.
            device: Device to use (cuda/cpu).
            use_fp16: Use FP16 precision on CUDA.
            use_flash_attention: Use Flash Attention 2 if available.

        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_fp16 = use_fp16 and self.device == "cuda"
        self.use_flash_attention = use_flash_attention and self.device == "cuda"

        self._processor = None
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Load model into memory (lazy loading) with optimizations."""
        if self._loaded:
            return

        logger.info("Loading STT model", extra={"model": self.model_name, "device": self.device})

        from transformers import (  # noqa: PLC0415
            WhisperForConditionalGeneration,
            WhisperProcessor,
        )

        self._processor = WhisperProcessor.from_pretrained(self.model_name)
        
        # Load with optimizations
        model_kwargs = {}
        if self.use_flash_attention:
            try:
                model_kwargs["attn_implementation"] = "flash_attention_2"
            except Exception:  # noqa: BLE001, S110
                pass  # Flash attention not available
        
        if self.use_fp16 and self.device == "cuda":
            model_kwargs["torch_dtype"] = torch.float16
        
        self._model = WhisperForConditionalGeneration.from_pretrained(
            self.model_name,
            **model_kwargs,
        )

        if self.device == "cuda":
            self._model = self._model.to("cuda")
        
        # Try to use BetterTransformer for faster inference
        try:
            self._model = self._model.to_bettertransformer()
            logger.info("BetterTransformer enabled for STT")
        except Exception:  # noqa: BLE001, S110
            pass  # BetterTransformer not available

        self._loaded = True
        logger.info("STT model loaded successfully")

    def unload(self) -> None:
        """Unload model to free memory."""
        self._model = None
        self._processor = None
        self._loaded = False

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def transcribe(
        self,
        audio_path: str | Path,
        *,
        language: str = "persian",
        return_timestamps: bool = False,
    ) -> str:
        """Transcribe an audio file to Persian text."""
        self.load()

        import librosa  # noqa: PLC0415

        audio, _ = librosa.load(str(audio_path), sr=WHISPER_SAMPLE_RATE)

        inputs = self._processor(
            audio,
            sampling_rate=WHISPER_SAMPLE_RATE,
            return_tensors="pt",
        )

        if self.device == "cuda":
            inputs = inputs.to("cuda")

        with torch.no_grad():
            generated_ids = self._model.generate(
                inputs["input_features"],
                language=language,
                return_timestamps=return_timestamps,
            )

        transcription = self._processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0]

        return transcription.strip()

    def transcribe_stream(
        self,
        audio_data: bytes,
        *,
        sample_rate: int = WHISPER_SAMPLE_RATE,
    ) -> str:
        """Transcribe raw audio bytes for streaming use-cases."""
        self.load()

        import librosa  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415

        audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        if sample_rate != WHISPER_SAMPLE_RATE:
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=WHISPER_SAMPLE_RATE)

        inputs = self._processor(
            audio,
            sampling_rate=WHISPER_SAMPLE_RATE,
            return_tensors="pt",
        )

        if self.device == "cuda":
            inputs = inputs.to("cuda")

        with torch.no_grad():
            generated_ids = self._model.generate(inputs["input_features"])

        return self._processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()


_stt_instance: PersianSTT | None = None


def get_stt() -> PersianSTT:
    """Return singleton STT instance."""
    global _stt_instance  # noqa: PLW0603
    if _stt_instance is None:
        _stt_instance = PersianSTT()
    return _stt_instance


class FastPersianSTT:
    """Alternative STT using faster-whisper for speed."""

    def __init__(self, model_size: str = "large-v3") -> None:
        """Initialize with the specified model size.

        Args:
            model_size: Whisper model size (e.g. large-v3).

        """
        self.model_size = model_size
        self._model = None

    def load(self) -> None:
        """Load the faster-whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel  # noqa: PLC0415

            self._model = WhisperModel(
                self.model_size,
                device="cuda" if torch.cuda.is_available() else "cpu",
                compute_type="float16" if torch.cuda.is_available() else "int8",
            )

    def transcribe(self, audio_path: str | Path) -> str:
        """Transcribe an audio file to Persian text."""
        self.load()
        segments, _info = self._model.transcribe(str(audio_path), language="fa")
        return " ".join(segment.text for segment in segments)
