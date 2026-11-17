# P7-Session1-REPORT — Backend Exports & Progress

**Phase:** P7-Session 1 (Backend)  
**Status:** ✅ COMPLETE  
**Date:** 2026-11-17  
**Next:** P7-Session 2 (Frontend UI)

---

## 1. What was delivered

| Deliverable | Location | Status |
|---|---|---|
| Export Service (DOCX) | `backend/app/services/export_service.py` | ✅ |
| Exports API | `backend/app/api/v1/exports.py` | ✅ |
| Progress API | `backend/app/api/v1/progress.py` | ✅ |

---

## 2. Verified Capabilities

### DOCX Export

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Lexemes in export | 104 | = DB count | ✅ |
| Total occurrences | 237 | = DB count | ✅ |
| Generation time | 0.22 s | < 2 s | ✅ |
| Columns | #, Lemma, POS, Occurrences, Persian Meaning | — | ✅ |
| RTL support | not yet (P8) | — | ⚠️ |

### Progress API

| Metric | Value | Status |
|---|---|---|
| Sessions | 5 | ✅ |
| Messages | 2 | ✅ |
| Speaking attempts | 2 | ✅ |
| Unique lexemes | 104 | ✅ |
| Due reviews | 0 | ✅ |

---

## 3. Known Issues (to address in P8)

- **Persian meanings empty** (`—` in DOCX): enrichment not run yet. P8 will add lexeme enrichment via LLM.
- **RTL not implemented** in DOCX: `Persian Meaning` column is LTR. P8 will add RTL paragraph formatting.
- **OCR noise**: tokens like `awhere`, `frompoznan`, `yourpartner` are in the export. These are OCR artifacts (from P2). Future: add spell-correction stage.
- **Single-letter tokens** (`b`, `d`, `g`, `p`): likely exercise labels (`B`, `D`, etc.) misclassified as words. Future: filter tokens that appear isolated in exercise contexts.

---

## 4. Files Added
