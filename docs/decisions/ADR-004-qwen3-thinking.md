# ADR-004: Qwen3 Reasoning Tokens

**Status:** Accepted  
**Date:** 2026-11-16

## Context
Qwen3 4B is a reasoning model. Ollama 0.40.16 does not honor the `think=false` flag on `/api/generate`, so responses include long reasoning chains. This slightly increases latency.

## Decision
We will use Qwen3 4B as-is in P1. Later phases (P5) will use the `/api/chat` endpoint or adjust prompts to suppress reasoning where not needed.

## Consequences
- ✅ Model is safe and available.
- ⚠️ Slightly longer responses; parsing must tolerate leading reasoning text if format=json is not fully honored.