"""Tests for WakeWordListener pause/resume logic."""

from unittest.mock import MagicMock

from src.config_manager import DEFAULT_WAKE_WORD_THRESHOLD
from src.wake_word import WakeWordListener


class TestDefaults:
    def test_default_threshold_is_conservative(self):
        """Default threshold should prevent false triggers on ambient noise."""
        assert DEFAULT_WAKE_WORD_THRESHOLD == 1e-20

    def test_listener_uses_configured_threshold(self):
        listener = WakeWordListener(keyword="hey", threshold=1e-20)
        assert listener._threshold == 1e-20
        assert listener._keyword == "hey"

    def test_listener_default_threshold(self):
        listener = WakeWordListener()
        assert listener._threshold == 1e-20


class TestPauseResume:
    def test_pause_sets_flag(self):
        listener = WakeWordListener(keyword="test")
        assert not listener._paused
        listener.pause()
        assert listener._paused

    def test_resume_clears_flag(self):
        listener = WakeWordListener(keyword="test")
        listener._paused = True
        listener.resume()
        assert not listener._paused

    def test_resume_sets_cooldown(self):
        import time
        listener = WakeWordListener(keyword="test")
        listener._paused = True
        listener.resume()
        # Cooldown should be ~2s in the future
        assert listener._cooldown_until > time.monotonic()
        assert listener._cooldown_until <= time.monotonic() + 2.5

    def test_resume_resets_decoder(self):
        listener = WakeWordListener(keyword="test")
        decoder = MagicMock()
        listener._decoder = decoder
        listener._paused = True

        listener.resume()

        decoder.end_utt.assert_called_once()
        decoder.start_utt.assert_called_once()

    def test_resume_without_decoder_no_crash(self):
        listener = WakeWordListener(keyword="test")
        listener._decoder = None
        listener._paused = True

        # Should not raise
        listener.resume()

    def test_resume_decoder_error_handled(self):
        listener = WakeWordListener(keyword="test")
        decoder = MagicMock()
        decoder.end_utt.side_effect = RuntimeError("boom")
        listener._decoder = decoder
        listener._paused = True

        # Should not propagate exception
        listener.resume()
        assert not listener._paused
