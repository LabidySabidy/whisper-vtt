# Whisper VTT — Modernized Reproduction Guide

> A self-contained prompt to reproduce Whisper VTT with its polished CLI interface, persistent status bar, wake word support, and GGML-based transcription. Feed this entire document to an AI coding agent.

## What This App Does

A portable, offline, system-wide dictation utility for Windows. Press a hotkey or say a wake word from any application, speak, and your words appear as text — transcribed locally via whisper.cpp. Audio never leaves the machine. Clipboard-only output. No installation.

### Key Properties

- **100% offline** — whisper.cpp GGML inference on CPU
- **Portable** — single folder, no installer, no admin
- **System-wide hotkey + wake word** — backtick hotkey or voice-activated
- **VDI-compatible** — PortAudio via sounddevice
- **TOML config** — hotkey, model, VAD, wake word settings
- **Zero-config** — sensible defaults, creates config on first run

---

## Architecture

Single-process Python app. Components communicate via callbacks.

```
┌────────────────────────────────────────────────────┐
│                  App Controller                     │
│   State: Idle → Recording → Transcribing → Idle    │
├────────────────────────────────────────────────────┤
│  Hotkey  │  Audio  │  VAD  │  Wake Word           │
│  Listener│ Capture │ Engine│  Listener            │
├──────────┴─────────┴───────┴──────────────────────┤
│  Transcription Engine (pywhispercpp / GGML)        │
│  Output Handler (clipboard via win32clipboard)     │
│  System Tray (pystray, colored circle icons)       │
├────────────────────────────────────────────────────┤
│  Config Manager (TOML)  │  Path Resolver           │
└────────────────────────────────────────────────────┘
```

### Threading

| Thread | Role |
|--------|------|
| Main | Event loop + synchronous transcription queue |
| Hotkey | Windows keyboard hook message pump |
| Audio | sounddevice callback (high-priority) |
| Wake Word | PocketSphinx keyword spotting |

Transcription runs **synchronously on the main thread** via a condition-variable queue — avoids threading crashes with whisper.cpp native code.

---

## Project Structure

```
whisper-vtt/
├── src/
│   ├── __main__.py            # Entry point, banner, status bar, logging
│   ├── app_controller.py      # State machine + transcription queue
│   ├── audio_capture.py       # sounddevice 16kHz mono recording
│   ├── config_manager.py      # TOML load/save/validate
│   ├── hotkey_listener.py     # Win32 low-level keyboard hook
│   ├── models.py              # Enums, dataclasses
│   ├── output_handler.py      # Clipboard via win32clipboard
│   ├── paths.py               # Source vs PyInstaller path resolution
│   ├── system_tray.py         # pystray + Pillow icons + notifications
│   ├── transcription_engine.py # pywhispercpp wrapper, chunked, periodic reload
│   ├── vad_engine.py          # RMS energy, dB, silence detection
│   └── wake_word.py           # PocketSphinx keyword spotting
├── scripts/
│   ├── build.py               # PyInstaller packaging
│   └── download_model.py      # Model download helper
├── tests/                     # pytest, 168 tests
├── models/                    # GGML model files (bundled)
├── config.toml                # User config
├── requirements.txt           # Dependencies
└── dictation.log              # Runtime log
```

---

## Dependencies (requirements.txt)

```
sounddevice>=0.4.6
pywhispercpp>=1.5.0
bottombar>=2.1
pystray>=0.19.5
pillow>=10.0.0
numpy>=1.24.0
pywin32>=306
```

### Dev Dependencies

```
pytest>=7.4.0
pyinstaller>=5.13.0
```

---

## Configuration (config.toml)

```toml
[hotkey]
modifiers = []
key = "`"

[recording]
mode = "wake_word"       # "toggle", "push_to_talk", or "wake_word"

[output]
mode = "clipboard"       # "clipboard" only (auto_paste removed)

[vad]
silence_threshold_ms = 3000
volume_threshold_db = -50.0

[wake_word]
phrase = "jarvis"
threshold = 1e-30

[model]
path = "models/ggml-base.en.bin"   # GGML format, ~141MB
```

Model options: `ggml-tiny.en.bin` (77MB), `ggml-base.en.bin` (141MB), `ggml-small.en.bin` (466MB).

---

## Component Implementation Notes

### Transcription Engine (`transcription_engine.py`)

Uses **pywhispercpp** (Python bindings for whisper.cpp GGML). Key behaviors:

- Model preloaded at startup from a `.bin` file path
- **Audio chunking**: splits into 60-second max chunks to stay within the model's 448-token context window (prevents buffer overflow crashes)
- **Periodic reload**: model is reloaded every 10 transcriptions to prevent whisper.cpp memory leaks
- **`[BLANK_AUDIO]` filtering**: silence segments are discarded
- Transcription runs synchronously on main thread — no threading issues with C library

```python
# Core transcription flow
self._model.params["language"] = "en"
segments = self._model.transcribe(audio_chunk)
text = " ".join(
    seg.text.strip() for seg in segments
    if seg.text and seg.text.strip() != "[BLANK_AUDIO]"
).strip()
```

### App Controller (`app_controller.py`)

State machine with synchronous transcription queue:

```
Idle → Recording → Transcribing → Idle
```

- **No ThreadPoolExecutor** — transcription runs on main thread via `process_queue()` loop
- **Condition variable** for signaling pending work
- **Tray notifications**: "Recording started", "Recording stopped — transcribing…"
- **Status callback**: notifies the CLI status bar on state changes
- **Wake word pause/resume**: paused during recording to prevent self-triggering

### CLI Interface (`__main__.py`)

#### Banner
Orange-bordered two-column startup banner with ASCII mascot art:

```
╭─── Whisper VTT ───────────────────────────────────────╮
│  Welcome to Whisper VTT        │  Tips for getting...  │
│  Your local voice transcription│                        │
│         [mascot art]           │  Say 'jarvis' or...   │
│  Model: ggml-base.en.bin       │  to start recording   │
│  Hotkey: `  ·  Ctrl+V to paste│  Transcription copied  │
╰────────────────────────────────────────────────────────╯
```

Implementation: `_Term` class with ANSI 256-color orange (`\033[38;5;208m`), ANSI-aware width calculation (`_strip_ansi` helper), center-alignment support for welcome text.

#### Console Output
Filtered to show only:
- Cycle dividers (`──────────`)
- Recording start (`◉ Recording started.`)
- Transcribing status (`○ Transcribing 12.3s...`)
- Transcription result (cyan text)

All module name prefixes, debug messages, and noisy transitions are filtered via `_ConsoleFilter` class.

#### Persistent Status Bar
Uses the **`bottombar`** library (v2.1+) for a reliable persistent bottom bar:

```python
import bottombar as bb
item = bb.add(" ● Idle — say 'jarvis' to start", label="status")
item.text = " ◉ Recording — speak now..."  # updates in-place
```

The bar updates on every state change (idle → recording → transcribing → idle). No ANSI cursor tricks needed — `bottombar` handles terminal compatibility.

#### Logging Architecture
- **File**: full DEBUG-level log with timestamps (`dictation.log`)
- **Console**: INFO-level, filtered through `_ConsoleFilter` (only shows app_controller + transcription_engine messages), styled via `_CLIFormatter`

### Audio Capture + VAD
- 16kHz mono, 100ms chunks (1600 samples), float32
- RMS-based energy detection → dB calculation
- Consecutive silent chunk tracking with configurable threshold
- Diagnostic dB levels logged to file only (DEBUG)

### Hotkey + Wake Word
- **Hotkey**: Win32 `SetWindowsHookExW` with `WH_KEYBOARD_LL`, dedicated message pump thread
- **Wake Word**: PocketSphinx keyword spotting, configurable threshold, multi-phrase support via `/` delimiter
- Both work simultaneously — hotkey can toggle even in wake word mode

---

## Build & Distribution

### PyInstaller Packaging (`--onedir`)

```bash
python scripts/build.py
```

The build script:
1. Locates the cached GGML model
2. Runs PyInstaller with hidden imports for sounddevice, numpy, pystray, PIL, win32clipboard, pywhispercpp, pocketsphinx, bottombar
3. Copies model to `dist/Whisper-VTT/models/`
4. Bundles `config.toml`
5. Creates distributable zip

Key PyInstaller flags:
- `--hidden-import`: sounddevice, _sounddevice_data, numpy, pystray, PIL, win32clipboard, win32com, pywhispercpp, pocketsphinx, bottombar
- `--collect-all`: pywhispercpp, pocketsphinx
- `--runtime-hook`: scripts/runtime_hook.py (pre-loads VC++ runtime DLLs)
- `--exclude-module`: torch, whisper, faster_whisper, ctranslate2, tkinter, matplotlib, scipy, pandas, pytest, hypothesis

### Dist Folder Contents

```
dist/Whisper-VTT/
├── Whisper-VTT.exe
├── config.toml
├── models/
│   └── ggml-base.en.bin     (~141MB)
└── _internal/                (Python + deps)
```

Distribute the zip. Unzip and double-click the exe. No Python installation needed.

---

## Known Issues & Mitigations

| Issue | Mitigation |
|-------|-----------|
| whisper.cpp buffer overflow on long audio | Audio chunked into 60s max segments |
| whisper.cpp memory leak over many calls | Model reloaded every 10 transcriptions |
| `[BLANK_AUDIO]` in output | Filtered out in transcription engine |
| "Progress: X%" spam from whisper.cpp C code | Writes directly to stderr — accepted as unavoidable |
| PyInstaller DLL loading failures | Runtime hook pre-loads VC++ runtimes |

---

## Testing

```bash
pytest tests/ -v    # 168 tests
```

Tests cover: config validation/roundtrip, VAD dB calculations, audio buffer management, hotkey modifier matching, transcription engine (mocked), app controller state machine, output handler fallbacks, system tray icon generation, path resolution (source vs frozen).

---

## Design Principles

1. **Never crash** — all exceptions caught, reported via tray notification, return to idle
2. **No network** — everything local, no telemetry, no API keys
3. **No audio to disk** — buffers exist only in memory
4. **Portable** — single folder, no registry, no admin
5. **Synchronous transcription** — avoids C library threading issues
6. **Clean console** — only user-relevant output visible, debug details in file log
7. **Reliable status bar** — `bottombar` library, no fragile ANSI tricks
