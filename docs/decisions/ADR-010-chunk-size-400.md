# ADR-010: Chunk size = 400 characters (v1)

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P4

## Context

The architecture spec (section 6.8) says: "Chunk within node boundaries when possible; map chunks to multiple source spans". However, learning node mapping is not built until P5. For P4, we need a simple chunking strategy.

## Decision

Target ~400 characters per chunk, splitting on content block boundaries. This produces reasonable chunks for textbook passages (~2-3 sentences each).

## Consequences

- ✅ Simple to implement and understand.
- ✅ Fast: 4 chunks for 289 blocks in 0.58 s.
- ⚠️ Chunks may span multiple lessons or exercises.
- ⚠️ Will need re-chunking when node mapping is added (P5). Add migration for `chunk_source_spans` update.
- ⚠️ Very long blocks (>400 chars) are not further split.