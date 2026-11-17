"""Enrichment Service: generate Persian meanings and examples for lexemes."""
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vocabulary import Lexeme, LexemeEnrichment
from app.services.llm_service import ChatMessage, LLMService


@dataclass
class EnrichmentResult:
    processed: int
    enriched: int
    elapsed_s: float


ENRICH_SYSTEM_PROMPT = """You are an English-to-Persian dictionary.
For the given word, output ONLY valid JSON.
Do not copy the example. Use the real meaning for the provided word.

Example input: Word: book (NOUN)
Example output: {"meaning_fa": "کتاب", "example": "I read a book yesterday.", "ipa": "/bʊk/"}

Now process the actual word provided by the user.
"""


class EnrichmentService:
    """Enriches lexemes with Persian meaning + example via local LLM."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._llm = LLMService(model="qwen2.5:3b-instruct")

    async def enrich_lexemes(self, limit: int = 20) -> EnrichmentResult:
        """Enrich up to `limit` lexemes that have no enrichment yet."""
        import json
        import time

        t0 = time.time()

        stmt = (
            select(Lexeme)
            .where(Lexeme.enrichment_status == "pending")
            .limit(limit)
        )
        lexemes = list((await self._session.execute(stmt)).scalars())
        if not lexemes:
            return EnrichmentResult(processed=0, enriched=0, elapsed_s=0.0)

        enriched_count = 0
        for lex in lexemes:
            try:
                # پرامپت بسیار کوتاه و مستقیم
                user_prompt = f"Translate this word to Persian: {lex.lemma} (part of speech: {lex.pos})"

                resp = await self._llm.chat(
                    messages=[
                        ChatMessage(role="system", content=ENRICH_SYSTEM_PROMPT),
                        ChatMessage(role="user", content=user_prompt),
                    ],
                    temperature=0.1,
                    num_predict=150,   # کافی برای JSON کوتاه
                    format="json",
                )

                raw = resp.content.strip()
                
                # اگر content خالی بود، از thinking استفاده کن
                if not raw and resp.thinking:
                    import re
                    raw = resp.thinking.strip()
                    # تلاش برای پیدا کردن آخرین JSON
                    matches = re.findall(r'\{[^{}]*\}', raw, re.DOTALL)
                    if matches:
                        raw = matches[-1]
                
                # اگر باز هم خالی بود، خطا بده
                if not raw:
                    raise ValueError("Empty response from LLM")
                
                # حذف code fences
                if raw.startswith("```"):
                    parts = raw.split("```")
                    if len(parts) >= 2:
                        raw = parts[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                
                data = json.loads(raw.strip())
                
                lex.persian_meaning = data.get("meaning_fa")
                if data.get("ipa"):
                    lex.ipa = data["ipa"]
                lex.enrichment_status = "enriched"

                enrichment = LexemeEnrichment(
                    lexeme_id=lex.id,
                    model_profile_id=None,
                    meaning_fa=data.get("meaning_fa"),
                    example=data.get("example"),
                    example_origin="generated",
                    review_status="auto_accepted",
                )
                self._session.add(enrichment)
                enriched_count += 1
                print(f"[enrich] OK: {lex.lemma} -> {data.get('meaning_fa')}")

            except Exception as e:
                lex.enrichment_status = "failed"
                print(f"[enrich] Failed for {lex.lemma}: {type(e).__name__}: {e}")
                print(f"  raw response: {resp.content[:200] if 'resp' in locals() else 'N/A'}")
                print(f"  thinking: {(resp.thinking or '')[:200] if 'resp' in locals() else 'N/A'}")

            await self._session.flush()

        elapsed = time.time() - t0
        return EnrichmentResult(
            processed=len(lexemes),
            enriched=enriched_count,
            elapsed_s=elapsed,
        )