# ADR-014: Accept Qwen3 reasoning tokens in P5

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P5

## Context

Qwen3 4B is a reasoning model. Ollama 0.40.16 does not expose a `think=false` flag that fully suppresses reasoning chains. Responses therefore include occasional reasoning text, and latency is ~30s for a 2-paragraph answer.

## Decision

Accept Qwen3's reasoning as-is for P5. Do not try to strip or filter it.

## Consequences

- ✅ Model produces high-quality grounded answers.
- ⚠️ Responses can be verbose; latency up to 60s for complex questions.
- ⚠️ Future options (P6+):
  - Add system prompt: "Answer concisely. Do not show your thinking."
  - Parse `response` and `thinking` fields separately (if Ollama exposes both in `/api/chat`).
  - Add streaming (SSE) to show partial output progressively.