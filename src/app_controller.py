"""Application controller — orchestrates the dictation state machine.

State flow:
    Idle → Recording → Transcribing → Delivering → Idle
      ↑        │              │             │
      └────────┴──────────────┴─────────────┘  (any error → Idle)
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from src.audio_capture import AudioCapture, AudioCaptureError
from src.config_manager import AppConfig, RecordingMode
from src.hotkey_listener import HotkeyListener
from src.models import AppStatus, AudioBuffer, HotkeyEvent
from src.output_handler import OutputHandler
from src.system_tray import SystemTray
from src.transcription_engine import TranscriptionEngine, TranscriptionError
from src.vad_engine import VADEngine

logger = logging.getLogger(__name__)


class AppController:
    """Central orchestrator implementing the dictation state machine.

    Wires together hotkey listener, audio capture, VAD,
    transcription, output, and system tray. Handles errors
    at every transition — never crashes, always returns to idle.
    """

    def __init__(
        self,
        config: AppConfig,
        tray: SystemTray,
        hotkey_listener: HotkeyListener,
        audio_capture: AudioCapture,
        vad_engine: VADEngine,
        transcription_engine: TranscriptionEngine,
        output_handler: OutputHandler,
    ):
        self._config = config
        self._tray = tray
        self._hotkey_listener = hotkey_listener
        self._audio_capture = audio_capture
        self._vad_engine = vad_engine
        self._transcription_engine = transcription_engine
        self._output_handler = output_handler

        self._status: AppStatus = AppStatus.IDLE
        self._lock = threading.Lock()

        # Single worker for transcription (avoids concurrent GPU/CPU contention)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="transcribe")

        # Wire callbacks
        self._hotkey_listener.set_on_activated(self._on_hotkey_activated)
        self._hotkey_listener.set_on_released(self._on_hotkey_released)
        self._audio_capture.set_chunk_callback(self._on_audio_chunk)

        # Push-to-talk tracking
        self._push_to_talk_active: bool = False

    # ── Public API ─────────────────────────────────────────────────────

    @property
    def status(self) -> AppStatus:
        return self._status

    def start(self) -> None:
        """Start the application — begin listening for the hotkey."""
        logger.info("AppController starting.")
        self._set_status(AppStatus.IDLE)
        self._hotkey_listener.start()
        self._tray.start()

    def stop(self) -> None:
        """Stop the application gracefully."""
        logger.info("AppController stopping.")
        self._set_status(AppStatus.IDLE)
        self._hotkey_listener.stop()
        if self._audio_capture.is_recording:
            try:
                self._audio_capture.stop_recording()
            except Exception:
                pass
        self._executor.shutdown(wait=False)
        self._tray.stop()

    # ── Status management ──────────────────────────────────────────────

    def _set_status(self, status: AppStatus) -> None:
        with self._lock:
            self._status = status
        self._tray.set_status(status)

    # ── Hotkey callbacks ───────────────────────────────────────────────

    def _on_hotkey_activated(self, event: HotkeyEvent) -> None:
        """Hotkey pressed — start recording or toggle stop."""
        mode = self._config.recording_mode

        if mode == RecordingMode.PUSH_TO_TALK:
            self._start_recording()
        elif mode == RecordingMode.TOGGLE:
            if self._status == AppStatus.IDLE:
                self._start_recording()
            elif self._status == AppStatus.RECORDING:
                self._stop_recording()
            # Ignore if transcribing or error — let them finish/fail

    def _on_hotkey_released(self, event: HotkeyEvent) -> None:
        """Hotkey released — stop recording in push-to-talk mode."""
        if self._config.recording_mode == RecordingMode.PUSH_TO_TALK:
            if self._status == AppStatus.RECORDING:
                self._stop_recording()

    # ── Recording flow ─────────────────────────────────────────────────

    def _start_recording(self) -> None:
        """Begin recording from the microphone."""
        if self._status != AppStatus.IDLE:
            return

        self._vad_engine.reset()

        try:
            self._audio_capture.start_recording()
        except AudioCaptureError as e:
            logger.error("Failed to start recording: %s", e)
            self._tray.show_notification("Whisper VTT", f"Microphone error: {e}")
            return

        self._set_status(AppStatus.RECORDING)
        logger.info("Recording started.")

    def _stop_recording(self) -> None:
        """Stop recording and begin transcription."""
        if self._status != AppStatus.RECORDING:
            return

        try:
            buffer = self._audio_capture.stop_recording()
        except AudioCaptureError as e:
            logger.error("Failed to stop recording: %s", e)
            self._set_status(AppStatus.IDLE)
            return

        # Discard very short recordings (< 0.1s)
        if buffer.duration_seconds < 0.1:
            logger.debug("Recording too short (%.2fs), discarding.", buffer.duration_seconds)
            self._set_status(AppStatus.IDLE)
            return

        self._set_status(AppStatus.TRANSCRIBING)
        self._executor.submit(self._do_transcribe, buffer)

    # ── Audio chunk callback (VAD) ─────────────────────────────────────

    def _on_audio_chunk(self, chunk) -> None:
        """Process each audio chunk through VAD."""
        silence_detected = self._vad_engine.process_chunk(chunk)
        if silence_detected and self._status == AppStatus.RECORDING:
            logger.info("Silence detected, auto-stopping recording.")
            self._stop_recording()

    # ── Transcription (runs on worker thread) ──────────────────────────

    def _do_transcribe(self, buffer: AudioBuffer) -> None:
        """Run transcription and deliver the result."""
        try:
            text = self._transcription_engine.transcribe(
                buffer.samples,
                buffer.sample_rate,
            )
        except TranscriptionError as e:
            logger.error("Transcription failed: %s", e)
            self._tray.show_notification("Whisper VTT", f"Transcription error: {e}")
            self._set_status(AppStatus.IDLE)
            return

        if text:
            try:
                self._output_handler.deliver(text)
            except Exception as e:
                logger.error("Failed to deliver text: %s", e)
                self._tray.show_notification(
                    "Whisper VTT",
                    f"Could not set clipboard: {e}",
                )

        self._set_status(AppStatus.IDLE)
        logger.info("Dictation cycle complete.")
