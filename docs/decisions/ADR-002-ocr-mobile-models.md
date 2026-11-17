# ADR-002: Use PP-OCRv5 Mobile Models

**Status:** Accepted  
**Date:** 2026-11-16

## Context
PaddleOCR 3.7 defaults to `PP-OCRv6_medium` models, which are very slow on CPU (0.57 pages/min) and hit a oneDNN bug on Windows. We also needed reliable English OCR.

## Decision
We explicitly configure PaddleOCR with `text_detection_model_name="PP-OCRv5_mobile_det"` and `text_recognition_model_name="PP-OCRv5_mobile_rec"`, and disable oneDNN (`enable_mkldnn=False`). This yields ~2.13 pages/min with high confidence on textbook pages.

## Consequences
- ✅ Stable CPU performance.
- ✅ No oneDNN crash.
- ⚠️ ~2.4 hours for a 300-page book (acceptable for background ingestion).