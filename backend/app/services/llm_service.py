"""LLM Service: wraps Ollama for chat generation."""
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResponse:
    content: str
    thinking: str | None = None
    tokens_generated: int = 0
    elapsed_s: float = 0.0


class LLMService:
    """Wraps Ollama's /api/chat endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.OLLAMA_MODEL

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        num_predict: int = 1000,
    ) -> ChatResponse:
        """Call Ollama /api/chat and return the assistant message."""
        import time
        t0 = time.time()

        payload = {
            "model": self._model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat", json=payload
            )
            resp.raise_for_status()
            data = resp.json()

        elapsed = time.time() - t0
        msg = data.get("message", {})
        return ChatResponse(
            content=msg.get("content", "").strip(),
            thinking=msg.get("thinking"),
            tokens_generated=data.get("eval_count", 0),
            elapsed_s=elapsed,
        )