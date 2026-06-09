# Design Concept — macOS Port

## Goal
Port Whisper-VTT to macOS from a single codebase — no fork, Windows unchanged, macOS ships as a double-clickable `.app`.

## Approach
Backend factory package (`src/backends/`) swaps interaction layer by `sys.platform`. Windows keeps current code moved into `windows.py`; macOS gets new implementations behind identical interfaces. `rumps` for tray (not pystray), Quartz event tap for hotkeys, `pbcopy`/`osascript` for output. Mac-only threading inversion: tray owns main thread, controller on worker thread.

## Assumptions (with confidence)
- HIGH: Cross-platform core (sounddevice, pywhispercpp, VAD, transcription) needs zero changes — verified by reading all four source files; zero Windows-specific calls in audio/vad/transcription code.
- HIGH: Backend factory + identical public signatures means `app_controller.py` and `__main__.py` change by ~3 import lines — verified by reading controller's calls; it only touches public methods (`start`, `stop`, `deliver`, `set_status`, `process_queue`).
- MEDIUM: Quartz event tap can swallow the backtick without leaking into the focused app — NOT prototyped. Spike first.
- MEDIUM: `rumps` owns the NSApplication loop cleanly and removes the main-thread gymnastics from Gotcha 1 — known from other projects, but not tested in this specific app.
- LOW: `pyobjc-framework-Quartz` installs and imports cleanly on arm64 macOS — depends on pip wheels for arm64.

## Risks (ranked)

- **CRITICAL**: Quartz event tap untested — if it can't swallow the backtick reliably, the entire macOS hotkey model collapses. → Spike in isolation before refactoring: create tap, intercept backtick, verify swallow in a text editor.
- **HIGH**: Permissions (Accessibility + Microphone) must be granted manually — no TCC workaround exists. → Proactive prompt with `AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})`; health-check command (`--check`) that reports permission state.
- **HIGH**: No Mac available for testing — build verification and TCC-gated features require a real Mac. → Health-check diagnostic prints accessibility/mic/model status; sister can screenshot failures.
- **MEDIUM**: PyInstaller Info.plist injection is incomplete — `LSUIElement` may be dropped on rebuild. → Post-build `plutil` verification step in `build.py`; fail build if keys missing.
- **MEDIUM**: `.icns` conversion from `.ico` — `iconutil` needs a `.iconset` folder, `sips` can't read `.ico`. → Need high-res PNG source or intermediate conversion tool.
- **LOW**: Model bundling — read-only inside `.app` vs user-swappable at `~/Library/`. → Decide: read-only for v1 (simpler), add user-swappable later.
- **LOW**: `pyproject.toml` lists `openai-whisper` but codebase uses `pywhispercpp` — stale, not blocking. → Fix in this pass or defer to separate cleanup.

## Out of scope
- Code signing / notarization ($99/yr Apple Developer Program)
- Universal2 binary (arm64-only is fine, build on target arch)
- Rich console TUI on macOS (`.app` has no terminal — tray icon is the UI)
- Non-English models on macOS (same as Windows v1 scope)

## Open questions
- Do you have a high-res PNG of the app icon for `.icns` conversion?
- Will your sister test on her Mac, or do you have another Mac available?
- Model: read-only bundled, or user-swappable with `~/Library` fallback?

## Ready to implement?
Yes — AFTER the Quartz spike validates the hotkey swallow.
Recommended order: spike → step 0 (test import update) → step 1 (backend refactor, Windows green) → steps 2-6 (macOS code) → health check → sister tests.
