"""Tests for TranscriptionEngine (pywhispercpp)."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.transcription_engine import TranscriptionEngine, TranscriptionError


class TestTranscriptionEngineInit:
    def test_default_constructor(self):
        engine = TranscriptionEngine()
        assert not engine.is_available
        assert engine.load_error is None

    def test_with_model_path(self):
        engine = TranscriptionEngine(model_path="models/ggml-small.en.bin")
        assert not engine.is_available


class TestTranscriptionEngineLoadModel:
    def test_load_model_success(self):
        mock_model = MagicMock()
        mock_model.model_path = "/cache/ggml-base.en.bin"

        with patch("pywhispercpp.model.Model", return_value=mock_model):
            engine = TranscriptionEngine()
            engine.load_model()

        assert engine.is_available
        assert engine.load_error is None

    def test_load_model_idempotent(self):
        mock_model = MagicMock()

        with patch("pywhispercpp.model.Model", return_value=mock_model) as mock_cls:
            engine = TranscriptionEngine()
            engine.load_model()
            engine.load_model()

        assert mock_cls.call_count == 1

    def test_load_model_import_error(self):
        engine = TranscriptionEngine()

        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pywhispercpp.model":
                raise ImportError("No module named 'pywhispercpp'")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = mock_import
        try:
            engine.load_model()
        finally:
            builtins.__import__ = original_import

        assert not engine.is_available
        assert "pywhispercpp" in engine.load_error

    def test_load_model_failure(self):
        engine = TranscriptionEngine()

        with patch(
            "pywhispercpp.model.Model",
            side_effect=RuntimeError("model load error"),
        ):
            engine.load_model()

        assert not engine.is_available
        assert "model load error" in engine.load_error


class TestTranscriptionEngineTranscribe:
    def test_transcribe_success(self):
        engine = TranscriptionEngine()
        mock_segment = MagicMock()
        mock_segment.text = "hello world"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = [mock_segment]
        engine._model = mock_model
        engine._model_loaded = True

        audio = np.zeros(16000, dtype=np.float32)
        result = engine.transcribe(audio)

        assert result == "hello world"
        mock_model.transcribe.assert_called_once()

    def test_transcribe_empty_audio(self):
        engine = TranscriptionEngine()
        engine._model = MagicMock()
        engine._model_loaded = True

        result = engine.transcribe(np.array([], dtype=np.float32))
        assert result == ""

    def test_transcribe_not_loaded(self):
        engine = TranscriptionEngine()
        audio = np.zeros(16000, dtype=np.float32)

        with pytest.raises(TranscriptionError, match="Model not loaded"):
            engine.transcribe(audio)

    def test_transcribe_inference_failure(self):
        engine = TranscriptionEngine()
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("inference error")
        engine._model = mock_model
        engine._model_loaded = True

        audio = np.zeros(16000, dtype=np.float32)
        with pytest.raises(TranscriptionError, match="inference error"):
            engine.transcribe(audio)

    def test_transcribe_converts_int_to_float(self):
        engine = TranscriptionEngine()
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = [mock_segment]
        engine._model = mock_model
        engine._model_loaded = True

        audio = np.zeros(16000, dtype=np.int16)
        result = engine.transcribe(audio)

        called_audio = mock_model.transcribe.call_args[0][0]
        assert called_audio.dtype == np.float32
        assert result == "test"

    def test_transcribe_blank_audio_filtered(self):
        engine = TranscriptionEngine()
        mock_segment = MagicMock()
        mock_segment.text = "[BLANK_AUDIO]"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = [mock_segment]
        engine._model = mock_model
        engine._model_loaded = True

        audio = np.zeros(16000, dtype=np.float32)
        result = engine.transcribe(audio)

        assert result == ""
