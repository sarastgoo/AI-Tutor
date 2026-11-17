# ADR-013: Hand-rolled RAG (not LangGraph) in P5

**Status:** Accepted  
**Date:** 2026-11-17  
**Phase:** P5

## Context

The architecture spec (section 9) describes LangGraph-based TutorGraph. However, for P5, the actual flow is linear:
1. Load session state.
2. Retrieve relevant chunks.
3. Build prompt with context.
4. Call LLM.
5. Persist messages.

There is no branching or stateful checkpoint required yet.

## Decision

Implement P5 tutor as a hand-rolled async function in `tutor_graph.py` (despite the filename). Each step is a plain async call. LangGraph will be adopted in P6 when we implement guided lessons (which require state machine: lesson cursor, awaiting-student-answer flag, multi-turn exercises).

## Consequences

- ✅ Cleaner, easier-to-test code in P5.
- ✅ No LangGraph migration risk at this stage.
- ⚠️ In P6, `tutor_graph.py` will be rewritten as a proper LangGraph with:
  - `thread_id` = session_id
  - PostgreSQL checkpointer
  - Nodes: load_session, route_intent, retrieve_grounded_context, plan_lesson_step, compose_teaching_turn, evaluate_answer, persist_turn
- ⚠️ Existing `chat_messages` data will need to be imported into LangGraph checkpoint format (or we continue to write both).