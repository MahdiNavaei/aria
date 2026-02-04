"""Voice input component with Persian STT support.

Requires: pip install streamlit-mic-recorder
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from aria.ui.i18n import t

logger = logging.getLogger(__name__)

# Try to import mic_recorder, fallback gracefully if not installed
_MIC_RECORDER_AVAILABLE = False
try:
    from streamlit_mic_recorder import mic_recorder

    _MIC_RECORDER_AVAILABLE = True
except ImportError:
    logger.warning("streamlit-mic-recorder not installed. Voice input will be disabled.")


def render_voice_input(
    key: str = "voice_input",
    on_transcription: Any = None,
) -> str | None:
    """Render voice input button with Persian STT.

    Args:
        key: Unique key for the component
        on_transcription: Callback when transcription is complete

    Returns:
        Transcribed text if available, None otherwise
    """
    if not _MIC_RECORDER_AVAILABLE:
        # Show disabled button
        if st.button(
            "🎤",
            key=f"{key}_disabled",
            disabled=True,
            help="Voice input unavailable. Install: pip install streamlit-mic-recorder",
        ):
            pass
        return None

    # Initialize state
    if f"{key}_transcribing" not in st.session_state:
        st.session_state[f"{key}_transcribing"] = False
    if f"{key}_last_text" not in st.session_state:
        st.session_state[f"{key}_last_text"] = None

    # Show recording status
    if st.session_state[f"{key}_transcribing"]:
        st.info(f"🔄 {t('chat.voice_processing')}")

    # Record audio
    audio = mic_recorder(
        key=key,
        start_prompt=f"🎤 {t('chat.voice_button')}",
        stop_prompt=f"⏹️ Stop",
        just_once=True,
        use_container_width=True,
        format="wav",
        callback=None,
    )

    if audio is not None and audio.get("bytes"):
        st.session_state[f"{key}_transcribing"] = True

        # Process audio
        text = _transcribe_audio(audio)

        if text:
            st.session_state[f"{key}_last_text"] = text
            st.session_state[f"{key}_transcribing"] = False

            if on_transcription:
                on_transcription(text)

            return text

        st.session_state[f"{key}_transcribing"] = False

    return st.session_state.get(f"{key}_last_text")


def _transcribe_audio(audio: dict[str, Any]) -> str | None:
    """Transcribe audio using Persian STT.

    Args:
        audio: Audio data dict with 'bytes' and optionally 'sample_rate'

    Returns:
        Transcribed text or None if failed
    """
    audio_bytes = audio.get("bytes")
    sample_rate = audio.get("sample_rate", 16000)

    if not audio_bytes:
        return None

    try:
        # Try to use PersianSTT
        from aria.core.voice.stt import get_stt

        stt = get_stt()

        # Save to temp file for transcription
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            text = stt.transcribe(temp_path)
            return text
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    except ImportError:
        logger.warning("PersianSTT not available, trying fallback")
        return _transcribe_fallback(audio_bytes, sample_rate)
    except Exception as exc:
        logger.error("STT transcription failed", exc_info=exc)
        st.error(f"❌ {t('error.generic')}: {exc}")
        return None


def _transcribe_fallback(audio_bytes: bytes, sample_rate: int) -> str | None:
    """Fallback transcription using Google Speech API via mic_recorder.

    Args:
        audio_bytes: Raw audio bytes
        sample_rate: Audio sample rate

    Returns:
        Transcribed text or None
    """
    try:
        from streamlit_mic_recorder import speech_to_text

        # Use built-in speech_to_text with Persian
        text = speech_to_text(
            language="fa-IR",
            start_prompt="🎤",
            stop_prompt="⏹️",
            just_once=True,
            key="stt_fallback",
        )
        return text
    except Exception as exc:
        logger.error("Fallback STT failed", exc_info=exc)
        return None


def render_voice_button_simple(key: str = "voice_simple") -> bool:
    """Render a simple voice button that returns True when clicked.

    This is a simpler alternative when full STT is not needed.

    Args:
        key: Unique key for the button

    Returns:
        True if button was clicked
    """
    return st.button(
        "🎤",
        key=key,
        help=t("chat.voice_button"),
        use_container_width=True,
    )


def is_voice_available() -> bool:
    """Check if voice input is available.

    Returns:
        True if streamlit-mic-recorder is installed
    """
    return _MIC_RECORDER_AVAILABLE
