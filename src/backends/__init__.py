"""Backend factory -- picks the right implementation by platform.

Usage:
    from src.backends import HotkeyListener, OutputHandler, SystemTray
    from src.backends import KEY_NAME_TO_VK, OutputError, STATUS_COLORS

These names always resolve to the correct concrete class for the
current OS. No branching anywhere else in the codebase.
"""

import sys

if sys.platform == "win32":
    from .windows import (
        WindowsHotkeyListener as HotkeyListener,
        WindowsOutputHandler as OutputHandler,
        WindowsSystemTray as SystemTray,
        KEY_NAME_TO_VK,
        OutputError,
        STATUS_COLORS,
    )
elif sys.platform == "darwin":
    from .macos import (
        MacHotkeyListener as HotkeyListener,
        MacOutputHandler as OutputHandler,
        MacSystemTray as SystemTray,
        KEY_NAME_TO_VK,
        OutputError,
        STATUS_COLORS,
    )
else:
    raise RuntimeError(
        f"Unsupported platform: {sys.platform}. "
        f"Whisper VTT supports Windows (win32) and macOS (darwin) only."
    )
