
# ADR-006: Local OCR model directory

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P2

## Context

PaddleOCR defaults to storing models under `C:\Users\<user>\.paddlex\official_models\`. When the API server (uvicorn) launched as a subprocess calls PaddleOCR, Windows Defender intermittently returned `PermissionError: [Errno 13]` on `inference.yml` files inside that hidden directory.

Additionally, PaddleOCR 3.x by default resolves model names to `PP-OCRv6_medium_det` even when a directory is provided. When both `model_dir` and `model_name` disagree, it raises `Model name mismatch`.

## Decision

1. Copy `PP-OCRv5_mobile_det` and `PP-OCRv5_mobile_rec` model folders into `C:\Projects\ai-english-tutor\models\`.
2. Configure PaddleOCR with BOTH:
   - `text_detection_model_dir=<local path>`
   - `text_detection_model_name="PP-OCRv5_mobile_det"`
   - (and the same for `_rec`).
3. Add `models/` to `.gitignore` to avoid committing binary model weights.
4. Provide a setup script (see P3) to copy models on fresh installs.

## Consequences

- ✅ Stable, predictable model loading from a directory owned by the project.
- ✅ No antivirus interference.
- ⚠️ Duplicate storage (~30 MB per model pair).
- ⚠️ Must include model files in deployment (already local-first).