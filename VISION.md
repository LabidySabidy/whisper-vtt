# VISION.md — Whisper VTT

## What this app is
A portable, offline, system-wide dictation utility for Windows. Press a global hotkey from any application, speak, and your words appear as text — transcribed locally via OpenAI's Whisper model. No audio leaves the machine. No network calls. No API keys. No installation.

## Who it's for

| Persona | Context |
|---|---|
| **Enterprise/VDI worker** | Locked-down virtual desktop, no admin rights, can't install software. Drops a folder, double-clicks the EXE, gets dictation. |
| **Privacy-conscious professional** | Won't use cloud dictation tools (Otter, Dragon cloud, browser-based). Needs a guarantee that audio stays local. |
| **Power user / developer** | Wants a keyboard-driven dictation tool that works everywhere (IDEs, terminals, emails) without switching context. |
| **Accessibility user** | Needs voice input as an alternative to typing, but can't install system-level accessibility software. |

## What problem it solves
"Every dictation tool either phones home, requires an internet connection, needs admin install, or only works inside one app. I want to press a key, talk, and have text appear wherever my cursor is — without my voice data leaving this machine."

## Solution shape
**Windows system tray app** with global keyboard hook. Single Python process, CPU-only inference, portable folder distribution (unzip → double-click → works).

## Core v1 functionality
1. Global hotkey (default: backtick) triggers recording from any application
2. Microphone capture at 16kHz mono, with voice activity detection to auto-stop
3. Local Whisper transcription (tiny.en model bundled, CPU-only)
4. Transcribed text placed on clipboard; user pastes manually (Ctrl+V)
5. System tray icon shows status (idle/recording/transcribing/error)
6. TOML config file for power users (hotkey, model, VAD sensitivity, output mode)
7. Packaged as portable folder via PyInstaller — no install required

## Non-goals for v1
- GPU acceleration
- Non-English transcription
- Audio file import/transcription
- Persistent transcription history
- Custom vocabulary or model fine-tuning
- Multi-language UI

## Domain glossary

| Term | Meaning in this project |
|---|---|
| **VAD** | Voice Activity Detection — RMS energy analysis that determines when the user has stopped speaking |
| **Push-to-talk** | Recording mode where user holds the hotkey to record, releases to stop |
| **Toggle** | Recording mode where each hotkey press starts/stops recording |
| **Auto-paste** | Output mode that simulates Ctrl+V after transcription (where SendInput is available) |
| **Clipboard-only** | Output mode that places text on clipboard for manual paste |
| **PortAudio** | Cross-platform audio API (via sounddevice) — chosen for VDI audio redirection compatibility |
| **Whisper model** | OpenAI's speech recognition model; `tiny.en` (~75MB) is the bundled default |
| **`--onedir`** | PyInstaller mode that outputs a folder (not single EXE) for easier model bundling |
