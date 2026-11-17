# P2-REPORT — PDF Ingestion Complete

**Phase:** P2 (PDF Ingestion)  
**Status:** ✅ COMPLETE  
**Date:** 2026-11-17  
**Next phase:** P3 (Audio Ingestion)

---

## 1. What was delivered

| Deliverable | Location | Status |
|---|---|---|
| OCR Service | `backend/app/services/ocr_service.py` | ✅ |
| Ingestion Service | `backend/app/services/ingestion_service.py` | ✅ |
| Books API (CRUD) | `backend/app/api/v1/books.py` | ✅ |
| Import-local endpoint | `POST /api/v1/books/{id}/import-local` | ✅ |
| Local model paths | `C:\Projects\ai-english-tutor\models\` | ✅ |
| Test scripts | `scripts/run_ocr_test.py`, `scripts/run_ingestion_test.py` | ✅ |

---

## 2. Verified Capabilities

### OCR (PaddleOCR PP-OCRv5 mobile)

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Blocks per page (avg) | 97 | — | ✅ |
| Confidence threshold | ≥ 0.3 (filtered) | — | ✅ |
| Time per page (CPU) | ~40 s | < 60 s | ✅ PASS |
| Sample text | `"Are you? Can you? Do you? Did you?"` | — | ✅ |

### Ingestion

| Operation | Result | Status |
|---|---|---|
| 1 page | 72 blocks / 26.76 s | ✅ |
| 3 pages | 290 blocks / 121.5 s | ✅ |
| Deduplication (SHA-256) | Same hash → same source_file | ✅ |

---

## 3. Known Issues & Deviations (with ADRs)

### ADR-006: Local model directory for OCR

**Context:** PaddleOCR's default model location is under `C:\Users\<user>\.paddlex`, but Windows Defender (or system policies) intermittently blocked reading `inference.yml` files from that hidden location, especially when called from a subprocess (uvicorn).

**Decision:** Copy the models to `C:\Projects\ai-english-tutor\models\` and configure PaddleOCR to load from there via `text_detection_model_dir` and `text_recognition_model_dir`.

**Consequences:**
- ✅ Stable, predictable model loading.
- ✅ No antivirus interference.
- ⚠️ Duplicate storage (~30 MB per model).
- ⚠️ Setup scripts must copy models on fresh install.

**Additional required fix:** Must pass BOTH `text_detection_model_dir` and `text_detection_model_name` (similarly for rec) when using local directories. Otherwise PaddleOCR 3.x tries to auto-resolve the model name to `PP-OCRv6_medium_det` and raises `Model name mismatch`.

### ADR-007: Disable PaddleOCR image preprocessor features

**Context:** PaddleOCR's default pipeline includes `UVDoc` (document unwarping) and `doc_orientation_classify`, which add extra model loads and permissions issues on Windows.

**Decision:** Explicitly set `use_doc_unwarping=False` and `use_doc_orientation_classify=False`. For our use case (already-upright textbook scans), these are unnecessary and add latency + failure modes.

**Consequences:**
- ✅ Faster initialization (23.9 s → 6.8 s).
- ✅ No more UVDoc permission errors.
- ⚠️ Might matter for skewed/rotated scans; if we encounter these, we can re-enable per-book.

---

## 4. Test Results

### OCR Test (3 pages, DPI 250)
