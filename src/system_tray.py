"""System tray icon and notifications."""

import logging
import threading
from typing import Callable, Optional

from PIL import Image, ImageDraw

from src.models import AppStatus

logger = logging.getLogger(__name__)

# Icon sizes and colors
ICON_SIZE = 64
STATUS_COLORS = {
    AppStatus.IDLE: (0, 180, 0),         # Green
    AppStatus.RECORDING: (220, 30, 30),   # Red
    AppStatus.TRANSCRIBING: (255, 165, 0), # Orange
    AppStatus.ERROR: (128, 128, 128),     # Gray
}


class SystemTray:
    """System tray icon with status indicator and exit menu.

    Uses pystray with Pillow-generated colored circle icons.
    Runs on its own daemon thread.
    """

    def __init__(self, title: str = "Whisper VTT"):
        self._title = title
        self._status: AppStatus = AppStatus.IDLE
        self._tray_icon: Optional[object] = None
        self._on_exit: Optional[Callable[[], None]] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def status(self) -> AppStatus:
        return self._status

    def set_on_exit(self, callback: Callable[[], None]) -> None:
        """Set callback invoked when user clicks Exit."""
        self._on_exit = callback

    def set_status(self, status: AppStatus) -> None:
        """Update the tray icon to reflect the new status."""
        self._status = status
        if self._tray_icon is not None:
            self._tray_icon.icon = self._generate_icon(status)

    def show_notification(self, title: str, message: str) -> None:
        """Show a balloon notification."""
        if self._tray_icon is not None:
            try:
                self._tray_icon.notify(message, title)
            except Exception as e:
                logger.warning("Failed to show notification: %s", e)

    def start(self) -> None:
        """Start the system tray on a daemon thread."""

        self._thread = threading.Thread(
            target=self._run_tray,
            daemon=True,
            name="system-tray",
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the system tray icon."""
        if self._tray_icon is not None:
            self._tray_icon.stop()

    def _run_tray(self) -> None:
        """Run the pystray event loop (blocking on this thread)."""
        import pystray

        icon = self._generate_icon(self._status)
        menu = pystray.Menu(
            pystray.MenuItem("Exit", self._on_exit_clicked),
        )

        self._tray_icon = pystray.Icon(
            name=self._title,
            title=self._title,
            icon=icon,
            menu=menu,
        )

        try:
            self._tray_icon.run()
        except Exception as e:
            logger.error("System tray error: %s", e)

    def _on_exit_clicked(self, icon, item) -> None:
        """Handle Exit menu click."""
        if self._on_exit:
            self._on_exit()
        if self._tray_icon:
            self._tray_icon.stop()

    @staticmethod
    def _generate_icon(status: AppStatus) -> Image.Image:
        """Generate a colored circle icon for the given status."""
        color = STATUS_COLORS.get(status, STATUS_COLORS[AppStatus.IDLE])
        image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw filled circle
        margin = 4
        draw.ellipse(
            [margin, margin, ICON_SIZE - margin, ICON_SIZE - margin],
            fill=color,
        )

        return image
