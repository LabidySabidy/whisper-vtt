"""Path resolution for source and PyInstaller-bundled runs."""

import sys
from pathlib import Path


class PathResolver:
    """Resolves paths relative to the application root.

    When running from source, the root is the project directory
    (parent of src/). When running from a PyInstaller bundle
    (sys.frozen is True), the root is the directory containing
    the executable.
    """

    @staticmethod
    def base_path() -> Path:
        if getattr(sys, "frozen", False):
            # PyInstaller bundle: exe directory
            return Path(sys.executable).parent
        else:
            # Running from source: project root (parent of src/)
            return Path(__file__).resolve().parent.parent

    @classmethod
    def resolve(cls, relative_path: str | Path) -> Path:
        """Resolve a relative path against the application root."""
        return cls.base_path() / relative_path

    @classmethod
    def config_path(cls, filename: str = "config.toml") -> Path:
        """Path to the config file adjacent to the exe / project root."""
        return cls.resolve(filename)

    @classmethod
    def model_path(cls, relative: str = "models/ggml-base.en.bin") -> Path:
        """Path to the whisper model file."""
        return cls.resolve(relative)

    @classmethod
    def log_path(cls, filename: str = "dictation.log") -> Path:
        """Path to the runtime log file."""
        return cls.resolve(filename)
