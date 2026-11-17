# ADR-003: Pin `av` to <19

**Status:** Accepted  
**Date:** 2026-11-16

## Context
The default `av` (PyAV) 19 removed the `metadata_errors` keyword argument, which faster-whisper 1.2.1 still passes. This caused a `TypeError` at runtime.

## Decision
We install `av>=18,<19` in `requirements.txt` and `requirements-p0.lock.txt`. This is the latest major version compatible with faster-whisper 1.2.1.

## Consequences
- ✅ faster-whisper works reliably.
- ⚠️ Must upgrade `av` and `faster-whisper` together when newer versions fix this.