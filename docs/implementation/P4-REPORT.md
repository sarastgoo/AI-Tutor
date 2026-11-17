# P4-REPORT — Knowledge Layer Complete

**Phase:** P4 (Knowledge Layer: Vocabulary + Embeddings)  
**Status:** ✅ COMPLETE  
**Date:** 2026-11-17  
**Next phase:** P5 (Tutor Graph + LangGraph)

---

## 1. What was delivered

| Deliverable | Location | Status |
|---|---|---|
| Vocabulary Service | `backend/app/services/vocabulary_service.py` | ✅ |
| Embedding Service | `backend/app/services/embedding_service.py` | ✅ |
| Vocabulary API | `backend/app/api/v1/vocabulary.py` | ✅ |
| Embeddings API | `backend/app/api/v1/embeddings.py` | ✅ |
| spaCy model | `en_core_web_sm` (installed) | ✅ |
| e5-small model | `intfloat/multilingual-e5-small` (cached) | ✅ |

---

## 2. Verified Capabilities

### Vocabulary Extraction (spaCy)

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Blocks processed | 72 | — | ✅ |
| Total occurrences | 237 | — | ✅ |
| Unique lexemes | 104 | — | ✅ |
| Extraction time | ~30 s | < 60 s | ✅ PASS |
| Top lemmas | `you` (37), `do` (19), `the` (9) | — | ✅ Expected |

### Chunking + Embeddings (e5-small)

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Chunks created | 4 | — | ✅ |
| Embeddings created | 4 | — | ✅ |
| Chunk length | 285–398 chars | ~400 target | ✅ PASS |
| Embedding time | 0.58 s | < 5 s | ✅ PASS |
| Embedding dimension | 384 | 384 | ✅ |

---

## 3. Known Issues & Deviations

### ADR-010: Chunk size = 400 characters (v1)

**Context:** The architecture spec suggests chunks should stay within learning node boundaries, but we don't have learning node mapping yet (that's P5). For P4, we chunk by character count as a first-pass.

**Decision:** Target ~400 characters per chunk, splitting on content block boundaries. This produces 4 chunks for 289 blocks (one page).

**Consequences:**
- ✅ Simple and fast.
- ⚠️ Chunks may span multiple lessons. Will be improved in P5 when node mapping is available.
- ⚠️ Very short or very long blocks are not split further.

### ADR-011: Source spans auto-created per content block

**Context:** The spec requires all vocabulary occurrences to link to a `SourceSpan` for provenance. In P2, we only created `ContentBlock` rows, not `SourceSpan` rows.

**Decision:** In P4, when processing a content block for vocabulary, we automatically create a `SourceSpan` if one doesn't exist (start_offset=0, end_offset=len(text), source_version=block.text_version). This makes provenance traceable without requiring re-ingestion.

**Consequences:**
- ✅ Every occurrence is traceable to its content block.
- ⚠️ One span per block (no sub-block granularity). Fine for v1; sub-block spans can be added later.

### ADR-012: Synchronous embedding (batch=32)

**Context:** Embedding 4 chunks took 0.58 s (very fast). For a full textbook (~3000 chunks), expected time is ~11 s.

**Decision:** Keep embedding synchronous in P4 (matches the P2/P3 pattern). Will move to background job in P5 when job queue is introduced.

**Consequences:**
- ✅ Fast enough for current scale.
- ⚠️ Large books (>10000 chunks) may hit HTTP timeouts; background worker needed.

---

## 4. Test Results

### Vocabulary Extraction
