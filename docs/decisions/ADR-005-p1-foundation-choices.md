# ADR-005: P1 Foundation Technology Choices

**Status:** Accepted  
**Date:** 2026-11-16

## Context
P1 needed concrete choices for framework, ORM, logging, and UI, keeping local-first constraints in mind.

## Decision
- **FastAPI + SQLAlchemy 2 (async)** with Alembic for migrations (sync psycopg).
- **structlog** for JSON logs (no cloud telemetry).
- **Vite + React + TypeScript + shadcn/ui** for a modular, accessible frontend.
- **Single initial Alembic migration** for all 28 tables, reviewed as a unit.
- **PostgreSQL+pgvector** runs only in Docker; app and worker run natively.

## Consequences
- ✅ Fast iteration and type safety end-to-end.
- ✅ No hidden runtime dependencies; easy offline use.
- ⚠️ Async DB requires careful testing (as seen with pytest-asyncio event loop).