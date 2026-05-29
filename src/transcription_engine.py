"""Whisper speech-to-text transcription engine."""

import logging
import warnings
from pathlib import Path
from typing import Optional

import numpy as np

# Suppress whisper's verbose output
warnings.filterwarnings("ignore", module="whisper")

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when transcription fails."""


class TranscriptionEngine:
    """Local CPU-only speech-to-text using OpenAI's Whisper model.

    The model is preloaded at construction to minimize first-transcription
    latency. Supports two loading strategies:
    1. If a model file exists at the configured path → load directly.
    2. Otherwise → use whisper's built-in model name resolution
       (downloads on first use, caches at ~/.cache/whisper/).
    """

    def __init__(self, model_path: Optional[Path] = None):
        """
        Args:
            model_path: Path to a .pt model file, or None to use
                        whisper's built-in name resolution.
        """
        self._model_path = model_path
        self._model: Optional[object] = None
        self._model_loaded = False
        self._load_error: Optional[str] = None

    @property
    def is_available(self) -> bool:
        """Whether the model loaded successfully and transcription is possible."""
        return self._model_loaded

    @property
    def load_error(self) -> Optional[str]:
        """Error message if model failed to load, or None."""
        return self._load_error

    def load_model(self) -> None:
        """Preload the whisper model into memory.

        Must be called before transcribe(). Safe to call multiple times —
        subsequent calls are no-ops.
        """
        if self._model_loaded:
            return

        try:
            import whisper
        except ImportError:
            self._load_error = (
                "openai-whisper package not installed. "
                "Install with: pip install openai-whisper"
            )
            logger.error(self._load_error)
            return

        try:
            if self._model_path and Path(self._model_path).exists():
                logger.info("Loading model from file: %s", self._model_path)
                self._model = whisper.load_model(
                    str(self._model_path),
                    device="cpu",
                )
            else:
                # Use whisper's built-in resolution — will download
                # tiny.en from the hub if not cached locally.
                model_name = "tiny.en"
                if self._model_path:
                    # Try to extract model name from path (e.g., "models/base.en.pt" → "base.en")
                    stem = Path(self._model_path).stem
                    if stem:
                        model_name = stem
                logger.info("Loading model: %s", model_name)
                self._model = whisper.load_model(
                    model_name,
                    device="cpu",
                )

            self._model_loaded = True
            self._load_error = None
            logger.info("Whisper model loaded successfully.")

        except Exception as e:
            self._load_error = f"Failed to load whisper model: {e}"
            logger.error(self._load_error)
            self._model = None
            self._model_loaded = False

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio samples to text.

        Args:
            audio: float32 numpy array at the given sample rate.
            sample_rate: Audio sample rate in Hz (default 16kHz).

        Returns:
            Transcribed text with whitespace stripped.

        Raises:
            TranscriptionError: If model not loaded or inference fails.
        """
        if not self._model_loaded or self._model is None:
            raise TranscriptionError(
                "Model not loaded. Call load_model() first."
            )

        if len(audio) == 0:
            return ""

        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        try:
            result = self._model.transcribe(
                audio,
                language="en",
                fp16=False,  # CPU-only
                verbose=False,
            )
            text = result.get("text", "").strip()
            logger.info("Transcription: %r", text)
            return text

        except Exception as e:
            raise TranscriptionError(
                f"Transcription failed: {e}"
            ) from e
