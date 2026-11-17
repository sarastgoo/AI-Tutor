# ADR-018: Defer pronunciation scoring

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P6

## Context

The architecture spec requires pronunciation scoring to be `not_assessed` until a validated acoustic/phoneme model exists. STT confidence is not a proxy for pronunciation quality.

## Decision

In P6, `pronunciation_status` is hardcoded to `not_assessed`. We do not attempt any pronunciation scoring.

## Consequences

- ✅ Honest, spec-compliant behavior.
- ✅ No risk of misleading scores.
- ⚠️ Users won't get pronunciation feedback yet.
- ⚠️ Future phases may add a validated model (e.g., Wav2Vec2 + phoneme alignment), after independent evaluation.

## Alternatives considered

- **Use STT confidence as pronunciation score:** rejected (misleading; STT confidence reflects audio quality and accent, not intelligibility).
- **Use speech recognition difference:** rejected (measures word error, not pronunciation).
- **Skip entirely:** chosen for P6. P8+ will revisit with a proper model.