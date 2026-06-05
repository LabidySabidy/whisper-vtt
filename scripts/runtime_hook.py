"""PyInstaller runtime hook: pre-load native DLLs before imports."""

import os
import sys
from pathlib import Path


def _preload_dlls():
    if not getattr(sys, "frozen", False):
        return

    import ctypes

    base = Path(sys.executable).parent / "_internal"
    kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)

    # Add all DLL directories before any imports
    for d in [base, base / "torch" / "lib"]:
        try:
            os.add_dll_directory(str(d))
        except OSError:
            pass

    # Pre-load runtime DLLs in dependency order
    for dll_name in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]:
        dll_path = base / dll_name
        if dll_path.exists():
            kernel32.LoadLibraryW(str(dll_path))


_preload_dlls()
