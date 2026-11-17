"""TutorGraph: LangGraph-based tutoring pipeline."""
from dataclasses import dataclass
from typing import Any

from app.services.llm_service import ChatMessage, LLMService
from app.services.retrieval_service import RetrievedChunk, RetrievalService

SYSTEM_PROMPT = """You are a friendly, patient English tutor for Persian-speaking learners.

You are grounded in the provided book excerpts. When the book contains the answer, cite it by page number.
When the book does not contain the answer, say so explicitly and offer a general explanation instead.

Guidelines:
- Be concise and clear.
- Use English for explanations, but offer Persian (Farsi) translations or explanations when the student seems confused or when they ask.
- When explaining grammar, show examples.
- When the student makes an error, gently correct it and explain the rule.
- Never invent facts that are not in the provided book excerpts.

Book excerpts follow.
"""


@dataclass
class TutorTurn:
    reply: str
    sources: list[dict[str, Any]]
    used_retrieval: bool
    elapsed_s: float


class TutorGraph:
    """Simple RAG-based tutor using Ollama + retrieval.

    Note: In P5 we implement a hand-rolled pipeline for clarity and testability.
    In P6 we will migrate to LangGraph for stateful multi-turn flows.
    """

    def __init__(self) -> None:
        self._llm = LLMService()

    async def respond(
        self,
        session: Any,  # AsyncSession
        book_id: str,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> TutorTurn:
        """One tutor turn: retrieve + prompt + respond."""
        import time
        t0 = time.time()

        # 1. Retrieve relevant chunks
        retrieval = RetrievalService(session)
        chunks: list[RetrievedChunk] = await retrieval.search(
            book_id=book_id, query=user_message, top_k=3
        )
        used_retrieval = len(chunks) > 0

        # 2. Build context from chunks
        if chunks:
            ctx_lines = []
            for i, c in enumerate(chunks, start=1):
                pages = ", ".join(str(r["page_number"]) for r in c.source_refs)
                ctx_lines.append(f"[Excerpt {i} from page {pages}]\n{c.content}\n")
            context_block = "\n".join(ctx_lines)
        else:
            context_block = "(No relevant excerpts were found in the book for this query.)"

        # 3. Build message list
        messages: list[ChatMessage] = [
            ChatMessage(role="system", content=SYSTEM_PROMPT + "\n\n" + context_block),
        ]
        if conversation_history:
            for m in conversation_history:
                messages.append(ChatMessage(role=m["role"], content=m["content"]))
        messages.append(ChatMessage(role="user", content=user_message))

        # 4. Call LLM
        llm_resp = await self._llm.chat(messages, temperature=0.6, num_predict=800)

        # 5. Build source refs for response
        sources = [
            {
                "chunk_id": c.chunk_id,
                "page_numbers": [r["page_number"] for r in c.source_refs],
                "score": round(c.score, 3),
                "excerpt": c.content[:200] + ("..." if len(c.content) > 200 else ""),
            }
            for c in chunks
        ]

        elapsed = time.time() - t0
        return TutorTurn(
            reply=llm_resp.content,
            sources=sources,
            used_retrieval=used_retrieval,
            elapsed_s=elapsed,
        )