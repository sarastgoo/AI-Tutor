# ADR-009: Synchronous transcription in P3

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P3

## Context

For a 3.5-minute audio, transcription takes ~31 s (RTF 0.14). For 2-hour audio, this would be ~17 minutes — far exceeding typical HTTP timeouts. The architecture spec requires background jobs for long operations.

## Decision

For P3 (small audio files, ~3-5 min each), keep transcription **synchronous** for simplicity. Long-running jobs will be handled in P4 via `ingestion_jobs` table.

## Consequences

- ✅ Simpler API in P3.
- ✅ Easier testing.
- ⚠️ UI must show loading state (~30 s per file).
- ⚠️ Files longer than 15 minutes will likely time out; will require P4 background worker.
- ⚠️ Migration path: `transcribe-local` will accept an optional `async=true` flag in P4, returning 202 with a job ID.

This ADR will be superseded by ADR-XXX in P4 when the background job queue is implemented.