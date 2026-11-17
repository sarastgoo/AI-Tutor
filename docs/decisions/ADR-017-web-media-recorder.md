# ADR-017: Use native MediaRecorder for browser audio

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P6 (frontend will be in P7)

## Context

The frontend needs to record microphone audio and upload it to the backend.

## Decision

Use the browser's native `MediaRecorder` API:
- `navigator.mediaDevices.getUserMedia({ audio: true })` to request permission.
- `new MediaRecorder(stream)` to record.
- Output format: `audio/webm` (Chrome default) — faster-whisper supports WebM via `av`.

## Consequences

- ✅ No external library.
- ✅ Works in Chrome, Edge, Firefox.
- ⚠️ Safari produces `audio/mp4`; may need later support.
- ⚠️ WebM is more compact than WAV; STT quality unaffected.