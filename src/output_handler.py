"""Output handler — delivers transcribed text via clipboard."""

import logging
import subprocess

from src.models import OutputMode

logger = logging.getLogger(__name__)


class OutputError(Exception):
    """Raised when text delivery fails."""


class OutputHandler:
    """Delivers transcribed text to the user.

    Two modes:
    - AUTO_PASTE: Sets clipboard, then tries to simulate Ctrl+V via
      SendInput (VDI environments often block this, so it falls back
      to clipboard-only).
    - CLIPBOARD: Sets clipboard text for manual paste by the user.
    """

    def __init__(self, mode: OutputMode = OutputMode.AUTO_PASTE):
        self._mode = mode

    @property
    def mode(self) -> OutputMode:
        return self._mode

    @mode.setter
    def mode(self, value: OutputMode) -> None:
        self._mode = value

    def deliver(self, text: str) -> None:
        """Deliver transcribed text according to the configured mode.

        Args:
            text: The transcribed text to deliver.

        Raises:
            OutputError: If clipboard access fails and fallback also fails.
        """
        if not text:
            return

        # Set clipboard — this always happens regardless of mode
        self._set_clipboard(text)

        if self._mode == OutputMode.AUTO_PASTE:
            self._simulate_paste()

    def _set_clipboard(self, text: str) -> None:
        """Set the Windows clipboard to the given text.

        Tries win32clipboard first, falls back to clip.exe subprocess.
        """
        # Strategy 1: win32clipboard
        try:
            import win32clipboard

            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                logger.info("Clipboard set via win32clipboard: %r", text[:50])
                return
            finally:
                win32clipboard.CloseClipboard()
        except ImportError:
            logger.debug("pywin32 not available, trying clip.exe fallback.")
        except Exception as e:
            logger.warning("win32clipboard failed: %s. Trying clip.exe fallback.", e)

        # Strategy 2: clip.exe subprocess
        try:
            subprocess.run(
                ["clip.exe"],
                input=text,
                text=True,
                check=True,
                capture_output=True,
            )
            logger.info("Clipboard set via clip.exe: %r", text[:50])
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            raise OutputError(
                f"Could not set clipboard: {e}"
            ) from e

    def _simulate_paste(self) -> None:
        """Attempt to simulate Ctrl+V via SendInput.

        In many VDI environments, SendInput is blocked. If it fails,
        we silently fall back — the text is already on the clipboard.
        """
        try:
            import win32com.client

            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys("^v")
            logger.info("Simulated Ctrl+V paste.")
        except ImportError:
            logger.debug("win32com not available — paste simulation skipped.")
        except Exception as e:
            # VDI environments often block this — not an error
            logger.debug("SendInput paste blocked or unavailable: %s", e)
