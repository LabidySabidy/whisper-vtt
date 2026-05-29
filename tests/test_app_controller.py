"""Tests for AppController state machine."""

from unittest.mock import MagicMock

import numpy as np

from src.app_controller import AppController
from src.config_manager import AppConfig, RecordingMode
from src.models import (
    AppStatus,
    AudioBuffer,
    HotkeyCombo,
    OutputMode,
)


def make_toggle_config() -> AppConfig:
    return AppConfig(
        hotkey=HotkeyCombo(modifiers=frozenset(), key="`"),
        recording_mode=RecordingMode.TOGGLE,
        output_mode=OutputMode.CLIPBOARD,
        silence_threshold_ms=5000,
        volume_threshold_db=-15.0,
        model_path="models/tiny.en.pt",
    )


def make_push_to_talk_config() -> AppConfig:
    return AppConfig(
        hotkey=HotkeyCombo(modifiers=frozenset(), key="`"),
        recording_mode=RecordingMode.PUSH_TO_TALK,
        output_mode=OutputMode.CLIPBOARD,
        silence_threshold_ms=5000,
        volume_threshold_db=-15.0,
        model_path="models/tiny.en.pt",
    )


class TestAppControllerInit:
    def test_starts_idle(self):
        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=MagicMock(),
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )
        assert controller.status == AppStatus.IDLE

    def test_callbacks_wired(self):
        hotkey = MagicMock()
        audio = MagicMock()

        _controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=hotkey,
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        hotkey.set_on_activated.assert_called_once()
        hotkey.set_on_released.assert_called_once()
        audio.set_chunk_callback.assert_called_once()


class TestToggleMode:
    """Toggle mode: first press starts recording, second stops it."""

    def test_first_press_starts_recording(self):
        audio = MagicMock()
        audio.is_recording = False

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        # Initial status should be IDLE
        assert controller.status == AppStatus.IDLE

        # Simulate hotkey press
        from src.models import HotkeyEvent
        controller._on_hotkey_activated(
            HotkeyEvent(
                combo=HotkeyCombo(modifiers=frozenset(), key="`"),
                pressed=True,
                timestamp_ms=0,
            )
        )

        audio.start_recording.assert_called_once()
        assert controller.status == AppStatus.RECORDING

    def test_second_press_stops_recording(self):
        audio = MagicMock()
        audio.is_recording = True

        # Return a buffer that's long enough
        buffer = AudioBuffer(
            samples=np.zeros(16000, dtype=np.float32),  # 1 second
            sample_rate=16000,
        )
        audio.stop_recording.return_value = buffer

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        # Manually set to RECORDING
        controller._set_status(AppStatus.RECORDING)

        from src.models import HotkeyEvent
        controller._on_hotkey_activated(
            HotkeyEvent(
                combo=HotkeyCombo(modifiers=frozenset(), key="`"),
                pressed=True,
                timestamp_ms=0,
            )
        )

        audio.stop_recording.assert_called_once()

    def test_press_during_transcribing_ignored(self):
        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=MagicMock(),
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        controller._set_status(AppStatus.TRANSCRIBING)

        from src.models import HotkeyEvent
        controller._on_hotkey_activated(
            HotkeyEvent(
                combo=HotkeyCombo(modifiers=frozenset(), key="`"),
                pressed=True,
                timestamp_ms=0,
            )
        )

        # Nothing should happen — audio should NOT start
        # (we can verify status is still TRANSCRIBING)
        assert controller.status == AppStatus.TRANSCRIBING


class TestPushToTalkMode:
    def test_press_starts_recording(self):
        audio = MagicMock()
        audio.is_recording = False

        controller = AppController(
            config=make_push_to_talk_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        from src.models import HotkeyEvent
        controller._on_hotkey_activated(
            HotkeyEvent(
                combo=HotkeyCombo(modifiers=frozenset(), key="`"),
                pressed=True,
                timestamp_ms=0,
            )
        )

        audio.start_recording.assert_called_once()
        assert controller.status == AppStatus.RECORDING

    def test_release_stops_recording(self):
        audio = MagicMock()
        audio.is_recording = True

        buffer = AudioBuffer(
            samples=np.zeros(16000, dtype=np.float32),
            sample_rate=16000,
        )
        audio.stop_recording.return_value = buffer

        controller = AppController(
            config=make_push_to_talk_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        controller._set_status(AppStatus.RECORDING)

        from src.models import HotkeyEvent
        controller._on_hotkey_released(
            HotkeyEvent(
                combo=HotkeyCombo(modifiers=frozenset(), key="`"),
                pressed=False,
                timestamp_ms=0,
            )
        )

        audio.stop_recording.assert_called_once()

    def test_release_when_not_recording_noop(self):
        audio = MagicMock()

        controller = AppController(
            config=make_push_to_talk_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        # IDLE → release should be noop
        from src.models import HotkeyEvent
        controller._on_hotkey_released(
            HotkeyEvent(
                combo=HotkeyCombo(modifiers=frozenset(), key="`"),
                pressed=False,
                timestamp_ms=0,
            )
        )

        audio.stop_recording.assert_not_called()


class TestRecordingTooShort:
    def test_recording_under_100ms_discarded(self):
        audio = MagicMock()
        audio.is_recording = True

        # Buffer with less than 0.1s of audio
        buffer = AudioBuffer(
            samples=np.zeros(800, dtype=np.float32),  # 0.05s at 16kHz
            sample_rate=16000,
        )
        audio.stop_recording.return_value = buffer

        transcription = MagicMock()
        output = MagicMock()

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=transcription,
            output_handler=output,
        )

        controller._set_status(AppStatus.RECORDING)
        controller._stop_recording()

        # Should return to idle without transcribing
        assert controller.status == AppStatus.IDLE
        transcription.transcribe.assert_not_called()

    def test_recording_exactly_100ms_not_discarded(self):
        audio = MagicMock()
        audio.is_recording = True

        buffer = AudioBuffer(
            samples=np.zeros(1600, dtype=np.float32),  # exactly 0.1s
            sample_rate=16000,
        )
        audio.stop_recording.return_value = buffer

        transcription = MagicMock()
        transcription.transcribe.return_value = "test"

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=transcription,
            output_handler=MagicMock(),
        )

        # Use a mock executor to control timing
        mock_executor = MagicMock()
        controller._executor = mock_executor

        controller._set_status(AppStatus.RECORDING)
        controller._stop_recording()

        # Status should be TRANSCRIBING (submitted to executor)
        assert controller.status == AppStatus.TRANSCRIBING
        mock_executor.submit.assert_called_once()


class TestVADAutoStop:
    def test_silence_detected_stops_recording(self):
        audio = MagicMock()
        audio.is_recording = True

        buffer = AudioBuffer(
            samples=np.zeros(16000, dtype=np.float32),
            sample_rate=16000,
        )
        audio.stop_recording.return_value = buffer

        vad = MagicMock()
        vad.process_chunk.return_value = True  # silence detected

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=vad,
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        controller._set_status(AppStatus.RECORDING)

        # Send a chunk that triggers silence
        controller._on_audio_chunk(np.zeros(1600, dtype=np.float32))

        audio.stop_recording.assert_called_once()

    def test_silence_ignored_when_not_recording(self):
        audio = MagicMock()
        vad = MagicMock()
        vad.process_chunk.return_value = True

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=vad,
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        # IDLE — silence should not trigger stop
        controller._on_audio_chunk(np.zeros(1600, dtype=np.float32))
        audio.stop_recording.assert_not_called()


class TestTranscription:
    def test_transcription_delivers_text(self):
        transcription = MagicMock()
        transcription.transcribe.return_value = "hello world"

        output = MagicMock()

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=MagicMock(),
            vad_engine=MagicMock(),
            transcription_engine=transcription,
            output_handler=output,
        )

        buffer = AudioBuffer(
            samples=np.zeros(16000, dtype=np.float32),
            sample_rate=16000,
        )

        controller._do_transcribe(buffer)

        transcription.transcribe.assert_called_once()
        output.deliver.assert_called_once_with("hello world")
        assert controller.status == AppStatus.IDLE

    def test_transcription_error_returns_to_idle(self):
        transcription = MagicMock()
        from src.transcription_engine import TranscriptionError
        transcription.transcribe.side_effect = TranscriptionError("model crash")

        output = MagicMock()
        tray = MagicMock()

        controller = AppController(
            config=make_toggle_config(),
            tray=tray,
            hotkey_listener=MagicMock(),
            audio_capture=MagicMock(),
            vad_engine=MagicMock(),
            transcription_engine=transcription,
            output_handler=output,
        )

        buffer = AudioBuffer(
            samples=np.zeros(16000, dtype=np.float32),
            sample_rate=16000,
        )

        controller._do_transcribe(buffer)

        output.deliver.assert_not_called()
        tray.show_notification.assert_called_once()
        assert controller.status == AppStatus.IDLE

    def test_empty_transcription_not_delivered(self):
        transcription = MagicMock()
        transcription.transcribe.return_value = ""

        output = MagicMock()

        controller = AppController(
            config=make_toggle_config(),
            tray=MagicMock(),
            hotkey_listener=MagicMock(),
            audio_capture=MagicMock(),
            vad_engine=MagicMock(),
            transcription_engine=transcription,
            output_handler=output,
        )

        buffer = AudioBuffer(
            samples=np.zeros(16000, dtype=np.float32),
            sample_rate=16000,
        )

        controller._do_transcribe(buffer)

        output.deliver.assert_not_called()
        assert controller.status == AppStatus.IDLE

    def test_delivery_error_shows_notification(self):
        transcription = MagicMock()
        transcription.transcribe.return_value = "hello"

        output = MagicMock()
        output.deliver.side_effect = RuntimeError("clipboard error")

        tray = MagicMock()

        controller = AppController(
            config=make_toggle_config(),
            tray=tray,
            hotkey_listener=MagicMock(),
            audio_capture=MagicMock(),
            vad_engine=MagicMock(),
            transcription_engine=transcription,
            output_handler=output,
        )

        buffer = AudioBuffer(
            samples=np.zeros(16000, dtype=np.float32),
            sample_rate=16000,
        )

        controller._do_transcribe(buffer)

        tray.show_notification.assert_called_once()
        assert controller.status == AppStatus.IDLE


class TestRecordingErrors:
    def test_start_recording_error_shows_notification(self):
        from src.audio_capture import AudioCaptureError

        audio = MagicMock()
        audio.start_recording.side_effect = AudioCaptureError("mic not found")

        tray = MagicMock()

        controller = AppController(
            config=make_toggle_config(),
            tray=tray,
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        controller._start_recording()

        tray.show_notification.assert_called_once()
        assert controller.status == AppStatus.IDLE  # stays idle

    def test_stop_recording_error_returns_to_idle(self):
        from src.audio_capture import AudioCaptureError

        audio = MagicMock()
        audio.is_recording = True
        audio.stop_recording.side_effect = AudioCaptureError("stream error")

        tray = MagicMock()

        controller = AppController(
            config=make_toggle_config(),
            tray=tray,
            hotkey_listener=MagicMock(),
            audio_capture=audio,
            vad_engine=MagicMock(),
            transcription_engine=MagicMock(),
            output_handler=MagicMock(),
        )

        controller._set_status(AppStatus.RECORDING)
        controller._stop_recording()

        assert controller.status == AppStatus.IDLE
