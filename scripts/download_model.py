"""Download whisper model file for offline bundling."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Download a whisper model for offline use."
    )
    parser.add_argument(
        "model",
        nargs="?",
        default="tiny.en",
        help="Model name or size (default: tiny.en)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output path (default: models/<model>.pt)",
    )
    args = parser.parse_args()

    model_name = args.model
    output_path = Path(args.output) if args.output else Path(f"models/{model_name}.pt")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading model: {model_name}")

    try:
        import whisper
    except ImportError:
        print("ERROR: openai-whisper not installed.", file=sys.stderr)
        print("Install with: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    try:
        # whisper.load_model downloads and caches the model
        _ = whisper.load_model(model_name, device="cpu")
        print(f"Model '{model_name}' downloaded and cached by whisper.")
    except Exception as e:
        print(f"ERROR loading model: {e}", file=sys.stderr)
        sys.exit(1)

    # Whisper caches downloaded models in ~/.cache/whisper/
    # Find the cached file and copy it to our output location
    import shutil

    cache_dir = Path.home() / ".cache" / "whisper"
    cached_model = cache_dir / f"{model_name}.pt"

    if cached_model.exists():
        shutil.copy2(cached_model, output_path)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"Model copied to: {output_path} ({size_mb:.1f} MB)")
    else:
        print(f"WARNING: Could not find cached model at {cached_model}", file=sys.stderr)
        print("The model is loaded in memory but file location is unknown.", file=sys.stderr)
        print(f"Try running whisper once first, or manually place the .pt file at {output_path}",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
