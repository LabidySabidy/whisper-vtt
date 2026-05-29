# PLAN.md — Whisper VTT

## Phase 1: Foundation
Project skeleton, data models, config manager. End-to-end useful: you can load/save/validate TOML config.

- `pyproject.toml` with dependencies, `requirements.txt`
- `src/` package structure (`__init__.py`, `__main__.py` stub)
- `src/models.py` — all enums and dataclasses
- `src/paths.py` — PathResolver (source vs PyInstaller bundle)
- `src/config_manager.py` — TOML load/validate/write with defaults
- `config.toml` — shipped defaults

## Phase 2: Recording pipeline
Audio capture, VAD engine, transcription engine. End-to-end useful: record from mic, auto-stop on silence, get text.

- `src/audio_capture.py` — sounddevice InputStream, 16kHz mono, chunk streaming
- `src/vad_engine.py` — RMS energy detection, silence threshold tracking
- `src/transcription_engine.py` — openai-whisper model load/inference, CPU-only

## Phase 3: User interface
Hotkey listener, output handler, system tray. End-to-end useful: press a key, get text on clipboard.

- `src/hotkey_listener.py` — Windows low-level keyboard hook, message pump, toggle/push-to-talk
- `src/output_handler.py` — win32clipboard, clipboard set, fallback to clip.exe
- `src/system_tray.py` — pystray icon, colored status circles, exit menu

## Phase 4: Integration
App controller wires all components, entry point, state machine. End-to-end useful: full dictation flow.

- `src/app_controller.py` — state machine (Idle→Recording→Transcribing→Delivering→Idle), ThreadPoolExecutor, error handling
- `src/__main__.py` — load config, instantiate controller, start, handle shutdown

## Phase 5: Build & distribution
PyInstaller packaging, model bundling, zip output.

- `scripts/build.py` — PyInstaller --onedir, model copy, config copy, zip
- `scripts/download_model.py` — fetch tiny.en.pt if missing
