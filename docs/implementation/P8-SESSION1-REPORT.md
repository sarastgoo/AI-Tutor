# P8-Session1-REPORT — Enrichment Complete

**Phase:** P8-Session 1 (Enrichment)  
**Status:** ✅ COMPLETE  
**Date:** 2026-11-17

---

## 1. What was delivered

| Deliverable | Location | Status |
|---|---|---|
| Enrichment Service | `backend/app/services/enrichment_service.py` | ✅ |
| Enrichment API | `backend/app/api/v1/enrichment.py` | ✅ |
| Model switch to `qwen2.5:3b-instruct` | In service `__init__` | ✅ |

---

## 2. Verified Capabilities

| Metric | Value | Status |
|---|---|---|
| Enrichment success | 2/2 (100%) | ✅ |
| Time per word | ~3 s | ✅ |
| Persian meaning populated | Yes | ✅ |
| IPA populated (when model provides it) | Varies | ✅ |

---

## 3. ADR-019: Use qwen2.5:3b-instruct for JSON tasks

**Context:** Qwen3 4B (reasoning model) consistently put output in `thinking` instead of `content` when `format="json"`. Even with `num_predict=500`, the JSON was sometimes incomplete.

**Decision:** Use `qwen2.5:3b-instruct` (non-reasoning) for enrichment and any future strict-JSON tasks. It honors `format="json"` reliably, is smaller, and runs faster on CPU.

**Consequences:**
- ✅ Reliable JSON output.
- ✅ ~3 s per word (vs. 20+ s with qwen3).
- ⚠️ Slightly lower quality on complex explanations (but for dictionary-style translation, quality is sufficient).
- ⚠️ Two models must be loaded in Ollama (qwen3:4b for tutor, qwen2.5:3b-instruct for JSON).

---

## 4. Known Limitations

- Enrichment is synchronous and one-by-one. For 104 lexemes, total time ~5 min. Acceptable for one-shot batch.
- No retry on transient failures (will add in P8-Hardening).
- Example sentences are generated, not from the book (marked `example_origin="generated"` per spec).
- Model may occasionally provide inaccurate IPA (not validated).

---

## 5. Next Steps (P8-Session 2)

- Speaking UI (frontend recording page)
- Offline test