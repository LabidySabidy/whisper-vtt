# Plan — Model upgrade + banner polish

## Goal
Upgrade from tiny to base model for better accuracy, and fix the startup banner layout: all-orange borders, octopus art, proper column alignment, ANSI-aware widths.

## Approach
Model upgrade is mechanical — change default model path everywhere, download `ggml-base.en.bin`. Banner fix requires rewriting the `_Term.header()` method to handle ANSI escape codes when measuring string widths (strip codes before `len()`), ensuring the center divider aligns properly. Also reorder left-column content (welcome above art) and replace ASCII art with octopus.

## Phases

1. **Model upgrade to ggml-base** — download model, update all references, tests
2. **Banner layout fixes** — ANSI-aware width, orange everywhere, octopus, alignment, right-column no-border

## Files that will change

| File | Change | Phase |
|---|---|---|
| `src/config_manager.py` | `DEFAULT_MODEL_PATH = "models/ggml-base.en.bin"` | 1 |
| `src/paths.py` | Default model path updated | 1 |
| `config.toml` | `path = "models/ggml-base.en.bin"` | 1 |
| `scripts/build.py` | `model_name = "ggml-base.en.bin"` | 1 |
| `tests/test_config_manager.py` | Update expected model path | 1 |
| `tests/test_paths.py` | Update expected model path | 1 |
| `tests/test_models.py` | Update expected model path | 1 |
| `tests/test_app_controller.py` | Update expected model path | 1 |
| `src/__main__.py` | `_Term.header()` rewrite: ANSI-aware widths, orange border/title, octopus, welcome-back order | 2 |

## Acceptance criteria

- [ ] `ggml-base.en.bin` model is downloaded and bundled in dist
- [ ] 168 tests pass with new model path
- [ ] Banner has orange borders on all sides including top title bar
- [ ] "Whisper VTT" text in the title is orange
- [ ] "Welcome back!" appears above the octopus art
- [ ] Octopus ASCII art replaces old triangular art
- [ ] Left column text stays within its boundary (no overflow past center divider)
- [ ] Right column has text properly aligned, no right-side border line
- [ ] Center divider is evenly spaced between columns
- [ ] Build succeeds

## Not in scope

- Changing model reload interval
- Adding more model options to config
- Hiding "Progress: X%" lines (tried, caused crashes)
- Changing dictation-cycle console output

## Open questions

None

## Current step

Not started

## Notes

-
