"""macOS backend implementations -- stubs pending implementation.

Will contain: MacHotkeyListener (Quartz event tap), MacOutputHandler
(pbcopy + osascript Cmd+V), MacSystemTray (rumps menu bar app).
"""

import logging
from typing import Callable, Optional

from PIL import Image, ImageDraw

from src.models import AppStatus, HotkeyCombo, HotkeyEvent, OutputMode

logger = logging.getLogger(__name__)

# Re-export KEY_NAME_TO_VK for the factory -- same key names on all platforms.
KEY_NAME_TO_VK: dict[str, int] = {}


class OutputError(Exception):
    """Raised when text delivery fails."""


# Placeholder -- same color scheme as Windows
ICON_SIZE = 64
STATUS_COLORS = {
    AppStatus.IDLE: (0, 180, 0),
    AppStatus.RECORDING: (220, 30, 30),
    AppStatus.TRANSCRIBING: (255, 165, 0),
    AppStatus.ERROR: (128, 128, 128),
}


class MacHotkeyListener:
    """Quartz event tap hotkey listener -- NOT YET IMPLEMENTED."""

    def __init__(self, hotkey: HotkeyCombo):
        self._hotkey = hotkey
        self._running = False
        raise NotImplementedError("MacHotkeyListener not yet implemented")

    def set_on_activated(self, callback: Callable[[HotkeyEvent], None]) -> None:
        pass

    def set_on_released(self, callback: Callable[[HotkeyEvent], None]) -> None:
        pass

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        raise NotImplementedError("MacHotkeyListener not yet implemented")

    def stop(self) -> None:
        pass


class MacOutputHandler:
    """pbcopy + osascript output handler -- NOT YET IMPLEMENTED."""

    def __init__(self, mode: OutputMode = OutputMode.AUTO_PASTE):
        self._mode = mode

    @property
    def mode(self) -> OutputMode:
        return self._mode

    @mode.setter
    def mode(self, value: OutputMode) -> None:
        self._mode = value

    def deliver(self, text: str) -> None:
        raise NotImplementedError("MacOutputHandler not yet implemented")


class MacSystemTray:
    """rumps menu bar app -- NOT YET IMPLEMENTED."""

    def __init__(self, title: str = "Whisper VTT"):
        self._title = title
        self._status: AppStatus = AppStatus.IDLE

    @property
    def status(self) -> AppStatus:
        return self._status

    def set_on_exit(self, callback: Callable[[], None]) -> None:
        pass

    def set_status(self, status: AppStatus) -> None:
        self._status = status

    def show_notification(
        self, title: str, message: str, *, play_sound: bool = True
    ) -> None:
        pass

    def start(self) -> None:
        raise NotImplementedError("MacSystemTray not yet implemented")

    def stop(self) -> None:
        pass

    @staticmethod
    def _generate_icon(status: AppStatus) -> "Image.Image":
        color = STATUS_COLORS.get(status, STATUS_COLORS[AppStatus.IDLE])
        image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        margin = 4
        draw.ellipse(
            [margin, margin, ICON_SIZE - margin, ICON_SIZE - margin],
            fill=color,
        )
        return image
