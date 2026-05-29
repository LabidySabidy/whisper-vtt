"""Tests for TranscriptionEngine."""

from unittest.mock import MagicMock, patch

import numpy as np

from src.transcription_engine import TranscriptionEngine, TranscriptionError


class TestTranscriptionEngineInit:
    def test_default_constructor(self):
        engine = TranscriptionEngine()
        assert not engine.is_available
        assert engine.load_error is None

    def test_with_model_path(self):
        engine = TranscriptionEngine(model_path="models/tiny.en.pt")
        assert not engine.is_available


class TestTranscriptionEngineLoadModel:
    def test_load_model_success(self):
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model

        with patch.dict("sys.modules", {"whisper": mock_whisper}):
            engine = TranscriptionEngine()
            engine.load_model()

        assert engine.is_available
        assert engine.load_error is None
        mock_whisper.load_model.assert_called_once_with("tiny.en", device="cpu")

    def test_load_model_idempotent(self):
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model

        with patch.dict("sys.modules", {"whisper": mock_whisper}):
            engine = TranscriptionEngine()
            engine.load_model()
            engine.load_model()  # second call

        # load_model should only be called once
        assert mock_whisper.load_model.call_count == 1

    def test_load_model_import_error(self):
        engine = TranscriptionEngine()

        # simulate whisper not installed
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "whisper":
                raise ImportError("No module")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = mock_import
        try:
            engine.load_model()
        finally:
            builtins.__import__ = original_import

        assert not engine.is_available
        assert "not installed" in (engine.load_error or "")

    def test_load_model_failure(self):
        mock_whisper = MagicMock()
        mock_whisper.load_model.side_effect = RuntimeError("Out of memory")

        with patch.dict("sys.modules", {"whisper": mock_whisper}):
            engine = TranscriptionEngine()
            engine.load_model()

        assert not engine.is_available
        assert "Out of memory" in (engine.load_error or "")

    def test_load_model_from_path(self):
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model

        with (
            patch.dict("sys.modules", {"whisper": mock_whisper}),
            patch("pathlib.Path.exists", return_value=True),
        ):
            engine = TranscriptionEngine(model_path="models/custom.pt")
            engine.load_model()

        mock_whisper.load_model.assert_called_once_with(
            "models/custom.pt", device="cpu"
        )

    def test_load_model_falls_back_to_name_when_file_missing(self):
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model

        with (
            patch.dict("sys.modules", {"whisper": mock_whisper}),
            patch("pathlib.Path.exists", return_value=False),
        ):
            engine = TranscriptionEngine(model_path="models/base.en.pt")
            engine.load_model()

        # Should use the stem ("base.en") as model name
        mock_whisper.load_model.assert_called_once_with("base.en", device="cpu")


class TestTranscriptionEngineTranscribe:
    def _make_engine(self):
        """Create an engine with a mocked whisper model."""
        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model

        with patch.dict("sys.modules", {"whisper": mock_whisper}):
            engine = TranscriptionEngine()
            engine.load_model()

        return engine, mock_model

    def test_transcribe_success(self):
        engine, mock_model = self._make_engine()
        mock_model.transcribe.return_value = {"text": "  hello world  "}

        audio = np.zeros(16000, dtype=np.float32)
        result = engine.transcribe(audio)

        assert result == "hello world"
        mock_model.transcribe.assert_called_once()

    def test_transcribe_empty_audio(self):
        engine, mock_model = self._make_engine()

        audio = np.array([], dtype=np.float32)
        result = engine.transcribe(audio)

        assert result == ""
        mock_model.transcribe.assert_not_called()

    def test_transcribe_not_loaded(self):
        engine = TranscriptionEngine()
        audio = np.zeros(1600, dtype=np.float32)

        try:
            engine.transcribe(audio)
            assert False, "Should have raised"
        except TranscriptionError as e:
            assert "not loaded" in str(e).lower()

    def test_transcribe_inference_failure(self):
        engine, mock_model = self._make_engine()
        mock_model.transcribe.side_effect = RuntimeError("Inference crashed")

        audio = np.zeros(1600, dtype=np.float32)
        try:
            engine.transcribe(audio)
            assert False, "Should have raised"
        except TranscriptionError as e:
            assert "Inference crashed" in str(e)

    def test_transcribe_converts_int_to_float(self):
        """Audio with non-float32 dtype should be converted."""
        engine, mock_model = self._make_engine()
        mock_model.transcribe.return_value = {"text": "test"}

        audio = np.zeros(1600, dtype=np.int16)
        result = engine.transcribe(audio)

        assert result == "test"
        # Should have been called with float32 audio
        called_audio = mock_model.transcribe.call_args[0][0]
        assert called_audio.dtype == np.float32

    def test_transcribe_passes_correct_params(self):
        engine, mock_model = self._make_engine()
        mock_model.transcribe.return_value = {"text": "ok"}

        audio = np.zeros(8000, dtype=np.float32)
        engine.transcribe(audio, sample_rate=8000)

        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] == "en"
        assert call_kwargs["fp16"] is False
