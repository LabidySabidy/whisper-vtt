"""PyInstaller build script for Whisper VTT."""

import shutil
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    dist_dir = project_root / "dist" / "Whisper-VTT"
    models_dir = dist_dir / "models"
    model_name = "ggml-base.en.bin"

    print("=" * 60)
    print("Whisper VTT - PyInstaller Build")
    print(f"  Engine: pywhispercpp (whisper.cpp GGML)")
    print(f"  Model:  {model_name}")
    print("=" * 60)

    # Find or download the GGML model
    print(f"\nLocating model '{model_name}'...")
    import pywhispercpp.model

    cache_dir = (
        Path(pywhispercpp.model._MODELS_DIR)
        if hasattr(pywhispercpp.model, "_MODELS_DIR")
        else Path.home() / "AppData" / "Local" / "pywhispercpp" / "pywhispercpp" / "models"
    )
    cached_model = cache_dir / model_name
    local_model = project_root / "models" / model_name

    if local_model.exists():
        print(f"  Found: {local_model} ({local_model.stat().st_size / (1024 * 1024):.1f} MB)")
    elif cached_model.exists():
        local_model.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached_model, local_model)
        print(f"  Copied from cache: {cached_model} -> {local_model}")
    else:
        print(f"  WARNING: Model not found. Download with: python scripts/download_model.py")

    print("\nRunning PyInstaller...")
    import PyInstaller.__main__

    pyinstaller_args = [
        str(project_root / "src" / "__main__.py"),
        "--onedir",
        "--name=Whisper-VTT",
        "--distpath", str(project_root / "dist"),
        "--workpath", str(project_root / "build"),
        "--specpath", str(project_root),
        "--noconfirm",
        f"--icon={project_root / 'whisper_vtt.ico'}",
        "--hidden-import=sounddevice",
        "--hidden-import=_sounddevice_data",
        "--hidden-import=numpy",
        "--hidden-import=pystray",
        "--hidden-import=PIL",
        "--hidden-import=win32clipboard",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        "--hidden-import=pywhispercpp",
        "--hidden-import=pocketsphinx",
        "--collect-all=pywhispercpp",
        "--collect-all=pocketsphinx",
        "--runtime-hook=scripts/runtime_hook.py",
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=pytest",
        "--exclude-module=hypothesis",
        "--exclude-module=torch",
        "--exclude-module=whisper",
        "--exclude-module=faster_whisper",
        "--exclude-module=ctranslate2",
        "--exclude-module=tiktoken",
        "--exclude-module=sympy",
        "--exclude-module=numba",
        "--exclude-module=llvmlite",
        "--exclude-module=onnxruntime",
        "--exclude-module=scikit-learn",
        "--exclude-module=openwakeword",
        "--console",
    ]

    PyInstaller.__main__.run(pyinstaller_args)

    # Copy model
    models_dir.mkdir(parents=True, exist_ok=True)
    if local_model.exists():
        dest = models_dir / model_name
        shutil.copy2(local_model, dest)
        print(f"Copied model: {dest}")

    # Preserve existing config in dist, or copy from project root
    config_src = project_root / "config.toml"
    config_dest = dist_dir / "config.toml"
    if config_src.exists():
        if config_dest.exists():
            print(f"Existing config preserved: {config_dest}")
        else:
            print(f"Copying config: {config_src} -> {config_dest}")
            shutil.copy2(config_src, config_dest)

    zip_path = project_root / "dist" / "Whisper-VTT.zip"
    print(f"\nCreating zip: {zip_path}")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(
        str(zip_path.with_suffix("")), "zip",
        str(dist_dir.parent), dist_dir.name,
    )

    print("\n" + "=" * 60)
    print("Build complete!")
    print(f"  Folder: {dist_dir}")
    print(f"  Zip:    {zip_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
