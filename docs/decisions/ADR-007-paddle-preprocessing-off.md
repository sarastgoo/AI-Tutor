# ADR-007: Disable PaddleOCR document preprocessing

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P2

## Context

PaddleOCR's default pipeline includes two preprocessors:
- `UVDoc` (document unwarping) — corrects perspective distortion.
- `doc_orientation_classify` — detects and rotates upside-down scans.

These add 2 extra model loads (~30 MB each) and slowed init time from 6.8 s to 23.9 s. They also caused the UVDoc `inference.yml` permission errors in P2.

## Decision

Set both `use_doc_unwarping=False` and `use_doc_orientation_classify=False`. For clean, upright textbook scans (our primary use case), these preprocessors provide marginal benefit and significant latency cost.

## Consequences

- ✅ Init time down from 23.9 s to 6.8 s.
- ✅ No more UVDoc permission errors.
- ⚠️ Skewed or upside-down scans will OCR poorly. If encountered in a future book, we can re-enable per-book via a config flag.