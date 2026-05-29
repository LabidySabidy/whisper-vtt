"""Tests for VAD Engine."""

import numpy as np

from src.vad_engine import VADEngine


class TestComputeDb:
    def test_silence_is_negative_inf(self):
        samples = np.zeros(1600, dtype=np.float32)
        db = VADEngine._compute_db(samples)
        assert db == float("-inf")

    def test_empty_chunk_is_negative_inf(self):
        samples = np.array([], dtype=np.float32)
        db = VADEngine._compute_db(samples)
        assert db == float("-inf")

    def test_full_scale_sine(self):
        # A full-scale sine wave at 0 dBFS
        t = np.linspace(0, 1, 1600, endpoint=False, dtype=np.float32)
        samples = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        db = VADEngine._compute_db(samples)
        # RMS of sine = amplitude / sqrt(2) = 1/sqrt(2) ≈ 0.707
        # dB = 20*log10(0.707) ≈ -3.01
        assert -4 < db < -2

    def test_quiet_signal(self):
        # Very quiet signal
        samples = np.full(1600, 0.001, dtype=np.float32)
        db = VADEngine._compute_db(samples)
        # dB = 20*log10(0.001) = -60
        assert -61 < db < -59


class TestVADEngine:
    def make_chunk(self, amplitude: float = 0.0, size: int = 1600) -> np.ndarray:
        """Helper to create a chunk with given amplitude."""
        return np.full(size, amplitude, dtype=np.float32)

    def test_initial_state(self):
        vad = VADEngine(
            silence_threshold_ms=5000,
            volume_threshold_db=-15.0,
            chunk_duration_ms=100.0,
        )
        assert not vad.is_silence_detected
        assert vad.current_silence_ms == 0.0

    def test_single_silent_chunk_does_not_trigger(self):
        vad = VADEngine(silence_threshold_ms=5000, chunk_duration_ms=100.0)
        result = vad.process_chunk(self.make_chunk(0.0))
        assert not result
        assert vad.current_silence_ms == 100.0

    def test_silence_accumulates(self):
        vad = VADEngine(silence_threshold_ms=5000, chunk_duration_ms=100.0)
        for _ in range(30):  # 3 seconds
            vad.process_chunk(self.make_chunk(0.0))
        assert vad.current_silence_ms == 3000.0
        assert not vad.is_silence_detected

    def test_silence_threshold_reached(self):
        vad = VADEngine(silence_threshold_ms=5000, chunk_duration_ms=100.0)
        for _ in range(49):  # 4.9 seconds — not yet
            result = vad.process_chunk(self.make_chunk(0.0))
            assert not result
        # 50th chunk = 5.0 seconds — triggers
        result = vad.process_chunk(self.make_chunk(0.0))
        assert result
        assert vad.is_silence_detected
        assert vad.current_silence_ms == 5000.0

    def test_non_silent_chunk_resets_counter(self):
        vad = VADEngine(silence_threshold_ms=5000, chunk_duration_ms=100.0)
        # 3 seconds of silence
        for _ in range(30):
            vad.process_chunk(self.make_chunk(0.0))
        assert vad.current_silence_ms == 3000.0

        # A loud chunk resets the counter
        vad.process_chunk(self.make_chunk(1.0))
        assert vad.current_silence_ms == 0.0

    def test_quiet_but_above_threshold_resets(self):
        """Signal below -15dB should still reset if above volume_threshold_db."""
        vad = VADEngine(
            silence_threshold_ms=5000,
            volume_threshold_db=-30.0,  # very low threshold
            chunk_duration_ms=100.0,
        )
        for _ in range(30):
            vad.process_chunk(self.make_chunk(0.0))
        assert vad.current_silence_ms == 3000.0

        # A signal at -25 dB (amplitude ~0.056) is above -30dB threshold
        amplitude = 10 ** (-25.0 / 20.0)  # ~0.0562
        quiet = np.full(1600, amplitude, dtype=np.float32)
        vad.process_chunk(quiet)
        assert vad.current_silence_ms == 0.0

    def test_reset_clears_state(self):
        vad = VADEngine(silence_threshold_ms=5000, chunk_duration_ms=100.0)
        for _ in range(50):
            vad.process_chunk(self.make_chunk(0.0))
        assert vad.is_silence_detected

        vad.reset()
        assert not vad.is_silence_detected
        assert vad.current_silence_ms == 0.0

    def test_chunk_at_exact_threshold_db(self):
        """Signal exactly at volume_threshold_db is treated as silent."""
        # -15 dB = 10^(-15/20) ≈ 0.1778 amplitude
        amplitude = 10 ** (-15.0 / 20.0)
        samples = np.full(1600, amplitude, dtype=np.float32)
        vad = VADEngine(
            silence_threshold_ms=5000,
            volume_threshold_db=-15.0,
            chunk_duration_ms=100.0,
        )
        # Should be <= threshold, so silent
        vad.process_chunk(samples)
        assert vad.current_silence_ms == 100.0
