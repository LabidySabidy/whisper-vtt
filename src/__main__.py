"""Whisper VTT — Portable offline dictation utility.

Entry point. Loads config, wires components, and starts the app.
"""

import logging
import signal
import sys

from src.app_controller import AppController
from src.audio_capture import AudioCapture
from src.config_manager import load_config
from src.hotkey_listener import HotkeyListener
from src.output_handler import OutputHandler
from src.paths import PathResolver
from src.system_tray import SystemTray
from src.transcription_engine import TranscriptionEngine
from src.vad_engine import VADEngine


def setup_logging() -> None:
    """Configure logging to file and stderr."""
    log_path = PathResolver.log_path()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def main() -> None:
    """Application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Whisper VTT starting...")

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.fatal("Failed to load config: %s", e)
        sys.exit(1)

    logger.info("Config loaded: hotkey=%s, mode=%s, model=%s",
                 config.hotkey, config.recording_mode.value, config.model_path)

    # Resolve model path
    model_path = PathResolver.resolve(config.model_path)

    # Initialize components
    tray = SystemTray(title="Whisper VTT")
    hotkey_listener = HotkeyListener(config.hotkey)
    audio_capture = AudioCapture()
    vad_engine = VADEngine(
        silence_threshold_ms=config.silence_threshold_ms,
        volume_threshold_db=config.volume_threshold_db,
    )
    transcription_engine = TranscriptionEngine(model_path=model_path)
    output_handler = OutputHandler(mode=config.output_mode)

    # Preload the whisper model (non-blocking)
    # If model fails to load, app still starts — dictation just won't work
    transcription_engine.load_model()
    if not transcription_engine.is_available:
        logger.warning("Whisper model not available. Dictation disabled.")
        tray.show_notification(
            "Whisper VTT",
            f"Model not loaded: {transcription_engine.load_error or 'unknown error'}",
        )

    # Create controller
    controller = AppController(
        config=config,
        tray=tray,
        hotkey_listener=hotkey_listener,
        audio_capture=audio_capture,
        vad_engine=vad_engine,
        transcription_engine=transcription_engine,
        output_handler=output_handler,
    )

    # Handle graceful shutdown
    def on_exit() -> None:
        logger.info("Shutting down...")
        controller.stop()

    tray.set_on_exit(on_exit)

    # Handle Ctrl+C in console
    signal.signal(signal.SIGINT, lambda sig, frame: on_exit())

    # Start the app
    controller.start()

    logger.info("Whisper VTT running. Press %s to dictate.", config.hotkey)

    # Keep main thread alive while tray and hotkey threads run
    try:
        # Block on tray — it runs its own event loop on its thread,
        # but we wait here for the tray to be stopped.
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        on_exit()


if __name__ == "__main__":
    main()
