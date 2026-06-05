"""Whisper speech-to-text transcription engine using pywhispercpp.

Uses pywhispercpp (Python bindings for whisper.cpp GGML models).
Model is loaded once at startup and transcription runs on the main
thread — no subprocess, no threading issues.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when transcription fails."""


class TranscriptionEngine:
    """Local CPU-only speech-to-text using pywhispercpp (whisper.cpp)."""

    def __init__(self, model_path: str = "models/ggml-base.en.bin"):
        self._model_path = model_path
        self._model: Optional[object] = None
        self._model_loaded = False
        self._load_error: Optional[str] = None
        self._transcribe_count = 0
        self._reload_interval = 10  # Reload model every N transcriptions

    @property
    def is_available(self) -> bool:
        return self._model_loaded

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def load_model(self) -> None:
        """Load the whisper.cpp model into memory."""
        if self._model_loaded:
            return

        try:
            from pywhispercpp.model import Model
        except ImportError:
            self._load_error = (
                "pywhispercpp package not installed. "
                "Install with: pip install pywhispercpp"
            )
            logger.error(self._load_error)
            return

        try:
            if Path(self._model_path).exists():
                logger.debug("Loading model from file: %s", self._model_path)
                self._model = Model(str(self._model_path))
            else:
                model_name = "tiny.en"
                stem = Path(self._model_path).stem
                if stem:
                    model_name = stem.replace("ggml-", "")
                logger.debug("Loading model: %s", model_name)
                self._model = Model(model_name)

            self._model_loaded = True
            self._load_error = None
            logger.debug(
                "Model loaded successfully: %s",
                getattr(self._model, "model_path", self._model_path),
            )

        except Exception as e:
            self._load_error = f"Failed to load whisper model: {e}"
            logger.error(self._load_error)
            self._model = None
            self._model_loaded = False

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio samples to text.

        Splits audio into max-60s chunks to stay within the model's
        448-token context window (prevents buffer overflow crashes).
        """
        if not self._model_loaded or self._model is None:
            raise TranscriptionError("Model not loaded. Call load_model() first.")

        if len(audio) == 0:
            return ""

        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Periodically reload model to prevent whisper.cpp memory leak
        # over many transcription calls (crashes after ~20-30 cycles).
        self._transcribe_count += 1
        if self._transcribe_count % self._reload_interval == 0:
            logger.debug(
                "Reloading model (cycle %d) to prevent memory leak",
                self._transcribe_count,
            )
            self._model = None
            self._model_loaded = False
            self.load_model()

        # tiny.en context window is 448 tokens (~60s of speech).
        # Split into chunks to avoid buffer overflow crashes.
        chunk_samples = 60 * sample_rate  # 60 seconds
        texts = []

        for start in range(0, len(audio), chunk_samples):
            chunk = audio[start : start + chunk_samples]
            try:
                self._model.params["language"] = "en"
                segments = self._model.transcribe(chunk)
                chunk_text = " ".join(
                    seg.text.strip()
                    for seg in segments
                    if seg.text and seg.text.strip() != "[BLANK_AUDIO]"
                ).strip()
                if chunk_text:
                    texts.append(chunk_text)
            except Exception as e:
                raise TranscriptionError(
                    f"Transcription failed: {e}"
                ) from e

        if not texts:
            return ""

        text = " ".join(texts)
        logger.info("Transcription: %r", text)
        return text
