# ADR-015: Bootstrap default user on first session

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P5

## Context

`learning_sessions.user_id` is `NOT NULL` per the architecture spec. P5 has no auth and no user profile UI yet.

## Decision

In `POST /api/v1/tutor/sessions`, query for any existing user. If none exists, create a default `User(display_name="Local Learner")` inline. Subsequent sessions reuse that user.

## Consequences

- ✅ Single-user local workflow works immediately.
- ✅ No migration change required.
- ⚠️ When multi-user is added (P8+), the inline bootstrap must be replaced with proper auth.
- ⚠️ The default user id is stable but unnamed per-session; if we later add a "Welcome" flow, we may want to let the user rename it.