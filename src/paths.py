"""Path resolution for source and PyInstaller-bundled runs.

Platform-aware: on macOS .app bundles, user-writable files go to
~/Library instead of next to the executable.
"""

import sys
from pathlib import Path


class PathResolver:
    """Resolves paths relative to the application root.

    When running from source, the root is the project directory
    (parent of src/). When running from a PyInstaller bundle
    (sys.frozen is True), the root is the directory containing
    the executable. On macOS .app bundles, user-writable files
    (config, logs) go to ~/Library/Application Support/.
    """

    @staticmethod
    def base_path() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).resolve().parent.parent

    @classmethod
    def resolve(cls, relative_path: str | Path) -> Path:
        return cls.base_path() / relative_path

    @classmethod
    def config_path(cls, filename: str = "config.toml") -> Path:
        if sys.platform == "darwin" and getattr(sys, "frozen", False):
            base = Path.home() / "Library" / "Application Support" / "Whisper-VTT"
        else:
            base = cls.base_path()
        base.mkdir(parents=True, exist_ok=True)
        return base / filename

    @classmethod
    def model_path(cls, relative: str = "models/ggml-base.en.bin") -> Path:
        return cls.resolve(relative)

    @classmethod
    def log_path(cls, filename: str = "dictation.log") -> Path:
        if sys.platform == "darwin":
            base = Path.home() / "Library" / "Logs" / "Whisper-VTT"
        else:
            base = cls.base_path()
        base.mkdir(parents=True, exist_ok=True)
        return base / filename
