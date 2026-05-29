# TASKS.md — Whisper VTT

## Phase 1: Foundation

- [x] Create project skeleton
  Done when: `pyproject.toml`, `requirements.txt`, `src/__init__.py`, `src/__main__.py` (stub), `scripts/`, `models/`, and `tests/` directories exist with correct structure.

- [x] Implement data models (`src/models.py`)
  Done when: All enums (RecordingMode, OutputMode, AppStatus) and dataclasses (HotkeyCombo, AppConfig, HotkeyEvent, AudioBuffer, DeviceInfo, ClipboardContents) are defined, importable, and match the spec.

- [x] Implement PathResolver (`src/paths.py`)
  Done when: `PathResolver` correctly resolves base path whether running from source (`sys.frozen` is False) or bundled (`sys.frozen` is True). Tested with both conditions.

- [x] Implement ConfigManager (`src/config_manager.py`)
  Done when: Loads valid TOML, replaces invalid fields with defaults (never crashes), writes TOML, logs warnings for bad values. Tested with valid config, corrupt config, and missing config file.

- [x] Create default `config.toml`
  Done when: `config.toml` exists at project root with all defaults from the spec (hotkey=backtick, toggle mode, auto_paste, 5000ms silence, -15dB threshold, models/tiny.en.pt).

- [x] Unit tests for Phase 1
  Done when: `pytest tests/ -v` passes. Covers config round-trip serialization, invalid config graceful defaults, PathResolver source vs bundled paths.
