"""Voice Activity Detection — RMS energy-based silence detection."""

import numpy as np


class VADEngine:
    """Detects silence in audio streams using RMS energy analysis.

    Accumulates consecutive silent chunks and fires a callback
    when the total silence duration exceeds the configured threshold.
    A single non-silent chunk resets the counter.
    """

    def __init__(
        self,
        silence_threshold_ms: int = 5000,
        volume_threshold_db: float = -45.0,
        chunk_duration_ms: float = 100.0,
    ):
        self.silence_threshold_ms = silence_threshold_ms
        self.volume_threshold_db = volume_threshold_db
        self.chunk_duration_ms = chunk_duration_ms

        self._consecutive_silent_ms: float = 0.0
        self._silence_detected: bool = False
        self._peak_db: float = float("-inf")  # track loudest chunk for diagnostics

    def reset(self) -> None:
        """Reset state for a new recording session."""
        self._consecutive_silent_ms = 0.0
        self._silence_detected = False
        self._peak_db = float("-inf")

    def process_chunk(self, samples: np.ndarray) -> bool:
        """Process an audio chunk. Returns True if silence threshold reached.

        Args:
            samples: float32 numpy array of audio samples.

        Returns:
            True if silence has been detected (consecutive silence >= threshold).
        """
        db_level = self._compute_db(samples)

        # Track peak for diagnostics
        if db_level > self._peak_db:
            self._peak_db = db_level

        if db_level <= self.volume_threshold_db:
            self._consecutive_silent_ms += self.chunk_duration_ms
        else:
            self._consecutive_silent_ms = 0.0

        if self._consecutive_silent_ms >= self.silence_threshold_ms:
            self._silence_detected = True
            return True

        return False

    @property
    def is_silence_detected(self) -> bool:
        """Has silence been detected since last reset?"""
        return self._silence_detected

    @property
    def current_silence_ms(self) -> float:
        """Current consecutive silent duration in milliseconds."""
        return self._consecutive_silent_ms

    @property
    def peak_db(self) -> float:
        """Loudest chunk seen since last reset (dBFS). For diagnostics."""
        return self._peak_db

    @staticmethod
    def _compute_db(samples: np.ndarray) -> float:
        """Compute RMS energy in decibels for an audio chunk.

        Formula: dB = 20 * log10(rms) where rms = sqrt(mean(samples²))

        Returns:
            dB level, or -inf for silent/empty chunks.
        """
        if len(samples) == 0:
            return float("-inf")

        rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
        if rms == 0.0:
            return float("-inf")

        return float(20.0 * np.log10(rms))
