"""PyInstaller build script for Whisper VTT.

Packages the app as a portable --onedir folder containing
the executable, all dependencies, the whisper model, and
a default config.toml.
"""

import shutil
import sys
from pathlib import Path


def main():
    # Ensure we're in the project root
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    dist_dir = project_root / "dist" / "Whisper-VTT"
    models_dir = dist_dir / "models"

    print("=" * 60)
    print("Whisper VTT — PyInstaller Build")
    print("=" * 60)

    # 1. Find the cached whisper model
    model_name = "tiny.en"
    cache_dir = Path.home() / ".cache" / "whisper"
    cached_model = cache_dir / f"{model_name}.pt"

    if cached_model.exists():
        print(f"Found cached model: {cached_model}")
        print(f"  Size: {cached_model.stat().st_size / (1024 * 1024):.1f} MB")
    else:
        print(f"WARNING: Cached model not found at {cached_model}")
        print("  Run 'python scripts/download_model.py' first to download the model.")
        print("  Continuing without model — you'll need to place it manually.")

    # 2. Run PyInstaller
    print("\nRunning PyInstaller...")
    import PyInstaller.__main__

    pyinstaller_args = [
        str(project_root / "src" / "__main__.py"),
        "--onedir",
        "--name=Whisper-VTT",
        "--distpath", str(project_root / "dist"),
        "--workpath", str(project_root / "build"),
        "--specpath", str(project_root),
        # Hidden imports
        "--hidden-import=sounddevice",
        "--hidden-import=_sounddevice_data",  # sounddevice native libs
        "--hidden-import=numpy",
        "--hidden-import=pystray",
        "--hidden-import=PIL",
        "--hidden-import=win32clipboard",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        "--hidden-import=whisper",
        "--hidden-import=torch",
        "--hidden-import=tiktoken",
        # Exclude heavy packages we don't use
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=pytest",
        "--exclude-module=hypothesis",
        # Collect whisper's asset files (mel_filters.npz, etc.)
        "--collect-all=whisper",
        # Console app (not windowed — shows log output)
        "--console",
    ]

    PyInstaller.__main__.run(pyinstaller_args)

    # 3. Copy model file into dist
    models_dir.mkdir(parents=True, exist_ok=True)
    if cached_model.exists():
        dest = models_dir / f"{model_name}.pt"
        print(f"\nCopying model: {cached_model} -> {dest}")
        shutil.copy2(cached_model, dest)
    else:
        print(f"\nWARNING: No model copied. Place {model_name}.pt in {models_dir} manually.")

    # 4. Copy default config
    config_src = project_root / "config.toml"
    if config_src.exists():
        config_dest = dist_dir / "config.toml"
        print(f"Copying config: {config_src} -> {config_dest}")
        shutil.copy2(config_src, config_dest)

    # 5. Create zip
    zip_path = project_root / "dist" / "Whisper-VTT.zip"
    print(f"\nCreating zip: {zip_path}")
    shutil.make_archive(
        str(zip_path.with_suffix("")),
        "zip",
        str(dist_dir.parent),
        dist_dir.name,
    )

    # 6. Summary
    print("\n" + "=" * 60)
    print("Build complete!")
    print(f"  Folder: {dist_dir}")
    print(f"  Zip:    {zip_path}")
    print("=" * 60)
    print("\nShare the zip file. Recipients unzip and double-click Whisper-VTT.exe.")


if __name__ == "__main__":
    main()
