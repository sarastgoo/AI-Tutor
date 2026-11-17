# ADR-019: Use qwen2.5:3b-instruct for JSON tasks

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P8

## Context

Qwen3 4B (reasoning model) consistently produces empty `content` when `format="json"` is used. It puts reasoning in `thinking` but doesn't complete JSON in `content`.

## Decision

For strict JSON tasks (enrichment, structured output), use `qwen2.5:3b-instruct`. This model honors `format="json"` reliably and runs faster.

For conversational tutoring (where reasoning quality matters), continue using `qwen3:4b`.

## Consequences

- ✅ Reliable JSON output for enrichment.
- ✅ Faster enrichment (~3s/word).
- ⚠️ Two models loaded in memory: qwen3:4b (2.5 GB) + qwen2.5:3b-instruct (1.9 GB) = ~4.4 GB VRAM. Fits in 6 GB but leaves less headroom.
- ⚠️ Model selection must be explicit per task (not automatic fallback).