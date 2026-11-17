# ADR-016: Handle empty feedback from Qwen3

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P6

## Context

Qwen3 4B is a reasoning model. When `num_predict` is too small (e.g., 400), the model may spend all its tokens on reasoning and leave `content` empty.

## Decision

Increase `num_predict` to 1000 in `speaking.py` when calling `llm.chat`.

## Consequences

- ✅ Fixes empty feedback.
- ⚠️ Slightly longer latency (~40s instead of ~30s).

## Future (P7+)

- Parse both `content` and `thinking` from Ollama's response. If `content` is empty but `thinking` contains structured feedback, extract feedback from `thinking`.
- Alternatively, use a more capable model (e.g., Qwen2.5 3B Instruct, non-reasoning) for feedback generation only.