# PROGRESS.md — Whisper VTT


<!-- session-in-progress:start=2026-06-04T21:20:32.120Z -->
## 2026-06-05 04:43 — Colors work (bottom bar is cyan), but RGB orange isn't supported _(in progress)_
Colors work (bottom bar is cyan), but RGB orange isn't supported. Switching to bright yellow `\033[93m` which your terminal definitely supports:
<!-- end-session-in-progress -->
## 2026-06-04 17:42 — Standalone whisper-cli.exe subprocess approach (WORKS)

Final fix: bundled pre-built whisper-cli.exe (whisper.cpp v1.8.6) + DLLs alongside
the Python app. Transcription writes audio to temp WAV, spawns whisper-cli.exe as
subprocess. Zero native Python library dependencies — no segfaults, no DLL init
failures. whisper.cpp crashes are isolated to the subprocess.

Bundle ~100MB (Python app + whisper-cli.exe + ggml-tiny.en.bin ~74MB).
167 tests pass. Starts cleanly in dist.

Replaced pywhispercpp (whisper.cpp GGML, C-level crash during transcription) with
faster-whisper (CTranslate2, 4x faster CPU inference, no PyTorch). Default model
changed to models/base.en (~145MB flat directory). Bundle ~550MB.

Model bundled as flat directory (snapshot_download with local_dir) — WhisperModel
loads directly, zero network, no HuggingFace cache dependency. Avoids the symlink/
blobs issue that broke the previous attempt. 169 tests pass.

Replaced pywhispercpp (whisper.cpp GGML, C-level crash during transcription) with
faster-whisper (CTranslate2, 4x faster CPU inference, no PyTorch). Default model
changed from ggml-tiny.en.bin → base.en (~140MB, good accuracy/speed balance).
Bundle ~500MB (vs 2GB for openai-whisper). 169 tests pass. Model pre-downloaded
and bundled into dist.

## 2026-06-04 16:50 — Reverted subprocess transcription + CLI-style logging

Subprocess transcription was broken in PyInstaller bundles: `sys.executable` points
to `Whisper-VTT.exe` (not a Python interpreter), so `subprocess.run()` launched a second
app instance that hung instead of transcribing. Reverted `_do_transcribe` to direct
`transcription_engine.transcribe()` call.

Logging reformatted: console output is now minimal CLI-style (`●`, `△`, `✕` symbols,
no timestamps); file log retains full timestamps at DEBUG level for diagnostics.

170 tests pass.

## 2026-06-04 14:41 — Subprocess transcription attempt (REVERTED — see 16:50)
to `Whisper-VTT.exe` (not a Python interpreter), so `subprocess.run()` launched a second
app instance that hung instead of transcribing. Reverted `_do_transcribe` to direct
`transcription_engine.transcribe()` call — the original approach that worked.

Logging reformatted: console output is now minimal CLI-style (`●`, `△`, `✕` symbols,
no timestamps); file log retains full timestamps at DEBUG level for diagnostics.

170 tests pass.

## 2026-06-04 14:41 — Subprocess transcription attempt (REVERTED)
## 2025-06-03 — Multiple wake words + faster silence detection

Wake word now supports multiple phrases via PocketSphinx native `/` delimiter: "okay now/hey dude". Silence threshold reduced 5000ms → 4000ms (20% faster auto-stop). No logic changes — both are PocketSphinx/VAD-native features. 167 tests pass, dist rebuilt.

Raised default threshold 1e-30 → 1e-15, added 2-frame consecutive-hit requirement before firing callback. Single-syllable words like "hey" no longer false-trigger from ambient noise. Dist rebuilt with config: wake_word="hey", threshold=1e-15. 167 tests passing.

Added `pause()`/`resume()` to `WakeWordListener`. Paused during recording (prevents self-triggering from own voice), resumed after transcription with clean decoder state (prevents stale matches). 164 tests passing (was 156), lint clean.

Added Windows toast notifications with system beep at recording start/stop, and a no-beep notification with transcribed text preview at completion. Notifications fire for all trigger types (hotkey toggle/push-to-talk, wake word, VAD auto-stop). Build script now preserves existing dist config on rebuild instead of overwriting user edits. 156 tests passing (was 151), lint clean.


## 2026-06-04 14:41 — Subprocess transcription attempt (REVERTED — see 16:50)
Done. Transcription now runs in a separate subprocess via the whisper CLI. No recording cap. If whisper.cpp crashes, the subprocess dies with an error code — the main app survives and shows "Transcription failed." 5-minute recordings? Go for it. Fire it up.
## 2025-06-03 — VAD threshold fixed, app fully operational

**VAD threshold calibrated:** Default changed from -15 dBFS → -30 → -45. The original -15 dB threshold was appropriate for loud signals but not speech through a typical webcam/laptop mic. User's speech peaks around -32 dBFS. Final threshold of -45 dB provides enough headroom while distinguishing speech from noise floor (-60 to -96 dB).

**Diagnostic logging added:** VAD now logs peak dB level vs threshold when silence triggers, making it easy to tune per-microphone.

**App status: FULLY OPERATIONAL**
- Startup: clean, model loads in ~120ms
- Hotkey: backtick toggle works, no ctypes errors
- Recording: 16kHz mono, 100ms chunks
- VAD: correctly tracks speech vs silence, auto-stops after 5s of real silence
- Transcription: whisper.cpp (GGML tiny.en), inference in ~1.5s for 33s of audio
- Output: clipboard set + auto-paste (Ctrl+V simulation)
- EXE: PyInstaller --onedir, portable, no PyTorch, no CUDA, no admin install

## 2025-06-02 — Switched to whisper.cpp + fixed hotkey & sounddevice

- Replaced openai-whisper (PyTorch) with pywhispercpp (whisper.cpp, GGML)
- Fixed CallNextHookEx ctypes overflow on x64 (declared argtypes)
- Fixed sounddevice missing from venv
- 151/151 tests pass, lint clean

## 2025-05-29 — Previous sessions
- All 5 phases implemented (Foundation, Recording, UI, Integration, Build)
- 151 tests across 10 test files
- PyInstaller build with model bundling
