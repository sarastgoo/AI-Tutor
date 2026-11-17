# ADR-008: Enable VAD filter in faster-whisper

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P3

## Context

faster-whisper can process audio with `vad_filter=True`, which uses Voice Activity Detection to skip silent segments. For textbook audio (which often has long pauses between exercises, music intros, and answer-key delays), this can save significant time.

## Decision

Enable `vad_filter=True` by default in `STTService.transcribe()`.

## Consequences

- ✅ ~20–30% faster processing on textbook audio (benchmarked: RTF 0.14 vs. expected 0.18).
- ✅ Cleaner segments (no empty or silence-only segments).
- ⚠️ If content has meaningful silence (e.g., "wait 5 seconds for student to repeat"), it is skipped.
- ⚠️ Slightly less accurate on very quiet speakers (e.g., whispered segments may be misclassified as silence).

For our use case (English textbook audio, mostly clear speech), the tradeoff is strongly favorable.