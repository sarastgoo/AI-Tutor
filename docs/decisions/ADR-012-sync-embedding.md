# ADR-012: Synchronous embedding in P4

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P4

## Context

Embedding 4 chunks took 0.58 s. For a full textbook (~3000 chunks), expected time is ~11 s. This is acceptable for synchronous HTTP.

## Decision

Keep embedding synchronous in P4. Move to background job queue in P5 when the tutor graph needs async.

## Consequences

- ✅ Simple API.
- ✅ Fast enough for current scale (one page = 4 chunks).
- ⚠️ Books with >10000 chunks may exceed HTTP timeout.
- ⚠️ UI must show progress for large books.