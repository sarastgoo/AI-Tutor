# ADR-011: Auto-create SourceSpan per content block

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P4

## Context

The spec requires all vocabulary occurrences to reference a `SourceSpan` for provenance. In P2, we only created `ContentBlock` rows. Occurrences need a foreign key to `source_spans`.

## Decision

When processing a content block for vocabulary, automatically create a `SourceSpan` (with `content_block_id=block.id`, `start_offset=0`, `end_offset=len(text)`, `source_version=block.text_version`) if one doesn't exist. This makes all occurrence chains traceable without re-ingestion.

## Consequences

- ✅ Every occurrence is traceable to its source block.
- ✅ No need to re-run OCR.
- ⚠️ One span per block (no sub-block granularity). Fine for v1.
- ⚠️ If `start_offset`/`end_offset` need to point to specific words, that's a future enhancement.